"""Stage 3 — build the Revit-type -> SINAPI-código crosswalk (the bridge dimension).

Deterministic by construction:
  1. Unit gate    — a Revit type priced in M2/M/UN can only match SINAPI composições with
                    the same unidade (conversion_factor stays 1.0).
  2. Grupo anchor — each Revit group is restricted to its allowed SINAPI `grupo`(s), so the
                    match space is semantically bounded (e.g. forros only match "Forros"/"Gesso").
  3. Thickness anchor (alvenaria, laje_interna) — wall thickness → block width; slab thickness
                    → SINAPI laje height bucket; narrows pool before fuzzy ranking.
  4. Fuzzy rank   — within that pool, rapidfuzz token_set_ratio on normalized descriptions;
                    ties broken by lowest código. Same inputs -> same output, always.

Output: crosswalk/revit_sinapi_map.csv — the version-controlled source of truth. Low-confidence
rows are flagged for human review (and are where an optional, gated LLM pass would later choose
from the top-k candidates). Nothing here calls an LLM; the runtime costing never does.

Run:  python3 src/build_crosswalk.py
"""
import re
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

from textnorm import normalize

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT  = ROOT / "crosswalk" / "revit_sinapi_map.csv"

TOPK = 5
HIGH, MED = 72, 55  # token_set_ratio thresholds

# Each Revit group -> allowed SINAPI grupo(s). Bounds the match space deterministically.
GROUP_RULES = {
    "paredes_alvenaria": ["Alvenaria de Vedação"],
    "divisoria_leve":    ["Instalações de Divisórias Diversas", "Paredes em Drywall"],
    "forro":             ["Forros", "Gesso"],
    "cobertura":         ["Telhamento para Cobertura", "Estrutura e Trama para Cobertura"],
    "drenagem":          ["Telhamento para Cobertura"],
    "porta":             ["Esquadrias - Portas"],
    "janela":            ["Esquadrias - Janelas"],
    "vidro_fachada":     ["Pele de Vidro em Fachadas", "Vidros e Espelhos"],
    "louca_sanitaria":   ["Louças e Metais"],
    "guarda_corpo":      ["Guarda-Corpo, Corrimão e Grade para Esquadrias"],
    "fechamento_lote":   ["Cercas, Protetores e Alambrados"],
    "piso_interno":      ["Pisos", "Revestimentos Cerâmicos Internos"],
    "contrapiso":        ["Contrapiso"],
    "laje_interna":      ["Lajes Pré-Moldadas", "Radier, Piso de Concreto e Laje sobre Solo"],
    "rampa_escada":      ["Escadas", "Acessibilidade"],
}


def revestimento_grupos(text_norm: str, type_name: str = ""):
    """Wall finishes vary by material; pick the SINAPI grupo from the finish text.

    Internal vs external matters: Revit wall names carry a "- int -" / "- ext -" scope, and a
    SINAPI 'Pintura Externa' costs more than 'Pintura Interna'. Anchor on that scope so internal
    walls stop matching the external paint composição (the recurring "parede empilhada" incident).
    """
    t = text_norm
    external = (" EXT " in f" {(type_name or '').upper()} ") or "FACHADA" in (type_name or "").upper() \
        or "EXTERN" in t
    if any(k in t for k in ("PINTURA", "TINTA", "ACRILIC", "ESMALTE", "LATEX")):
        return ["Pintura Externa"] if external else ["Pintura Interna"]
    if any(k in t for k in ("CERAMIC", "PORCELAN", "AZULEJO", "REVESTIMENTO CERAMIC")):
        return ["Revestimentos Cerâmicos Externos"] if external else ["Revestimentos Cerâmicos Internos"]
    if "GESSO" in t:
        return ["Gesso", "Massa Única Interna"]
    if any(k in t for k in ("TEXTURA", "GRAFIATO", "MASSA")):
        return ["Massa Única Externa"] if external else ["Massa Única Interna"]
    # default (unknown finish), lower conf
    return ["Pintura Externa", "Massa Única Externa"] if external else ["Pintura Interna", "Massa Única Interna"]


def allowed_grupos(row):
    if row.group == "parede_revestimento":
        return revestimento_grupos(row.text_norm, row.type_name), True
    return GROUP_RULES.get(row.group, []), bool(GROUP_RULES.get(row.group))


# SINAPI doors are sold in fixed widths (×210 cm); snap the Revit door width to the nearest one.
_DOOR_WIDTHS = (60, 70, 80, 90, 100)


def door_width(type_name: str):
    """Nearest SINAPI door width (cm) for a Revit door type name like '... - 90 x 210'.

    Dimensions are stripped by normalize(), so the fuzzy step is blind to size — this anchors
    on the raw width before fuzzy, the fix for the 'buscar porta com medida mais próxima' incidents.
    """
    m = re.search(r"(\d{2,3})\s*[xX]\s*(\d{2,3})", type_name or "")
    if not m:
        return None
    return min(_DOOR_WIDTHS, key=lambda d: abs(d - int(m.group(1))))


def janela_opening(type_name: str):
    """Map a Revit window type to the SINAPI opening-type keyword (reviewer priority #1)."""
    t = (type_name or "").upper()
    if "MAXIM" in t:                              return "MAXIM"
    if "BASCULANT" in t:                          return "BASCULANT"
    if "PIVOTANT" in t or "FIXA" in t or "FIXO" in t:  return "FIXO"   # no pivotante in SINAPI
    if "CORRER" in t or "CORREDIC" in t:          return "CORRER"
    return None


def janela_folhas(type_name: str):
    """Leaf count from a Revit window type name ('... - 4 FOLHAS ...'); reviewer priority #2."""
    m = re.search(r"(\d+)\s*FOLHA", (type_name or "").upper())
    return int(m.group(1)) if m else None


def thickness_width_cm(thickness_m):
    """Map a wall thickness (m) to the nearest SINAPI alvenaria block width in cm."""
    if thickness_m is None or pd.isna(thickness_m):
        return None
    t = float(thickness_m)
    if t < 0.115:
        return "9"
    if t <= 0.165:
        return "14"
    return "19"


def laje_height_cm(thickness_m):
    """Map a slab thickness (m) to the nearest SINAPI laje total height bucket (cm)."""
    if thickness_m is None or pd.isna(thickness_m):
        return None
    t = round(float(thickness_m) * 100)
    if t <= 13:  return "12"
    if t <= 18:  return "16"
    if t <= 22:  return "20"
    if t <= 27:  return "25"
    return "30"


def main():
    rev  = pd.read_parquet(DATA / "dim_revit_type.parquet")
    comp = pd.read_parquet(DATA / "dim_sinapi_composicao.parquet").copy()
    comp["desc_norm"] = comp["descricao"].map(normalize)
    comp["unidade"]   = comp["unidade"].astype(str).str.upper().str.strip()

    # General rule (spec 6.1): never match re-installation services ("recolocação"); they
    # are repair/reuse items, never wanted in a new-construction preliminary orçamento.
    n_recoloca = comp["desc_norm"].str.contains("RECOLOCA", regex=False).sum()
    comp = comp[~comp["desc_norm"].str.contains("RECOLOCA", regex=False)].reset_index(drop=True)
    if n_recoloca:
        print(f"excluded {n_recoloca} 'recolocação' composições from the candidate pool")

    # Drop composições SINAPI never prices (no positive custo in any uf/regime): matching one
    # always yields R$0, which is never a faithful cost. Removing them keeps the fuzzy step from
    # preferring an unpriced near-synonym (e.g. PVC windows, drywall isolamento) over a priced one.
    cost = pd.read_parquet(DATA / "fact_sinapi_custo.parquet")
    ever_priced = set(cost.loc[cost["custo_rs"] > 0, "codigo"])
    n_before = len(comp)
    comp = comp[comp["codigo"].isin(ever_priced)].reset_index(drop=True)
    print(f"excluded {n_before - len(comp)} never-priced composições from the candidate pool")

    rows = []
    for r in rev.itertuples(index=False):
        grupos, has_rule = allowed_grupos(r)
        pool = comp[comp["unidade"] == r.base_unit]
        if grupos:
            pool = pool[pool["grupo"].isin(grupos)]

        anchor = None  # method label once an attribute anchor narrows the pool, else None

        # Alvenaria: anchor on wall thickness -> block width, since type names carry only finish.
        if r.group == "paredes_alvenaria":
            width = thickness_width_cm(getattr(r, "thickness_m", None))
            if width:
                sub = pool[pool["desc_norm"].str.split().apply(lambda t: width in t)]
                if len(sub):
                    pool, anchor = sub, "rule+thickness"

        # Laje interna: anchor on slab thickness -> SINAPI laje height bucket.
        if r.group == "laje_interna":
            height = laje_height_cm(getattr(r, "thickness_m", None))
            if height:
                sub = pool[pool["desc_norm"].str.contains(height, regex=False)]
                if len(sub):
                    pool, anchor = sub, "rule+thickness"

        # Porta: anchor on door width (×210), matched against the RAW SINAPI descrição because
        # normalize() drops dimension tokens. Snaps to the nearest catalogued width.
        if r.group == "porta":
            width = door_width(r.type_name)
            if width is not None:
                sub = pool[pool["descricao"].str.upper().str.contains(
                    rf"\b{width}\s*X\s*210", regex=True, na=False)]
                if len(sub):
                    pool, anchor = sub, "rule+dim"

        # Janela: anchor on opening type first, then leaf count, preferring glass-included
        # variants — the reviewer's stated ranking ("priorizar abertura, depois nº de folhas").
        if r.group == "janela":
            op = janela_opening(r.type_name)
            if op:
                sub = pool[pool["descricao"].str.upper().str.contains(op, regex=False, na=False)]
                if len(sub):
                    pool, anchor = sub, "rule+dim"
                    inc = pool[~pool["descricao"].str.upper().str.contains(
                        r"N[ÃA]O\s+INCLUSO", regex=True, na=False)]
                    if len(inc):
                        pool = inc
                    nf = janela_folhas(r.type_name)
                    if nf is not None:
                        fsub = pool[pool["descricao"].str.upper().str.contains(
                            rf"{nf}\s*FOLHA", regex=True, na=False)]
                        if len(fsub):
                            pool = fsub

        best_code = best_desc = best_grupo = None
        score = 0
        alts  = []
        if len(pool):
            scored = [
                (int(fuzz.token_set_ratio(r.text_norm, dn)), int(c), d, g)
                for c, d, g, dn in zip(pool.codigo, pool.descricao, pool.grupo, pool.desc_norm)
            ]
            # deterministic: highest score, then lowest código
            scored.sort(key=lambda x: (-x[0], x[1]))
            score, best_code, best_desc, best_grupo = scored[0]
            alts = [f"{c}:{s}" for s, c, *_ in scored[:TOPK]]

        if best_code is None:
            method, conf = "unmatched", "none"
        elif anchor:
            method, conf = anchor, ("high" if score >= MED else "medium")
        elif has_rule and score >= HIGH:
            method, conf = "rule+fuzzy", "high"
        elif has_rule and score >= MED:
            method, conf = "rule+fuzzy", "medium"
        elif not has_rule and score >= 80:
            method, conf = "fuzzy", "medium"
        else:
            method, conf = "rule+fuzzy" if has_rule else "fuzzy", "low"

        rows.append({
            "revit_type_key": r.revit_type_key, "group": r.group, "chapter": r.chapter,
            # include family_name: for plumbing the type_name is just a finish/color
            # ("BRANCO GELO"), and the fixture identity ("BACIA SANITÁRIA", "BARRA DE APOIO")
            # lives in family_name — the review pass keys on it.
            "revit_text": " | ".join(p for p in (r.family_name, r.type_name, r.material) if p),
            "element_role": r.element_role, "base_unit": r.base_unit,
            "sinapi_codigo": best_code, "sinapi_descricao": best_desc,
            "sinapi_grupo": best_grupo, "sinapi_unidade": r.base_unit,
            "qty_basis": r.base_unit, "conversion_factor": 1.0,
            "match_score": score, "confidence": conf, "match_method": method,
            "reviewed": False, "candidates": ";".join(alts),
        })

    cw = pd.DataFrame(rows)
    OUT.parent.mkdir(exist_ok=True)
    cw.to_csv(OUT, index=False)

    print(f"crosswalk written: {OUT}  ({len(cw)} types)")
    print("\nconfidence distribution:")
    print(cw.confidence.value_counts().to_string())
    print("\nby group (high/med/low/none):")
    piv = cw.pivot_table(index="group", columns="confidence", values="revit_type_key",
                         aggfunc="count", fill_value=0)
    print(piv.to_string())
    flagged = cw[cw.confidence.isin(["low", "none"])]
    print(f"\n{len(flagged)} types need review (low/none) — candidates for LLM/human pass.")


if __name__ == "__main__":
    main()

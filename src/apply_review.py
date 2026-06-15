"""Stage 3b — LLM-assisted review pass over the flagged crosswalk rows.

This encodes the reviewer's decisions (made by reading each flagged Revit type against its
shortlisted SINAPI candidates + full descriptions). It runs ONCE and is frozen into the
crosswalk; the costing stage stays a pure deterministic join. Genuine gaps (no suitable SINAPI
composição, or a unit mismatch) are marked 'gap' with código cleared and a reason — surfaced in
the coverage report rather than silently mis-priced.

Decisions are data, not magic: every override is logged to crosswalk/review_log.csv with a reason.

Run:  python3 src/apply_review.py   (after build_crosswalk.py)
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CW = ROOT / "crosswalk" / "revit_sinapi_map.csv"
LOG = ROOT / "crosswalk" / "review_log.csv"


def review(group, text, role):
    """Return (codigo|None, confidence, note) for a flagged row, or None to leave unchanged.
    codigo=None with confidence 'gap' means: no reliable SINAPI match — price manually."""
    t = (text or "").upper()
    if group == "parede_revestimento":
        if "PELE DE VIDRO" in t:   return (None, "gap", "curtain-wall glazing — price as fachada/vidros manually")
        if "GRANITO" in t:         return (None, "gap", "granite partition — not a paint finish; price manually")
        if "NAVAL" in t or "DIVISÓRIA" in t: return (None, "gap", "prefab partition panel — price manually")
        if "MEIO-FIO" in t:        return (None, "gap", "curb modeled as wall — exclude from wall finish")
        if "AZULEJO" in t and "TINTA" not in t: return (87265, "high", "azulejo wall tiling -> revest. cerâmico interno esmaltado")
        if "EPÓXI" in t or "EPOXI" in t: return (104642, "medium", "epoxy paint -> latex acrílica standard (proxy)")
        if "TINTA" in t:           return (104642, "high", "painted wall -> pintura látex acrílica 2 demãos")
        if "CARPETE" in t:         return (104641, "low", "ambiguous wall finish -> economic latex paint")
        return None
    if group == "piso_interno":
        if "PORCEL" in t or "90 X 90" in t or "90X90" in t: return (87261, "high", "porcelain floor -> revest. cerâmico piso porcelanato")
        if "CERÂMIC" in t or "CERAMIC" in t: return (87249, "high", "ceramic floor 40x40 -> piso cerâmico esmaltado 45x45")
        return None
    if group == "forro":
        if "GESSO" in t:           return (96113, "high", "gypsum-board ceiling -> forro em placas de gesso, comercial")
        if "LAJE" in t:            return (None, "gap", "exposed slab — no suspended ceiling; price teto/pintura manually")
        return None
    if group == "janela":
        if "ÓCULO" in t or "OCULO" in t: return (100674, "high", "fixed light (óculo) -> caixilho fixo de alumínio p/ vidro")
        return None
    if group == "drenagem":
        return (None, "gap", "roof gutter (calha) — no SINAPI composição in 2026-05; price sheet-metal gutter manually")
    if group in ("porta", "fechamento_lote"):
        if "PORTÃO" in t or "PORTAO" in t:
            return (None, "gap", "metal gate — SINAPI 106463 is per M2; current qty unit mismatch, price manually")
        return None
    if group == "guarda_corpo":
        if "GLASS" in t or "VIDRO" in t: return (99846, "medium", "glass/panoramic guardrail -> guarda-corpo panorâmico")
        return None
    if group == "louca_sanitaria":
        if role == "toilet":  return (86931, "high", "toilet -> bacia sanitária c/ caixa acoplada louça branca")
        if role == "urinal":  return (100858, "high", "urinal -> mictório sifonado c/ válvula descarga")
        if role == "sink":
            if "INOX" in t:                 return (86900, "high", "stainless sink -> cuba inox de embutir")
            if "L83C" in t or "410" in t:   return (86900, "medium", "square louça cuba -> cuba de embutir (proxy)")
            if "BRANCO GELO" in t:          return (86902, "high", "washbasin -> lavatório louça branca c/ coluna")
            return (86900, "low", "generic sink -> cuba inox (proxy)")
        return None
    return None


def main():
    cw = pd.read_csv(CW)
    comp = pd.read_parquet(ROOT / "data" / "dim_sinapi_composicao.parquet").set_index("codigo")

    target = cw.confidence.isin(["low", "none"]) | (cw.group == "louca_sanitaria")
    logs, changed = [], 0
    for i, r in cw[target].iterrows():
        dec = review(r.group, r.revit_text, str(r.element_role))
        if dec is None:
            continue
        codigo, conf, note = dec
        before = r.sinapi_codigo
        if codigo is None:
            cw.at[i, "sinapi_codigo"] = pd.NA
            cw.at[i, "sinapi_descricao"] = pd.NA
        else:
            cw.at[i, "sinapi_codigo"] = codigo
            if codigo in comp.index:
                cw.at[i, "sinapi_descricao"] = comp.loc[codigo, "descricao"]
                cw.at[i, "sinapi_grupo"] = comp.loc[codigo, "grupo"]
        cw.at[i, "confidence"] = conf
        cw.at[i, "match_method"] = "llm_review"
        cw.at[i, "reviewed"] = True
        changed += 1
        logs.append({"group": r.group, "revit_text": r.revit_text, "role": r.element_role,
                     "from_codigo": before, "to_codigo": codigo, "confidence": conf, "note": note})

    cw.to_csv(CW, index=False)
    pd.DataFrame(logs).to_csv(LOG, index=False)
    print(f"reviewed {changed} rows -> {CW.name}; log -> {LOG.name}")
    print("\nnew confidence distribution:")
    print(cw.confidence.value_counts().to_string())
    gaps = cw[cw.confidence == "gap"]
    print(f"\n{len(gaps)} explicit gaps (priced manually):")
    for r in gaps.itertuples():
        print(f"  [{r.group}] {str(r.revit_text)[:50]}")


if __name__ == "__main__":
    main()

"""Stage 2 — flatten the Revit model summary JSON into the star schema's Revit side.

Emits:
  data/dim_revit_type.parquet      (revit_type_key PK, group, chapter, type_name, material, base_unit, text_norm)
  data/fact_revit_quantity.parquet (revit_type_key FK, quantity, unit, n_elements, quantity_status, data_origin)

Scope is declared in GROUP_SPECS: each entry maps a building chapter to one of the JSON
`*_types` aggregate arrays, the quantity field that feeds costing, and the SINAPI unit it
must be priced in.

Floor surfaces are decomposed layer-by-layer (floor_layer_types) to separate contrapiso and
structural laje from the finish layer. Wall finish surfaces are split into divisoria_leve and
vidro_fachada before the generic parede_revestimento group.
"""
import json
import statistics
from collections import defaultdict
from pathlib import Path

import pandas as pd

from textnorm import normalize

ROOT = Path(__file__).resolve().parent.parent
SRC_JSON = ROOT / "revit_model_summary.json"
OUT = ROOT / "data"

_DIVISORIA = ("divisória", "divisoria")
_VIDRO     = ("vidro", "espelho")
_CORTINA   = ("cortina",)          # curtain walls (pele de vidro) — glazed, not masonry
_MEIO_FIO  = ("meio-fio",)

# (group, chapter, json_path_to_types_array, quantity_field, sinapi_unit, optional row-filter)
GROUP_SPECS = [
    # ── Vedações ──────────────────────────────────────────────────────────────────────
    ("paredes_alvenaria",   "Vedações",        "wall_types",                    "total_area_m2",  "M2",
        # exclude curtain-wall glazing (pele de vidro) — it is priced by vidro_fachada,
        # not as masonry. Without this, the "Parede cortina - PELE DE VIDRO" wall_type
        # leaks into alvenaria and is mis-priced as block masonry.
        lambda t: not any(k in (t.get("type_name") or "").lower()
                          for k in _VIDRO + _CORTINA)),
    ("divisoria_leve",      "Vedações",        "wall_finish_types",             "total_area_m2",  "M2",
        lambda t: any(k in (t.get("type_name") or "").lower() for k in _DIVISORIA)),
    # ── Acabamentos ───────────────────────────────────────────────────────────────────
    ("parede_revestimento", "Acabamentos",     "wall_finish_types",             "total_area_m2",  "M2",
        lambda t: not any(k in (t.get("type_name") or "").lower()
                          for k in _DIVISORIA + _VIDRO + _MEIO_FIO)),
    ("piso_interno",        "Acabamentos",     "floor_surface_types",           "total_area_m2",  "M2",
        lambda t: t.get("floor_scope") == "internal_floor_finish"),
    ("contrapiso",          "Acabamentos",     "floor_layer_types",             "total_area_m2",  "M2",
        lambda t: "contrapiso" in (t.get("material") or "").lower()),
    ("laje_interna",        "Estrutura",       "floor_layer_types",             "total_area_m2",  "M2",
        lambda t: (t.get("funcao") or "").lower() == "estrutura"),
    ("forro",               "Acabamentos",     "ceiling_surface_types",         "total_area_m2",  "M2", None),
    # ── Cobertura ─────────────────────────────────────────────────────────────────────
    ("cobertura",           "Cobertura",       "roof_types",                    "total_area_m2",  "M2", None),
    ("drenagem",            "Cobertura",       "roof_drainage_element_types",   "total_length_m", "M",  None),
    # ── Esquadrias ────────────────────────────────────────────────────────────────────
    ("porta",               "Esquadrias",      "door_types",                    "count",          "UN", None),
    ("janela",              "Esquadrias",      "window_types",                  "total_area_m2",  "M2", None),
    ("vidro_fachada",       "Esquadrias",      "wall_finish_types",             "total_area_m2",  "M2",
        lambda t: any(k in (t.get("type_name") or "").lower() for k in _VIDRO)),
    # ── Hidrossanitário ───────────────────────────────────────────────────────────────
    ("louca_sanitaria",     "Hidrossanitário", "plumbing_fixture_types",        "count",          "UN", None),
    # ── Circulação ────────────────────────────────────────────────────────────────────
    ("rampa_escada",        "Circulação",      "stairs_and_ramp_types",         "count",          "UN", None),
    ("guarda_corpo",        "Circulação",      "railing_types",                 "total_length_m", "M",  None),
    ("fechamento_lote",     "Circulação",      "site_enclosures.types",         "total_length_m", "M",  None),
]


# Each GROUP_SPECS *_types array maps back to the element-level array that carries the
# Revit element_id, so each priced type can list the concrete element IDs behind it (for
# fact-checking the report against revit_model_summary.json).
_TYPES_TO_ELEMENTS = {
    "wall_types":                  "walls",
    "wall_finish_types":           "wall_finish_surfaces",
    "floor_surface_types":         "floor_surfaces",
    "floor_layer_types":           "floor_surfaces",   # layers share the parent floor element ids
    "ceiling_surface_types":       "ceiling_surfaces",
    "roof_types":                  "roof_elements",
    "roof_drainage_element_types": "roof_drainage_elements",
    "door_types":                  "doors",
    "window_types":                "windows",
    "plumbing_fixture_types":      "plumbing_fixtures",
    "stairs_and_ramp_types":       "stairs_and_ramps",
    "railing_types":               "railing_elements",
    "site_enclosures.types":       "site_enclosures.items",
}


def _resolve(doc, path):
    node = doc
    for part in path.split("."):
        node = node.get(part, {}) if isinstance(node, dict) else {}
    return node if isinstance(node, list) else []


def _element_ids_index(doc):
    """For each element source, index element_id by (type_name, element_role) and by type_name.
    The role-aware key disambiguates fixtures sharing a type_name; the type_name-only key is the
    fallback when a *_type carries no role but its elements do (e.g. drenagem calhas)."""
    idx = {}
    for elem_path in set(_TYPES_TO_ELEMENTS.values()):
        by_tr, by_t = defaultdict(set), defaultdict(set)
        for e in _resolve(doc, elem_path):
            if not isinstance(e, dict):
                continue
            eid = e.get("element_id")
            if eid is None:
                continue
            tn   = (e.get("type_name")    or "").strip()
            role = (e.get("element_role") or "").strip()
            by_tr[(tn, role)].add(eid)
            by_t[tn].add(eid)
        idx[elem_path] = (by_tr, by_t)
    return idx


def _ids_for(idx, types_path, type_name, role):
    """Element ids for a type: prefer the (type_name, role) match, fall back to type_name."""
    elem_path = _TYPES_TO_ELEMENTS.get(types_path)
    if elem_path not in idx:
        return []
    by_tr, by_t = idx[elem_path]
    ids = by_tr.get((type_name, role)) or by_t.get(type_name, set())
    return sorted(ids, key=str)  # sort by str for deterministic output regardless of id type


def _thickness_by_type(doc):
    """Median wall thickness per type_name, from element-level `walls` (wall_types omits it).
    Lets the crosswalk pick the alvenaria block width, since wall type names carry only finish."""
    buckets = {}
    for w in doc.get("walls", []):
        tn = (w.get("type_name") or "").strip()
        th = w.get("thickness_m")
        if tn and isinstance(th, (int, float)):
            buckets.setdefault(tn, []).append(float(th))
    return {tn: round(statistics.median(v), 3) for tn, v in buckets.items()}


def _finish_thickness_by_type(doc):
    """Median total wall thickness per finish type, from wall_finish_surfaces compound layers."""
    buckets = {}
    for w in doc.get("wall_finish_surfaces", []):
        tn = (w.get("type_name") or "").strip()
        construction = (w.get("bim_details") or {}).get("construction", {})
        th = construction.get("total_thickness_m")
        if tn and isinstance(th, (int, float)):
            buckets.setdefault(tn, []).append(float(th))
    return {tn: round(statistics.median(v), 3) for tn, v in buckets.items()}


def _floor_layer_types(doc):
    """Aggregate floor element compound layers into type-level rows (type_name × material × funcao).

    Each floor element has stacked layers (finish, contrapiso, structural slab). This explodes
    them so each layer becomes a separately priceable type with its own area and thickness.
    """
    buckets = defaultdict(lambda: {
        "count": 0, "total_area_m2": 0.0,
        "thickness_m": None, "funcao": None, "floor_scope": None,
    })
    for elem in doc.get("floor_surfaces", []):
        type_name = (elem.get("type_name") or "").strip()
        area = float(elem.get("area_m2") or 0.0)
        floor_scope = elem.get("floor_scope", "")
        layers = (elem.get("bim_details") or {}).get("construction", {}).get("compound_layers", [])
        for layer in layers:
            material = (layer.get("material") or "").strip()
            funcao = (layer.get("function") or "").strip()
            thickness = layer.get("thickness_m")
            if not material:
                continue
            key = (type_name, material, funcao)
            b = buckets[key]
            b["count"] += 1
            b["total_area_m2"] += area
            b["thickness_m"] = thickness
            b["funcao"] = funcao
            b["floor_scope"] = floor_scope
    result = []
    for (type_name, material, funcao), vals in buckets.items():
        result.append({
            "type_name": type_name,
            "material": material,
            "funcao": funcao,
            "count": vals["count"],
            "total_area_m2": round(vals["total_area_m2"], 4),
            "thickness_m": vals["thickness_m"],
            "floor_scope": vals["floor_scope"],
            "quantity_status": "valid",
            "data_origin": "layer_decomposition",
        })
    return result


def main():
    doc = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    print(f"Project: {doc['project']['name']}")
    thickness_by_type        = _thickness_by_type(doc)
    finish_thickness_by_type = _finish_thickness_by_type(doc)
    id_index                 = _element_ids_index(doc)

    # Inject derived layer aggregate so GROUP_SPECS can reference it via _resolve
    doc["floor_layer_types"] = _floor_layer_types(doc)

    dim_rows, fact_rows = [], []
    for group, chapter, path, qty_field, unit, filt in GROUP_SPECS:
        entries = _resolve(doc, path)
        kept = 0
        for t in entries:
            if filt and not filt(t):
                continue
            family    = (t.get("family_name")   or "").strip()
            type_name = (t.get("type_name")      or "").strip()
            material  = (t.get("material")       or "").strip()
            role      = (t.get("element_role")   or "").strip()
            if not (family or type_name or material):
                continue
            # family_name distinguishes fixtures whose type_name is just a finish/color
            # (e.g. plumbing "BRANCO GELO"); include it in both the key and match text.
            key = f"{group}|{family}|{type_name}|{material}"
            qty = t.get(qty_field)
            qty = float(qty) if isinstance(qty, (int, float)) else 0.0
            # dedup the descriptor parts, preserving order, for the fuzzy-match text
            seen, parts = set(), []
            for p in (family, type_name, material):
                if p and p.upper() not in seen:
                    seen.add(p.upper()); parts.append(p)
            text = " ".join(parts)

            if group == "paredes_alvenaria":
                thickness_m = thickness_by_type.get(type_name)
            elif group == "divisoria_leve":
                thickness_m = finish_thickness_by_type.get(type_name)
            elif group == "laje_interna":
                thickness_m = t.get("thickness_m")
            else:
                thickness_m = None

            elem_ids = _ids_for(id_index, path, type_name, role)
            dim_rows.append({
                "revit_type_key": key, "group": group, "chapter": chapter,
                "family_name": family, "type_name": type_name, "material": material,
                "element_role": role, "base_unit": unit, "text_norm": normalize(text),
                "thickness_m": thickness_m,
                "revit_element_ids": ",".join(str(i) for i in elem_ids),
                "revit_n_elements": len(elem_ids),
            })
            fact_rows.append({
                "revit_type_key": key, "quantity": qty, "unit": unit,
                "n_elements": int(t.get("count") or 0),
                "quantity_status": t.get("quantity_status"),
                "data_origin": t.get("data_origin"),
            })
            kept += 1
        print(f"  {group:<20} <- {path:<32} {kept:>3} types")

    dim  = pd.DataFrame(dim_rows).drop_duplicates("revit_type_key").reset_index(drop=True)
    fact = pd.DataFrame(fact_rows).drop_duplicates("revit_type_key").reset_index(drop=True)

    OUT.mkdir(exist_ok=True)
    dim.to_parquet(OUT / "dim_revit_type.parquet", index=False)
    fact.to_parquet(OUT / "fact_revit_quantity.parquet", index=False)

    print("--- Revit tidy summary ---")
    print(f"dim_revit_type:      {len(dim):>4} distinct types")
    print(f"fact_revit_quantity: {len(fact):>4} rows")
    print("\nquantity by chapter/unit:")
    j = dim.merge(fact, on="revit_type_key")
    print(j.groupby(["chapter", "unit"])["quantity"].agg(["count", "sum"]).round(1).to_string())
    zero = fact[fact.quantity == 0]
    if len(zero):
        print(f"\n{len(zero)} types have zero quantity (will flag in coverage report).")


if __name__ == "__main__":
    main()

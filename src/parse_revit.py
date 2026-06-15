"""Stage 2 — flatten the Revit model summary JSON into the star schema's Revit side.

Emits:
  data/dim_revit_type.parquet      (revit_type_key PK, group, chapter, type_name, material, base_unit, text_norm)
  data/fact_revit_quantity.parquet (revit_type_key FK, quantity, unit, n_elements, quantity_status, data_origin)

Scope is declared in GROUP_SPECS: each entry maps a building chapter to one of the JSON
`*_types` aggregate arrays, the quantity field that feeds costing, and the SINAPI unit it
must be priced in. Structural groups are empty in this model and omitted. External paving /
landscape / topography are intentionally excluded (preliminary, flagged in the plan).
"""
import json
from pathlib import Path

import pandas as pd

from textnorm import normalize

ROOT = Path(__file__).resolve().parent.parent
SRC_JSON = ROOT / "revit_model_summary.json"
OUT = ROOT / "data"

# (group, chapter, json_path_to_types_array, quantity_field, sinapi_unit, optional row-filter)
GROUP_SPECS = [
    ("paredes_alvenaria",   "Vedações",        "wall_types",                    "total_area_m2",  "M2", None),
    ("parede_revestimento", "Acabamentos",     "wall_finish_types",             "total_area_m2",  "M2", None),
    ("piso_interno",        "Acabamentos",     "floor_surface_types",           "total_area_m2",  "M2",
        lambda t: t.get("floor_scope") == "internal_floor_finish"),
    ("forro",               "Acabamentos",     "ceiling_surface_types",         "total_area_m2",  "M2", None),
    ("cobertura",           "Cobertura",       "roof_types",                    "total_area_m2",  "M2", None),
    ("drenagem",            "Cobertura",       "roof_drainage_element_types",   "total_length_m", "M",  None),
    ("porta",               "Esquadrias",      "door_types",                    "count",          "UN", None),
    ("janela",              "Esquadrias",      "window_types",                  "total_area_m2",  "M2", None),
    ("louca_sanitaria",     "Hidrossanitário", "plumbing_fixture_types",        "count",          "UN", None),
    ("rampa_escada",        "Circulação",      "stairs_and_ramp_types",         "count",          "UN", None),
    ("guarda_corpo",        "Circulação",      "railing_types",                 "total_length_m", "M",  None),
    ("fechamento_lote",     "Circulação",      "site_enclosures.types",         "total_length_m", "M",  None),
]


def _resolve(doc, path):
    node = doc
    for part in path.split("."):
        node = node.get(part, {}) if isinstance(node, dict) else {}
    return node if isinstance(node, list) else []


def _thickness_by_type(doc):
    """Median wall thickness per type_name, from element-level `walls` (wall_types omits it).
    Lets the crosswalk pick the alvenaria block width, since wall type names carry only finish."""
    import statistics
    buckets = {}
    for w in doc.get("walls", []):
        tn = (w.get("type_name") or "").strip()
        th = w.get("thickness_m")
        if tn and isinstance(th, (int, float)):
            buckets.setdefault(tn, []).append(float(th))
    return {tn: round(statistics.median(v), 3) for tn, v in buckets.items()}


def main():
    doc = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    print(f"Project: {doc['project']['name']}")
    thickness_by_type = _thickness_by_type(doc)

    dim_rows, fact_rows = [], []
    for group, chapter, path, qty_field, unit, filt in GROUP_SPECS:
        entries = _resolve(doc, path)
        kept = 0
        for t in entries:
            if filt and not filt(t):
                continue
            family = (t.get("family_name") or "").strip()
            type_name = (t.get("type_name") or "").strip()
            material = (t.get("material") or "").strip()
            role = (t.get("element_role") or "").strip()
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
            dim_rows.append({
                "revit_type_key": key, "group": group, "chapter": chapter,
                "family_name": family, "type_name": type_name, "material": material,
                "element_role": role, "base_unit": unit, "text_norm": normalize(text),
                "thickness_m": thickness_by_type.get(type_name) if group == "paredes_alvenaria" else None,
            })
            fact_rows.append({
                "revit_type_key": key, "quantity": qty, "unit": unit,
                "n_elements": int(t.get("count") or 0),
                "quantity_status": t.get("quantity_status"),
                "data_origin": t.get("data_origin"),
            })
            kept += 1
        print(f"  {group:<20} <- {path:<32} {kept:>3} types")

    dim = pd.DataFrame(dim_rows).drop_duplicates("revit_type_key").reset_index(drop=True)
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

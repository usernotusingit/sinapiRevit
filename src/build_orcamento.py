"""Stage 4 — deterministic costing join: Revit quantities x SINAPI unit costs -> orçamento.

Materializes the star schema in DuckDB and runs a pure relational join — no LLM, no
randomness. Same crosswalk + same SINAPI month + same (uf, regime) => identical output.

  fact_orcamento = fact_revit_quantity
                 ⋈ crosswalk (revit_type_key -> sinapi_codigo, conversion_factor)
                 ⋈ fact_sinapi_custo  (codigo, uf=:uf, regime=:regime)

Outputs:
  output/orcamento_<UF>_<REGIME>.xlsx  (line items + by-chapter + summary)
  output/fact_orcamento_<UF>_<REGIME>.parquet  (for the determinism hash test)

Run:  python3 src/build_orcamento.py --uf MG --regime SD
"""
import argparse
import hashlib
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTDIR = ROOT / "output"

JOIN_SQL = """
WITH q AS (SELECT * FROM read_parquet($qty)),
     cw AS (SELECT * FROM read_csv_auto($cw, header=true)),
     custo AS (SELECT codigo, custo_rs, pct_as FROM read_parquet($custo)
               WHERE uf = $uf AND regime = $regime),
     comp AS (SELECT codigo, descricao, grupo FROM read_parquet($comp)),
     rev AS (SELECT revit_type_key, "group" AS grp, chapter, type_name, material FROM read_parquet($rev))
SELECT
    cw.chapter,
    cw."group" AS group,
    rev.type_name,
    rev.material,
    q.quantity,
    q.unit,
    q.quantity_status,
    cw.sinapi_codigo            AS codigo,
    comp.descricao              AS sinapi_descricao,
    comp.grupo                  AS sinapi_grupo,
    cw.conversion_factor,
    custo.custo_rs              AS custo_unit,
    ROUND(q.quantity * cw.conversion_factor * custo.custo_rs, 2) AS custo_total,
    cw.match_score,
    cw.confidence,
    cw.match_method,
    cw.reviewed
FROM q
JOIN cw   ON q.revit_type_key = cw.revit_type_key
JOIN rev  ON q.revit_type_key = rev.revit_type_key
LEFT JOIN custo ON cw.sinapi_codigo = custo.codigo
LEFT JOIN comp  ON cw.sinapi_codigo = comp.codigo
ORDER BY cw.chapter, cw."group", custo_total DESC NULLS LAST
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf", default="MG")
    ap.add_argument("--regime", default="SD", choices=["SD", "CD", "SE"])
    args = ap.parse_args()

    con = duckdb.connect()
    df = con.execute(JOIN_SQL, {
        "qty": str(DATA / "fact_revit_quantity.parquet"),
        "cw": str(ROOT / "crosswalk" / "revit_sinapi_map.csv"),
        "custo": str(DATA / "fact_sinapi_custo.parquet"),
        "comp": str(DATA / "dim_sinapi_composicao.parquet"),
        "rev": str(DATA / "dim_revit_type.parquet"),
        "uf": args.uf, "regime": args.regime,
    }).df()

    OUTDIR.mkdir(exist_ok=True)
    tag = f"{args.uf}_{args.regime}"
    df.to_parquet(OUTDIR / f"fact_orcamento_{tag}.parquet", index=False)

    by_chapter = (df.groupby("chapter")["custo_total"].sum().round(2)
                  .reset_index().sort_values("custo_total", ascending=False))
    grand_total = df["custo_total"].sum()

    # confidence-weighted view: how much R$ rests on soft matches
    by_conf = df.groupby("confidence")["custo_total"].sum().round(2).reset_index()

    with pd.ExcelWriter(OUTDIR / f"orcamento_{tag}.xlsx", engine="openpyxl") as xl:
        df.to_excel(xl, sheet_name="line_items", index=False)
        by_chapter.to_excel(xl, sheet_name="by_chapter", index=False)
        by_conf.to_excel(xl, sheet_name="by_confidence", index=False)

    h = hashlib.sha256(
        df.fillna("").astype(str).to_csv(index=False).encode()
    ).hexdigest()[:16]

    print(f"=== ORÇAMENTO {args.uf} / {args.regime} ===")
    print(f"line items: {len(df)}   missing price: {df.custo_unit.isna().sum()}")
    print("\nby chapter (R$):")
    print(by_chapter.to_string(index=False))
    print(f"\nGRAND TOTAL: R$ {grand_total:,.2f}")
    print("\nR$ by match confidence:")
    print(by_conf.to_string(index=False))
    print(f"\nfact_orcamento hash: {h}  (stable across runs => deterministic)")


if __name__ == "__main__":
    main()

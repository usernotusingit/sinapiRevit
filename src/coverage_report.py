"""Stage 5 — coverage / confidence report for the orçamento.

Summarizes how much of the model (by quantity and by R$) rests on confident matches vs.
matches that need human review, and lists the types to review. Reads the frozen crosswalk
and a computed orçamento parquet.

Run:  python3 src/coverage_report.py --uf MG --regime SD
"""
import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "output"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf", default="MG")
    ap.add_argument("--regime", default="SD")
    args = ap.parse_args()
    tag = f"{args.uf}_{args.regime}"

    o = pd.read_parquet(OUTDIR / f"fact_orcamento_{tag}.parquet")
    cw = pd.read_csv(ROOT / "crosswalk" / "revit_sinapi_map.csv")

    total = o.custo_total.sum()
    conf_rs = o.groupby("confidence").custo_total.sum().reindex(["high", "medium", "low"]).fillna(0)
    soft = conf_rs.get("low", 0) + conf_rs.get("medium", 0)

    lines = []
    w = lines.append
    w(f"# Orçamento coverage report — {args.uf} / {args.regime}\n")
    w(f"Project: **CÂMARA MUNICIPAL** · SINAPI 2026-05 · {len(o)} line items\n")
    w(f"**Grand total: R$ {total:,.2f}**\n")

    w("## R$ by match confidence\n")
    w("| confidence | R$ | % of total |")
    w("|---|---:|---:|")
    for c in ["high", "medium", "low"]:
        v = conf_rs.get(c, 0)
        w(f"| {c} | {v:,.2f} | {100*v/total:4.1f}% |")
    low_pct = 100 * conf_rs.get("low", 0) / total
    w(f"\n> **high** = reviewed/strong match · **medium** = grupo/thickness-anchored (semantically bounded, "
      f"unit-checked) · **low** = verify. Only {low_pct:.1f}% of the total rests on low-confidence "
      f"matches; {len(cw[cw.confidence=='gap'])} items are explicit gaps (excluded, priced manually).\n")

    w("## By chapter\n")
    ch = o.groupby("chapter").agg(itens=("codigo", "size"), total=("custo_total", "sum")).round(2)
    ch = ch.sort_values("total", ascending=False)
    w("| chapter | items | R$ |")
    w("|---|---:|---:|")
    for c, r in ch.iterrows():
        w(f"| {c} | {int(r.itens)} | {r.total:,.2f} |")

    w("\n## Coverage by group (confidence counts)\n")
    piv = cw.pivot_table(index="group", columns="confidence", values="revit_type_key",
                         aggfunc="count", fill_value=0)
    for c in ["high", "medium", "low", "none"]:
        if c not in piv.columns:
            piv[c] = 0
    w("| group | high | medium | low | none |")
    w("|---|---:|---:|---:|---:|")
    for g, r in piv.iterrows():
        w(f"| {g} | {int(r['high'])} | {int(r['medium'])} | {int(r['low'])} | {int(r['none'])} |")

    gap_rows = cw[cw.confidence == "gap"]
    w(f"\n## Explicit gaps — price manually ({len(gap_rows)})\n")
    w("No reliable SINAPI composição (missing item or unit mismatch). Excluded from the total above.\n")
    w("| group | revit type | reason |")
    w("|---|---|---|")
    rl_path = ROOT / "crosswalk" / "review_log.csv"
    notes = {}
    if rl_path.exists():
        rl = pd.read_csv(rl_path)
        notes = {str(t): n for t, n in zip(rl.revit_text, rl.note)}
    for r in gap_rows.itertuples(index=False):
        w(f"| {r.group} | {str(r.revit_text)[:46]} | {notes.get(str(r.revit_text), '')[:60]} |")

    flagged = cw[cw.confidence == "low"].copy()
    w(f"\n## Low-confidence matches ({len(flagged)})\n")
    w("Priced, but verify:\n")
    w("| group | revit | -> SINAPI código | desc |")
    w("|---|---|---|---|")
    for r in flagged.sort_values("match_score").itertuples(index=False):
        rv = str(r.revit_text)[:38]
        sd = str(r.sinapi_descricao)[:42]
        w(f"| {r.group} | {rv} | {r.sinapi_codigo} | {sd} |")

    w("\n## Known limitations\n")
    w("- **Alvenaria (Vedações):** Revit wall types describe the *finish* (e.g. \"Parede básica - "
      "int - ... / TINTA\"), not the block. There is no masonry spec in the model, so block-type "
      "matching is unreliable (all low). Options: use wall `thickness_m` to pick block width, assign "
      "a documented default composição, or cost wall finishes only.")
    w("- **Fuzzy scores under-rate correct matches** when the Revit name carries extra tokens "
      "(cobertura→telha metálica termoacústica is correct yet scores 60). Confidence tiers are "
      "conservative; review promotes them.")
    w("- Wall finish areas use the model's single computed face area; verify if both faces are needed.")

    out = OUTDIR / f"coverage_report_{tag}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    print(f"total R$ {total:,.2f} | soft (med+low) {100*soft/total:.0f}%")


if __name__ == "__main__":
    main()

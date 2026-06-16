"""Render the project skeleton schema to PNG (same layout as the .excalidraw)."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# palette
IN_S, IN_B = "#e8590c", "#ffec99"
SC_S, SC_B = "#1971c2", "#a5d8ff"
RV_S, RV_B = "#1971c2", "#d0ebff"
SN_S, SN_B = "#2f9e44", "#b2f2bb"
BR_S, BR_B = "#e03131", "#ffc9c9"
OUT_S, OUT_B = "#6741d9", "#d0bfff"
OR_S, OR_B = "#f08c00", "#ffe8cc"

W = 210
N = {}
# id: (x, y, w, h, label, stroke, bg, fontsize)
NODES = [
    ("revit_in", 40, 140, W, 64, "revit_model_summary.json", IN_S, IN_B, 10),
    ("sinapi_in", 40, 470, W, 64, "SINAPI_Referência\n_2026_05.xlsx", IN_S, IN_B, 10),
    ("parse_revit", 300, 140, W, 64, "parse_revit.py", SC_S, SC_B, 12),
    ("parse_sinapi", 300, 470, W, 64, "parse_sinapi.py", SC_S, SC_B, 12),
    ("dim_revit", 560, 110, W, 56, "dim_revit_type", RV_S, RV_B, 11),
    ("fact_qty", 560, 196, W, 56, "fact_revit_quantity", RV_S, RV_B, 11),
    ("dim_comp", 560, 386, W, 56, "dim_sinapi_composicao", SN_S, SN_B, 10),
    ("fact_custo", 560, 472, W, 56, "fact_sinapi_custo", SN_S, SN_B, 11),
    ("dim_loc", 560, 558, W, 56, "dim_localidade", SN_S, SN_B, 11),
    ("crosswalk", 900, 150, 230, 76, "revit_sinapi_map.csv\n(crosswalk / ponte)", BR_S, BR_B, 12),
    ("review", 900, 300, 230, 70, "apply_review.py →\nreview_log.csv\n(LLM, congelado)", OR_S, OR_B, 10),
    ("orcamento", 1180, 250, 230, 64, "build_orcamento.py", SC_S, SC_B, 12),
    ("fact_orc", 1180, 350, 230, 56, "fact_orcamento", OUT_S, OUT_B, 11),
    ("xlsx", 1180, 440, 230, 56, "orcamento_MG_{SD,CD}.xlsx", OUT_S, OUT_B, 10),
    ("coverage", 1180, 530, 230, 56, "coverage_report_MG.md", OUT_S, OUT_B, 10),
]
ARROWS = [
    ("revit_in", "parse_revit", "#343a40"), ("sinapi_in", "parse_sinapi", "#343a40"),
    ("parse_revit", "dim_revit", "#343a40"), ("parse_revit", "fact_qty", "#343a40"),
    ("parse_sinapi", "dim_comp", "#343a40"), ("parse_sinapi", "fact_custo", "#343a40"),
    ("parse_sinapi", "dim_loc", "#343a40"),
    ("dim_revit", "crosswalk", "#343a40"), ("dim_comp", "crosswalk", "#343a40"),
    ("review", "crosswalk", "#f08c00"),
    ("crosswalk", "orcamento", "#343a40"), ("fact_qty", "orcamento", "#1971c2"),
    ("fact_custo", "orcamento", "#2f9e44"),
    ("orcamento", "fact_orc", "#343a40"), ("fact_orc", "xlsx", "#343a40"),
    ("fact_orc", "coverage", "#343a40"),
]

fig, ax = plt.subplots(figsize=(15.5, 7.2), dpi=160)
ax.set_xlim(0, 1450); ax.set_ylim(640, 0)  # invert y to match excalidraw coords
ax.axis("off")

for nid, x, y, w, h, lbl, stroke, bg, fs in NODES:
    N[nid] = (x, y, w, h)
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=2,rounding_size=10",
                 linewidth=2, edgecolor=stroke, facecolor=bg, zorder=2))
    ax.text(x + w/2, y + h/2, lbl, ha="center", va="center", fontsize=fs,
            color="#1e1e1e", zorder=3, wrap=True)

def edge(src, dst):
    sx, sy, sw, sh = N[src]; dx, dy, dw, dh = N[dst]
    scx, scy, dcx, dcy = sx+sw/2, sy+sh/2, dx+dw/2, dy+dh/2
    if abs(dcx-scx) >= abs(dcy-scy):
        p1 = (sx+sw, scy) if dcx > scx else (sx, scy)
        p2 = (dx, dcy) if dcx > scx else (dx+dw, dcy)
    else:
        p1 = (scx, sy+sh) if dcy > scy else (scx, sy)
        p2 = (dcx, dy) if dcy > scy else (dcx, dy+dh)
    return p1, p2

for src, dst, col in ARROWS:
    p1, p2 = edge(src, dst)
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=14,
                 linewidth=1.8, color=col, zorder=1,
                 connectionstyle="arc3,rad=0.04"))

ax.text(40, 40, "SINAPI × Revit — esqueleto do pipeline de orçamento",
        fontsize=20, fontweight="bold", color="#1e1e1e")
ax.text(40, 70, "Fluxo de dados: inputs → parse → modelo estrela → ponte (crosswalk) → orçamento",
        fontsize=12, color="#868e96")
for x, t in [(40, "INPUTS"), (300, "PARSE"), (560, "MODELO ESTRELA"),
             (900, "PONTE"), (1180, "ORÇAMENTO & RELATÓRIOS")]:
    ax.text(x, 122, t, fontsize=11, color="#adb5bd", fontweight="bold")
ax.text(900, 245, "★ chave manufaturada — não há chave natural", fontsize=10.5, color="#e03131")
ax.text(1180, 210, "JOIN determinístico (UF, regime) · 0 LLM no runtime",
        fontsize=10, color="#6741d9")

out = Path(__file__).resolve().parent.parent / "docs" / "esqueleto_projeto.png"
out.parent.mkdir(exist_ok=True)
fig.savefig(out, bbox_inches="tight", facecolor="white", pad_inches=0.2)
print("wrote", out)

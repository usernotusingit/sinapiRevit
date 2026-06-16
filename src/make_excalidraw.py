"""Generate an .excalidraw schema of the project skeleton (data flow / star schema)."""
import json, random
from pathlib import Path

random.seed(7)
def nonce(): return random.randint(1, 2**31)

elements = []
NODES = {}

def rect(id, x, y, w, h, label, stroke, bg, fontsize=16, dashed=False):
    rid = id
    tid = id + "_t"
    rectangle = {
        "id": rid, "type": "rectangle", "x": x, "y": y, "width": w, "height": h,
        "angle": 0, "strokeColor": stroke, "backgroundColor": bg, "fillStyle": "solid",
        "strokeWidth": 2, "strokeStyle": "dashed" if dashed else "solid", "roughness": 1,
        "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": {"type": 3}, "seed": nonce(), "version": 1, "versionNonce": nonce(),
        "isDeleted": False, "boundElements": [{"type": "text", "id": tid}],
        "updated": 1, "link": None, "locked": False,
    }
    text = {
        "id": tid, "type": "text", "x": x + 6, "y": y + h/2 - fontsize, "width": w - 12,
        "height": fontsize*2.2, "angle": 0, "strokeColor": stroke, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid", "roughness": 1,
        "opacity": 100, "groupIds": [], "frameId": None, "roundness": None, "seed": nonce(),
        "version": 1, "versionNonce": nonce(), "isDeleted": False, "boundElements": [],
        "updated": 1, "link": None, "locked": False, "fontSize": fontsize, "fontFamily": 1,
        "text": label, "textAlign": "center", "verticalAlign": "middle",
        "containerId": rid, "originalText": label, "lineHeight": 1.25, "baseline": fontsize*0.8,
    }
    elements.extend([rectangle, text])
    NODES[id] = {"x": x, "y": y, "w": w, "h": h}
    return id

def label(x, y, text, color="#495057", size=18):
    elements.append({
        "id": f"lbl{nonce()}", "type": "text", "x": x, "y": y, "width": len(text)*size*0.55,
        "height": size*1.3, "angle": 0, "strokeColor": color, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid", "roughness": 1,
        "opacity": 100, "groupIds": [], "frameId": None, "roundness": None, "seed": nonce(),
        "version": 1, "versionNonce": nonce(), "isDeleted": False, "boundElements": [],
        "updated": 1, "link": None, "locked": False, "fontSize": size, "fontFamily": 1,
        "text": text, "textAlign": "left", "verticalAlign": "top", "containerId": None,
        "originalText": text, "lineHeight": 1.25, "baseline": size*0.8,
    })

def arrow(src, dst, color="#343a40", dashed=False):
    s, d = NODES[src], NODES[dst]
    scx, scy = s["x"]+s["w"]/2, s["y"]+s["h"]/2
    dcx, dcy = d["x"]+d["w"]/2, d["y"]+d["h"]/2
    dx, dy = dcx-scx, dcy-scy
    if abs(dx) >= abs(dy):
        sx = s["x"]+s["w"]+4 if dx > 0 else s["x"]-4
        sy = scy
        ex = d["x"]-6 if dx > 0 else d["x"]+d["w"]+6
        ey = dcy
    else:
        sx = scx
        sy = s["y"]+s["h"]+4 if dy > 0 else s["y"]-4
        ex = dcx
        ey = d["y"]-6 if dy > 0 else d["y"]+d["h"]+6
    aid = f"a{nonce()}"
    elements.append({
        "id": aid, "type": "arrow", "x": sx, "y": sy,
        "width": abs(ex-sx), "height": abs(ey-sy), "angle": 0, "strokeColor": color,
        "backgroundColor": "transparent", "fillStyle": "solid", "strokeWidth": 2,
        "strokeStyle": "dashed" if dashed else "solid", "roughness": 1, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": {"type": 2}, "seed": nonce(),
        "version": 1, "versionNonce": nonce(), "isDeleted": False, "boundElements": [],
        "updated": 1, "link": None, "locked": False,
        "points": [[0, 0], [ex-sx, ey-sy]], "lastCommittedPoint": None,
        "startBinding": {"elementId": src, "focus": 0, "gap": 4},
        "endBinding": {"elementId": dst, "focus": 0, "gap": 6},
        "startArrowhead": None, "endArrowhead": "arrow",
    })
    for nid in (src, dst):
        for el in elements:
            if el["id"] == nid:
                el["boundElements"].append({"type": "arrow", "id": aid})

# palette
INK="#1e1e1e"
IN_S,IN_B="#e8590c","#ffec99"      # inputs (orange)
SC_S,SC_B="#1971c2","#a5d8ff"      # scripts (blue)
RV_S,RV_B="#1971c2","#d0ebff"      # revit tables
SN_S,SN_B="#2f9e44","#b2f2bb"      # sinapi tables
BR_S,BR_B="#e03131","#ffc9c9"      # bridge (red = the key)
OUT_S,OUT_B="#6741d9","#d0bfff"    # outputs (violet)

label(40, 20, "SINAPI × Revit — esqueleto do pipeline de orçamento", INK, 26)
label(40, 56, "Fluxo de dados: inputs → parse → modelo estrela → ponte (crosswalk) → orçamento", "#868e96", 16)

# stage headers
for x, t in [(40,"INPUTS"),(300,"PARSE"),(560,"MODELO ESTRELA"),(900,"PONTE"),(1180,"ORÇAMENTO & RELATÓRIOS")]:
    label(x, 100, t, "#adb5bd", 14)

W,H=210,64
# col1 inputs
rect("revit_in", 40, 140, W, H, "revit_model_summary.json", IN_S, IN_B, 14)
rect("sinapi_in", 40, 470, W, H, "SINAPI_Referência_2026_05.xlsx", IN_S, IN_B, 13)
# col2 parse
rect("parse_revit", 300, 140, W, H, "parse_revit.py", SC_S, SC_B)
rect("parse_sinapi", 300, 470, W, H, "parse_sinapi.py", SC_S, SC_B)
# col3 star schema tables
rect("dim_revit", 560, 110, W, 56, "dim_revit_type", RV_S, RV_B, 14)
rect("fact_qty", 560, 196, W, 56, "fact_revit_quantity", RV_S, RV_B, 14)
rect("dim_comp", 560, 386, W, 56, "dim_sinapi_composicao", SN_S, SN_B, 13)
rect("fact_custo", 560, 472, W, 56, "fact_sinapi_custo", SN_S, SN_B, 14)
rect("dim_loc", 560, 558, W, 56, "dim_localidade", SN_S, SN_B, 14)
# col4 bridge
rect("crosswalk", 900, 150, 230, 76, "revit_sinapi_map.csv\n(crosswalk / ponte)", BR_S, BR_B, 15)
rect("review", 900, 300, 230, 70, "apply_review.py →\nreview_log.csv (LLM, congelado)", "#f08c00", "#ffe8cc", 12)
# col5 outputs
rect("orcamento", 1180, 250, 230, 64, "build_orcamento.py", SC_S, SC_B, 14)
rect("fact_orc", 1180, 350, 230, 56, "fact_orcamento", OUT_S, OUT_B, 14)
rect("xlsx", 1180, 440, 230, 56, "orcamento_MG_{SD,CD}.xlsx", OUT_S, OUT_B, 13)
rect("coverage", 1180, 530, 230, 56, "coverage_report_MG.md", OUT_S, OUT_B, 13)

# arrows
arrow("revit_in","parse_revit"); arrow("sinapi_in","parse_sinapi")
arrow("parse_revit","dim_revit"); arrow("parse_revit","fact_qty")
arrow("parse_sinapi","dim_comp"); arrow("parse_sinapi","fact_custo"); arrow("parse_sinapi","dim_loc")
arrow("dim_revit","crosswalk"); arrow("dim_comp","crosswalk")
arrow("review","crosswalk","#f08c00")
arrow("crosswalk","orcamento"); arrow("fact_qty","orcamento", "#1971c2")
arrow("fact_custo","orcamento","#2f9e44")
arrow("orcamento","fact_orc"); arrow("fact_orc","xlsx"); arrow("fact_orc","coverage")

label(900, 250, "★ chave manufaturada — não há chave natural", "#e03131", 13)
label(1180, 215, "JOIN determinístico (UF, regime) · 0 LLM no runtime", "#6741d9", 12)

doc = {"type": "excalidraw", "version": 2, "source": "sinapiRevit",
       "elements": elements, "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None},
       "files": {}}
out = Path(__file__).resolve().parent.parent / "output" / "esqueleto_projeto.excalidraw"
out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote", out, "—", len(elements), "elements")

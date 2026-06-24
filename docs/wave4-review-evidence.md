# Wave-4 review evidence — `observação` annotations on `orcamento_MG_CD`

Consolidated human-validation record for the wave-4 crosswalk pass. Supersedes the two earlier
review notes (a row-indexed read + a code-line read, now folded in here), adding the
**resolution status** of each incident after issue #1 (`listed_changes`, 2026-06-23).

## Source

Dropbox `/sinapi + revit/validacao/`, sheet `line_items`, column `observação` (col R, last):

- `orcamento_MG_CD_reviewed.xlsx` — 186 rows, 185 annotated; **77 real incidents**, 108 `OK`.
- `orcamento_MG_CD (1) (1).xlsx` — the earlier annotated copy (the `(1) (1)` suffix); same
  column, near-identical themes. The validacao folder has no plain `orcamento_MG_CD.xlsx`.

The `observação` column was added manually by the reviewer. Crosswalk rules referenced below
live in `src/build_crosswalk.py` (`GROUP_RULES`, `revestimento_grupos()`, the thickness/dim
anchors) and `src/apply_review.py` (`review()` decisions).

## Incidents by group — theme → matched composição → resolution

Status legend: ✅ resolved in issue #1 · ⏳ open (P2/P3 backlog) · ⬆ upstream (Revit modeling).

### `porta` → `["Esquadrias - Portas"]`

| Incident | Count | Matched (before) | Resolution |
|---|---|---|---|
| Buscar porta com medida mais próxima | 8 | wrong-size kits (90788 60×210, 94805 87×210) | ✅ `door_width()` snaps to nearest {60,70,80,90,100}×210 on raw descrição (`rule+dim`) |
| Porta de vidro | 9 | wooden sliding door (106148) | ✅ `review()` porta+VIDRO → `gap` (no faithful esquadria-porta for large sliding glass) |
| Não incluir recolocação | 3 | RECOLOCAÇÃO… (100695) | ✅ never-match `RECOLOCA` pool filter |
| Porta não identificada (PORTÃO) | 1 | gap (`PORTÃO DE METAL`) | ✅ `review()` porta+PORTÃO → `gap` (106463 is per-M2 unit mismatch) |

### `janela` → `["Esquadrias - Janelas"]`

| Incident | Count | Matched (before) | Resolution |
|---|---|---|---|
| Buscar itens com vidros inclusos | 5 | "VIDROS NÃO INCLUSOS" (94562) | ✅ anchor drops `VIDROS NÃO INCLUSOS` variants |
| Item muito diferente / fixa-pivotante | 2 | 3-folha corrediça (94572) | ✅ `janela_opening()` anchors opening type first (pivotante/fixa→FIXO) |
| Janela 2 folhas / leaf-count | 2 | 3-folha (94561) | ✅ `janela_folhas()` narrows by leaf count |
| Priorizar abertura, depois nº folhas | 1 | 4-folha c/ bandeira (94573) | ✅ ranking is opening → glass-included → folhas, as requested |

### `louca_sanitaria` → `["Louças e Metais"]`

| Incident | Count | Resolution |
|---|---|---|
| Ainda não verificado — incluir id | 11 | ✅ `review()` keys on fixture identity via `family_name` surfaced into `revit_text`: BARRA DE APOIO→100863, MICTÓRIO→100858, BACIA/ASSENTO→86931, TANQUE→86872, cuba/lavatório by material (INOX→86900, BRANCO GELO→86902) |

### `paredes_alvenaria` → `["Alvenaria de Vedação"]` + thickness anchor

| Incident | Before | Resolution |
|---|---|---|
| Verificar modelagem (MEIO-FIO) ×5 | priced as block 9/14/19 cm | ✅ `parse_revit` excludes `_MEIO_FIO` from wall_types (dropped as artifact) |
| Divisória granito / naval ×3 | priced as block masonry | ✅ excludes `_DIVISORIA`; priced once via `divisoria_leve` |
| Dry wall ×1 | priced as masonry (103323) | ✅ excludes `_DRYWALL`; routed to `divisoria_leve` |
| Pele de vidro não identificada apesar da regra ×1 | anchored as alvenaria (103317) | ✅ excludes `_VIDRO`+`_CORTINA`; routes to `vidro_fachada` |

### `parede_revestimento` → `revestimento_grupos()` router

| Incident | Count | Before | Resolution |
|---|---|---|---|
| Verificar regras — parede empilhada | 4 | external paint (95626) | ✅ int/ext detection in `revestimento_grupos()` routes "- int -" walls to Pintura Interna |
| Parede com 2 revestimentos | 1 | external paint | ✅ same int/ext fix |
| emboço — pintura? | 1 | 104642 | ⬆ upstream modeling (emboço layer named as paint) |
| Medidas mais próx. de revestimento (tile) | 1 | 20×20 (87265) | ⏳ open — tile-size dimension anchor not built (P2) |
| Divisória material / naval | 3 | gap | ✅ NAVAL/DIVISÓRIA → `gap` |
| Verificar modelagem (MEIO-FIO) | 4 | gap | ✅ MEIO-FIO → `gap` |

### `guarda_corpo` / `fechamento_lote`

| Incident | Count | Resolution |
|---|---|---|
| Portão — como identificar | 5 | ✅ PORTÃO → `gap` (priced separately; not as guarda-corpo/gradil) |
| Altura gradil — como ver altura | 1 | ⏳ open — no Revit height attribute to pick 1,10 m vs other (P2) |

### `forro` → `["Forros", "Gesso"]`

| Incident | Count | Resolution |
|---|---|---|
| Pintura PVC — Forro? | 1 | ⬆ upstream (PVA finish modeled as ceiling) |
| Erro de modelagem (LAJE como forro) | 1 | ✅ LAJE → `gap` (exposed slab, no suspended ceiling) |

### `piso_interno` → `["Pisos", "Revestimentos Cerâmicos Internos"]`

| Incident | Count | Resolution |
|---|---|---|
| Bancada modelada com piso | 1 | ✅ BANCADA → `gap` (granite countertop — price as bancada) |

### `drenagem` → `["Telhamento para Cobertura"]`

| Incident | Count | Resolution |
|---|---|---|
| Calha não identificada apesar da regra | 1 | ✅ CALHA → 94227 high (was always `gap`) |

## Resolution summary

Of 77 incidents: **69 resolved directly** by issue #1 design-time rules + **8 meio-fio dropped**
as modeling artifacts. Remaining open items are P2/P3 backlog (tile-size anchor, guarda-corpo
height, contrapiso m³, roof slope) or genuine upstream Revit-modeling errors (now surfaced as
`gap` rather than mis-priced). Total MG/CD moved R$2.94M → R$3.55M, explained by correct sizing
+ the never-priced filter. Determinism hash gate green.

## Two findings worth keeping

1. **Rule-firing failures** flagged by the reviewer (pele de vidro rows 56/144, calha row 80)
   were real: pele de vidro was leaking into alvenaria/revestimento (now excluded → `vidro_fachada`)
   and calha was an unconditional `gap` (now matches 94227). Both fixed.
2. **Reviewer notes ≈ the documented gaps.** The themes line up almost one-to-one with
   `conceptual_gaps.md` / `spec-gaps.md` — independent confirmation of that gap list from a human
   pass. After this wave, the gap docs' resolved items are marked accordingly.

## Cross-cutting patterns (root cause → fix direction)

| Root cause | Groups | Status |
|---|---|---|
| Size/dimension not used as anchor | porta, janela | ✅ `rule+dim` anchors; ⏳ tile-size still open |
| Glass items routed to non-glass SINAPI | porta, janela, vidro_fachada | ✅ upstream exclusion + `gap` routing |
| Modeling artifacts priced | alvenaria, revestimento, forro | ✅ filtered/`gap` |
| Opaque type codes | louca_sanitaria | ✅ `family_name` identity lookup |
| `recolocação` leaking through | porta | ✅ pool filter |

Entry point for further tuning: `crosswalk/upgrade_task_system_prompt.{json,md}`.

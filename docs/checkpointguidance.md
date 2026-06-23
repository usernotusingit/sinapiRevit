# Checkpoint Guidance — `orcamento_MG_CD_reviewed.xlsx` incident → crosswalk-rule mapping

Source: `/sinapi + revit/validacao/orcamento_MG_CD_reviewed.xlsx` (Dropbox), sheet `line_items`.
The `observação` column (col R) carries 185 values across 186 rows; **77 are real incidents**
(the remaining 108 are `OK`). Each incident cluster below is tied to the crosswalk rule actually
steering it. Rules live in `src/build_crosswalk.py` — `GROUP_RULES` (line 34), the dynamic
`revestimento_grupos()` router (line 53), and the thickness/laje anchors (lines 73, 85).

---

## 1. `porta` → rule `["Esquadrias - Portas"]` (`build_crosswalk.py:40`)

| Incident | Count | sinapi_descricao matched |
|---|---|---|
| Porta de vidro | 9 | `PORTA DE CORRER DE MADEIRA, FECHADURA E PUXADOR, COM ALIZAR` (106148) — glass doors mapping to wooden doors |
| Buscar porta com medida mais próxima | 8 | `KIT DE PORTA-PRONTA DE MADEIRA … 60X210CM` (90788) and `PORTA DE ALUMÍNIO DE ABRIR PARA VIDRO … 87X210CM` (94805) — size mismatch (90/80/100/110 → 60 or 87) |
| Não incluir recolocação | 3 | `RECOLOCAÇÃO DE FOLHAS DE PORTA DE MADEIRA … REAPROVEITAMENTO` (100695) |
| Porta não identificada - incluir busca por material | 1 | gap — `PORTÃO DE METAL`, no match |

⚠️ The "Não incluir recolocação" hits contradict spec 6.1, already implemented at
`build_crosswalk.py:103-108` (strips any `RECOLOCA` composição from the pool). Code 100695 still
appears, so this xlsx likely predates that filter, or the filter isn't reaching this path — verify.

## 2. `janela` → rule `["Esquadrias - Janelas"]` (`build_crosswalk.py:41`)

| Incident | Count | sinapi_descricao |
|---|---|---|
| Buscar itens com vidros inclusos | 5 | `JANELA DE AÇO DE CORRER COM 4 FOLHAS PARA VIDRO (VIDROS NÃO INCLUSOS)…` (94562) — wants glass-included variants |
| Item muito diferente | 2 | `JANELA DE ALUMÍNIO DE CORRER COM 3 FOLHAS…` (94572) — pivotante/fixa forced onto corrediça |
| Janela 2 folhas | 2 | `JANELA DE AÇO DE CORRER COM 3 FOLHAS…` (94561) — folha-count mismatch |
| Piorizar sempre abertura, depois número de folhas | 1 | `JANELA DE ALUMÍNIO DE CORRER COM 4 FOLHAS … COM BANDEIRA` (94573) — ranking-priority feedback |

## 3. `louca_sanitaria` → rule `["Louças e Metais"]` (`build_crosswalk.py:43`)

- **Ainda não verificado - incluir id** ×11 — descriptions span `BACIA SANITÁRIA COM CAIXA
  ACOPLADA` (86931), `LAVATÓRIO LOUÇA BRANCA COM COLUNA` (86902), `CUBA DE EMBUTIR … AÇO
  INOXIDÁVEL` (86900), `MICTÓRIO SIFONADO` (100858), `BARRA DE APOIO EM "L"` (100863). Revit
  `type_name`s are opaque codes (`P.13 BRANCO GELO GE17`, `L83C`, `PROF = 40`) → request to add an
  id/material-based lookup.

## 4. `paredes_alvenaria` → rule `["Alvenaria de Vedação"]` + thickness anchor (`build_crosswalk.py:35`, `:73`, `:120`)

All matched via `rule+thickness` (block width 9/14/19 cm from wall thickness):

| Incident | sinapi_descricao (block) |
|---|---|
| Verificar modelagem / Verficar modelagem (5) | MEIO-FIO and CARPETE walls → `ALVENARIA … 9/14/19 CM` (103317/103318/103319/103321) — modeling artifacts priced as walls |
| Divisória granito / Verificar regra - divisória / Divisória regra (3) | DIVISÓRIA NAVAL & GRANITO → `ALVENARIA … BLOCOS` (103316/103329) |
| Dry wall (1) | `ALVENARIA … BLOCOS CERÂMICOS … 9 CM` (103323) — drywall mapped to masonry |
| Pele de vidro não identificada apesar da regra (1) | `ALVENARIA DE VEDAÇÃO … 9 CM` (103317) — curtain wall wrongly anchored as alvenaria |

## 5. `parede_revestimento` → dynamic rule `revestimento_grupos()` (`build_crosswalk.py:53-64`)

No fixed `GROUP_RULES` entry; SINAPI grupo is picked from finish text (Pintura / Cerâmico / Gesso / Massa).

| Incident | sinapi_descricao |
|---|---|
| Verificar regras - parede empilhada ×4 | `APLICAÇÃO MANUAL DE TINTA LÁTEX ACRÍLICA EM PAREDE EXTERNAS…` (95626) — stacked walls misrouted to *external* paint |
| Verificar id, parede com 2 revestimentos ×1 | same 95626 (Pintura Externa) — two-finish wall |
| emboço - pintura? ×1 | `PINTURA LÁTEX ACRÍLICA STANDARD … PAREDES` (104642) — emboço material matched paint |
| Medidas mais próx. de revestimento ×1 | `REVESTIMENTO CERÂMICO … 20X20 CM` (87265) — tile-size mismatch (60×30 → 20×20) |
| Regra divisória - material ×1 | gap — `DIVISÓRIA DE GRANITO`, no match |
| Verificar regras - divisória ×2 | gap — `DIVISÓRIA NAVAL` |
| Verificar modelagem ×4 | gap — MEIO-FIO entries |

The text router keys on `TINTA/PINTURA → Pintura Interna/Externa`, but stacked-wall finishes land
on **Pintura Externa** — the recurring complaint.

## 6. `guarda_corpo` / `fechamento_lote` → `["Guarda-Corpo…"]` / `["Cercas, Protetores e Alambrados"]` (`build_crosswalk.py:44`, `:45`)

- **Portão - como identificar** ×5 and **Altura gradil - como ver altura** ×1 — all map to
  `GUARDA-CORPO DE AÇO GALVANIZADO DE 1,10M …` (99842). Gates (`PORTÃO`) and gradis collide; one
  `PORTÃO DE METAL` is a gap. No height attribute available to pick the right guarda-corpo.

## 7. `forro` → `["Forros", "Gesso"]` (`build_crosswalk.py:37`)

- **Pintura PVC - Forro?** ×1 → `FORRO EM PLACAS DE GESSO … COMERCIAIS` (96113); material is
  `PINTURA PVA` (finish vs. ceiling confusion).
- **Erro de modelagem** ×1 → gap (`LAJE (15)` modeled as forro).

## 8. `piso_interno` → `["Pisos", "Revestimentos Cerâmicos Internos"]` (`build_crosswalk.py:46`)

- **Bancada modelada com piso** ×1 → `PISO EM MÁRMORE … INTERNOS` (98672); a granite countertop
  modeled as floor.

## 9. `drenagem` → `["Telhamento para Cobertura"]` (`build_crosswalk.py:39`)

- **Calha não identificada apesar da regra** ×1 → gap; `CALHA / ZINCO` not found even though the
  rule restricts to roofing — the calha composição isn't in that grupo.

---

## Cross-cutting patterns

| Root cause | Affected groups | Fix direction |
|---|---|---|
| Size/dimension not used as anchor | porta, janela, parede_revestimento (tile) | add dimension parsing like the existing thickness anchor (`build_crosswalk.py:73`) |
| Glass items routed to non-glass SINAPI | porta (glass→wood), janela (vidros não inclusos), vidro_fachada (pele de vidro) | `vidro_fachada` rule exists (`:42`) but pele de vidro lands in alvenaria/revestimento — fix group classification upstream in `parse_revit.py` |
| Modeling artifacts priced | paredes_alvenaria, parede_revestimento, forro (MEIO-FIO, LAJE) | filter non-wall types before crosswalk |
| Opaque type codes | louca_sanitaria | id/material lookup ("incluir id") |
| `recolocação` leaking through | porta | confirm `:103` filter covers this path |

Maps directly to the planned crosswalk parameter-tuning work; entry point
`crosswalk/upgrade_task_system_prompt.{json,md}`.

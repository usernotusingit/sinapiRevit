# Second-act review — `observação` annotations on `orcamento_MG_CD`

Manual validation pass read from the `line_items` sheet (last column, **`observação`**)
of `orcamento_MG_CD (1) (1).xlsx`, located in Dropbox `/sinapi + revit/validacao/`.

- **186 data rows**, **185 annotated**; row 27 is the only blank.
- The large majority read `OK`; the non-`OK` notes are the actionable review signal,
  grouped below by theme with row numbers and the rule/spec they touch.

## Non-`OK` observações by theme

| Theme (observação) | Rows | Count | Maps to |
|---|---|---|---|
| `Buscar porta com medida mais próxima` | 106–113 | 8 | "round up to nearest size" general rule |
| `Ainda não verificado - incluir id` (all louça) | 127–137 | 11 | louca_sanitaria needs element id |
| `Porta de vidro` | 117–125 | 9 | glass doors not in esquadrias-porta (spec §6.1) |
| `Verificar modelagem` (MEIO-FIO etc.) | 52–55, 150, 152, 166, 182, 187 | 8 | curb/meio-fio modeling |
| `Buscar itens com vidros inclusos` (janela) | 81, 83, 85–87 | 5 | windows without glass (spec §6.2) |
| `Verificar regras - parede empilhada` / "parede com 2 revestimentos" | 26, 33–36 | 5 | stacked walls — open spec gap §8.2 |
| `Portão - como identificar` | 68–70, 73, 74 | 5 | portões live in Cercas/alambrados (spec §6.1) |
| `Verificar regras - divisória` / divisória material | 49–51, 145, 154, 183 | 6 | divisória routing |
| `Não incluir recolocação` | 114–116 | 3 | avoid "recolocação" services (spec §6.1) |
| `Janela 2 folhas` / `Priorizar sempre abertura, depois nº de folhas` | 88, 98, 105 | 3 | leaf-count anchor (spec §6.2) |
| `Pele de vidro não identificada apesar da regra` | 56, 144 | 2 | **rule-firing failure** |
| `Item muito diferente` (janela) | 82, 92 | 2 | weak fuzzy match |
| `Calha não identificada apesar da regra` | 80 | 1 | drenagem→gap (consistent with code) |

### One-offs

| Row | Group | observação |
|---|---|---|
| 6 | forro | Erro de modelagem (LAJE como forro) |
| 4 | forro | Pintura PVC - Forro? |
| 29 | parede_revestimento | emboço - pintura? |
| 18 | parede_revestimento | Medidas mais próx. de revestimento |
| 62 | piso_interno | Bancada modelada com piso |
| 71 | guarda_corpo | Altura gradil - como ver altura |
| 126 | porta | Porta não identificada - incluir busca por material (PORTÃO) |
| 154 | paredes_alvenaria | Divisória granito |
| 159 | paredes_alvenaria | Dry wall |

## Two findings worth flagging

1. **Rule-firing failures.** Rows 56 & 144 — *"Pele de vidro não identificada apesar da
   regra"* — and row 80 — *"Calha não identificada apesar da regra."* For calha this is
   consistent with the code (the review pass marks `drenagem` as always `gap`). For pele
   de vidro it suggests the `wall_finish_types` filter isn't catching
   `Parede cortina - PELE DE VIDRO`, which surfaces here as a `paredes_alvenaria` /
   `parede_revestimento` row rather than `vidro_fachada` — worth diagnosing.

2. **Reviewer notes ≈ the documented open gaps.** The themes line up almost one-to-one
   with `docs/conceptual_gaps.md` / `docs/spec-gaps.md`: nearest-size door matching,
   stacked walls, glass doors/windows, leaf-count anchoring, louça ids. Independent
   confirmation of that gap list from a human validation pass.

## Source

Dropbox: `/sinapi + revit/validacao/orcamento_MG_CD (1) (1).xlsx`, sheet `line_items`,
column `observação` (column R, 18th/last). Note: the validacao folder does **not**
contain a file named exactly `orcamento_MG_CD.xlsx`; the annotated copy carries the
` (1) (1)` suffix.

# PrevIA — BIM↔SINAPI Matching Specification (params)

Source: "Mestrado" Google Doc (author: anadribeiro5@gmail.com), synced from the
"Mestrado - June 22, 5:30 PM" revision. Synthesis of the rules and data
specification for matching Revit BIM parameters to SINAPI cost compositions, for
relational analysis. (The doc's business/accelerator material — Programa
Aceleração, the 8 PrevIA pitch questions, Acesso a Mercado — is intentionally
out of scope here.)

## The matching architecture (3 entities)

**SINAPI side** — reference is the monthly `SINAPI_Referência` file (CAIXA).
Association is done **primarily via composições** (not insumos), because
compositions are complete services with description, unit, and unit cost per UF.

| Tab | Content | Use |
|---|---|---|
| CSD | Composições sem desoneração | primary |
| CCD | Composições com desoneração | primary |
| CSE | Composições sem encargos sociais | primary |
| ISD/ICD/ISE | Insumos | complementary lookup only |

**Resolution flow:** `Select UF → select charge regime → consult SINAPI composition → associate to BIM element → calculate`

**Cost formula (global):** `quantity from BIM × SINAPI composition unit cost`

**BIM side** — Revit JSON export. Parameters that act as join keys across the doc:
- `class` / category (`walls`, `doors`, `windows`, `roof_elements`,
  `roof_drainage_elements`, `floor_surfaces`, `wall_finish_surfaces`,
  `ceiling_surfaces`)
- `type_name`, `material`, `level`
- `compound_layers[]`: `order`, `function` (Estrutura / Substrato / Acabamento N),
  `material`, `thickness_m`, `is_core`
- geometry: `width_m`, `height_m`, `area_m2`, `length_m`

## Per-category matching spec (the relational core)

Each category defines: (a) how the BIM element is selected, (b) the SINAPI join
key — written in the doc as *"união entre…"*, (c) the calc.

| Category | BIM selection | SINAPI join key | Calc | Unit |
|---|---|---|---|---|
| **5.1 Vedações (alvenaria)** | layer `function = Estrutura` | segmento + material + espessura | wall area × cost/m² | m² |
| **5.2 Divisórias leves** | term "divisória" in name | "divisória" + material + espessura | wall area × cost/m² | m² |
| **5.3 Vergas/contravergas** | derived from openings | — | opening width + 30cm/side; height ≥10cm or block height | m |
| **5.4 Encunhamento** | derived | — | from wall length | m |
| **6.1 Portas** | `class = doors` | tipo de abertura (from name) + medidas aproximadas | unit cost × qty | un |
| **6.2 Janelas** | `class = window` | tipo de abertura + número de folhas (from name) | cost/m² × area | m² |
| **6.3 Vidros** | "vidro"/"espelho" in name | key terms from name | cost/m² × area | m² |
| **6.4 Componentes/acessórios** | when needed | — | only if itemized separately in cost table | — |
| **7.2 Telhamento** | `class = roof_elements` | segmento + material | cost/m² × **adjusted** area | m² |
| **7.3 Calhas** | category/family/type contains "calha" | "calha" + material aprox. + altura aprox. | cost/m × length | m |
| **7.5 Impermeabilização** | only roof slabs | grupo impermeabilização → manta asfáltica | cost/m² × slab area | m² |
| **8.1 Piso** | slab layer NOT containing "contrapiso" and not `function=Estrutura` | material + (area analysis if needed) | cost/m² × area | m² |
| **Contrapiso** | "contrapiso" in material | "contrapiso" + espessura | cost/m³ × area | m³ |
| **8.2 Revest. parede/teto** | non-structural layer (or material=pintura) | material + interno/externo if needed | cost/m² × area | m² |
| **8.3 Forros** | "forro" in name | "forro" + material | cost/m² × area | m² |
| **8.4 Rodapé/soleira/peitoril** | name contains "rodapé"/"soleira"/"peitoril" | material + altura(parede)/espessura(piso)/dimensões | — | m |
| **8.5 Pintura** | non-structural wall layer + "pintura" in material | material name | cost/m² × area | m² |
| **8.2 Lajes (estrut.)** | `function = Estrutura` | segmento + material + espessura | slab area × cost/m² | m² |

**Recurring join-key primitives:** `segmento`, `material`, `espessura/thickness`,
`dimensões`, `tipo de abertura`, `número de folhas`, plus name-token matching.
Structural elements consistently join on **segmento + material + espessura**;
openings join on **opening type + dimensions/leaves**; finishes join on
**material (+ thickness/area)**.

### Per-category notes (from the doc's `*` annotations)

- **5.1 Vedações:** verify reduction of esquadrias (opening) area from wall area.
- **6.1 Portas:** always match opening type from Revit name — "abrir" doors have no
  "abrir" in SINAPI description; glass doors are NOT in "esquadrias-porta" (filter
  by description); avoid services like "recolocação" (prefer kits/portas); gates
  (portões) live in "Cercas, protetores e alambrados".
- **6.2 Janelas:** match opening type + number of leaves; ignore windows without
  glass included.
- **6.3 Vidros:** SINAPI group may be "Pele de vidro em fachadas" or "Vidros e
  espelhos"; watch zero-cost matches.
- **7.2 Telhamento:** SINAPI group "Telhamento para cobertura"; area must account
  for slope; roof slabs chosen by matching material/thickness.
- **7.3 Calhas:** SINAPI group "Telhamento para cobertura"; rufo similar but absent
  in model; associate to inclined roof only at upper meeting of two roof waters;
  choose by material closest to the roof; chapins under platibanda items?
- **8.1 Piso:** groups "Pisos" or "Revestimentos cerâmicos internos".
- **Contrapiso:** verify wet-area association to choose type; many types → pick a
  standard.
- **8.2 Revestimentos:** all non-structural layers should appear (emboço, reboco);
  select by material name + thickness, choosing a "standard"; stacked walls?
  **For ceilings:** from the slab layers, take non-structural layers and match on
  materials/thicknesses that make sense for the composition (e.g. gypsum
  regularization or chapisco + reboco).
- **8.3 Forros:** also extract perimeter to count edge finishing.
- **8.4 Rodapé/soleira/peitoril:** soleira/rodapé in "Piso", peitoril in "Peitoris
  e chapins"; unit is m — extraction method open.
- **8.5 Pintura:** sequence = sanding prep → sealer primer → putty → final paint;
  groups "Pintura interna"/"Pintura externa"; ceiling paint only if in composition;
  exclude ground-floor slabs.
- **8.2 Lajes:** SINAPI group "Lajes pré-moldadas" or "Radier, piso de concreto e
  laje sobre solo".

**Absent from the supplied model (no extraction path yet):** 7.1 estrutura de
cobertura, 7.4 condutores pluviais, and rufos (7.3) — all "não está presente no
modelo".

## Source classification (BIM vs historical) — all 13 groups

From the **Itens OP** section — which item is extractable from BIM:

- **From BIM:** 5 (vedações/divisórias — alvenaria note: *incluir arrimo*),
  6.1–6.3 (esquadrias/vidros), 7.2 (telhamento), 8 (acabamentos: 8.1 contrapiso,
  8.2 lajes, 8.3 revestimentos, 8.4 forros, 8.5 rodapés/soleiras/peitoris,
  8.6 pintura), 12.1/12.2/12.4 (calçadas, estacionamento, muros)
- **Not from BIM (historical/user data):** 1 (serviços preliminares — all),
  13 (serviços finais — all), 7.5 (impermeabilização — calc/historical),
  1.x administração/canteiro/mobilização
- **BIM *or* historical (conditional):** 2 (terreno/movimento de terra),
  3 (fundações), 4 (estrutura), 6.4 (componentes/acessórios), 7.1/7.3/7.4
  (estrutura de cobertura, calhas/rufos/arremates, condutores pluviais),
  9 (hidrossanitárias), 10 (elétricas), 11 (complementares),
  12.3/12.5/12.6 (drenagem externa, paisagismo, iluminação externa)

**Group 2 conditional rule (detailed in Sinapi-Rascunho):** earthwork/demolition
items only come from BIM when there's *specific evidence* — a demolition phase,
modeled valas with extractable geometry, or contention elements. Key one for
matching: **muro de arrimo** extracts from BIM only with explicit contention
evidence in the item name — a plain wall must NOT be classified as a retaining
wall from ambiguous type text.

## General rules (REGRAS GERAIS)

- High-uncertainty correspondence → **leave unassociated** rather than force a match
- **Avoid zero-priced items** (flagged on vidros / pele de vidro)
- When no element with identical dimensions exists → round **up** to nearest size
- Allow user to **inform building type (tipologia)** to improve associations
- Quality goal: make the *degree of information/uncertainty explicit per estimate*
  rather than automate everything
- Open question: **how to enable user adjustments** ("Como possibilitar ajustes?")

## Open specification gaps (unresolved `?` / `*` notes)

These constrain the relational model and are still undefined:

1. **Area adjustments** — subtract vergas/contravergas/esquadrias areas from wall
   area? (5.1, 5.3)
2. **Roof slope** — `inclined area = plan area ÷ cos(slope angle)`; slope param
   needs extraction (7.2)
3. **Separating roof slabs** from other slabs by material/thickness — undefined (7.2)
4. **Stacked walls** (paredes empilhadas) categorization — undefined (8.2)
5. **"Standard type" selection** when many SINAPI matches exist (contrapiso,
   revestimentos) — needs a default-pick rule
6. **Wet-area association** for contrapiso type choice — needs ambiente/room
   linkage (8.1)
7. **Linear measurement extraction** (m) for rodapé/soleira/peitoril (8.4)
8. **Elements read outside defined groups** — handling undefined
9. Doors: "abrir" type isn't in SINAPI description → match on opening type, not
   literal name; glass doors and gates live in other SINAPI groups (6.1)

## Work-breakdown structure (EAP — Modelagem BIM)

The June 22 revision adds an **EAP (Estrutura Analítica do Projeto)** for the BIM
modeling discipline — a service-level decomposition finer than the matching
categories above. It enumerates the individual services each estimate should
account for, useful for checking coverage of a SINAPI match (e.g. that a wall
finish expands into chapisco + emboço + reboco, or that pintura expands into the
full prep→primer→putty→paint sequence).

**1. Projeto arquitetônico**

| Sub | Services |
|---|---|
| 1.1 Paredes e vedações | alvenaria de vedação; encunhamento; chapisco (int/ext); emboço; reboco |
| 1.2 Esquadrias | portas; janelas |
| 1.3 Cobertura | estrutura do telhado; telhamento; cumeeiras |
| 1.4 Forro | forro; estrutura/suporte; acabamentos e arremates |
| 1.5 Pisos | regularização/contrapiso; piso cerâmico interno; piso de áreas molhadas; rejuntamento |
| 1.6 Revestimentos de paredes | revestimento cerâmico de cozinha; de banheiro; rejuntamento |
| 1.7 Rodapés | rodapé cerâmico; assentamento e acabamento |
| 1.8 Pintura | preparação; lixamento; fundo selador; massa corrida/acrílica; pintura interna; externa; de tetos/forros; de esquadrias (quando aplicável) |
| 1.9 Louças, metais e acessórios | vasos sanitários; lavatórios/bancadas; cubas; tanques; torneiras; chuveiros; registros e acessórios |

**2. Projeto estrutural**

| Sub | Services |
|---|---|
| 2.1 Sapatas | escavação; regularização de fundo; lastro de concreto magro (se previsto); fôrmas; armaduras; concreto; desforma; reaterro e compactação |
| 2.2 Vigas baldrame | escavação; lastro/regularização; fôrmas; armaduras; concreto; desforma; impermeabilização; reaterro lateral |
| 2.3 Pilares | fôrmas; armaduras; concreto; desforma |
| 2.4 Vigas | escoramento; fôrmas; armaduras; concreto; desforma |
| 2.5 Lajes | escoramento; fôrmas/elementos de enchimento (conforme tipo); armaduras; concreto; nivelamento e acabamento; desforma e retirada do escoramento |
| 2.6 Serviços estruturais complementares | aço CA; corte/dobra/montagem de armaduras; controle tecnológico do concreto (se exigido); cura; impermeabilização de elementos em contato com o solo |

Note: the EAP's structural discipline (group 2) corresponds to *Itens OP* groups
3–4, which are **conditional** (BIM-or-historical) — the EAP lists the services
but does not assert they are BIM-extractable.

## Notes for relational modeling

1. Join keys are **heterogeneous per category** — there is no single universal
   match key. The relational design needs a per-category mapping table
   (essentially the spec table above, as config: `category_match_rules`).
2. SINAPI has its **own group taxonomy** ("Telhamento para cobertura", "Pisos",
   "Pintura interna/externa", "Lajes pré-moldadas", etc.) — load it as a dimension
   to constrain matches.

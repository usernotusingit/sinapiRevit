# Conceptual gaps — spec prompt vs. logic prompt

Section-by-section comparison of the two governing system prompts:

- **Spec / requirement layer** — `crosswalk/params_spec_system_prompt.json` (derived from `params.md`)
- **Implemented / code layer** — `crosswalk/crosswalk_logic_system_prompt.json` (derived from
  `parse_sinapi.py`, `parse_revit.py`, `build_crosswalk.py`, `apply_review.py`, `build_orcamento.py`)

The spec is treated as the requirement (what should be true); the code prompt as what is true.
This is a **superset** of `docs/spec-gaps.md` (which listed only the five "real divergences");
notable additions surfaced here are the contrapiso m³ unit mismatch and the 7.3-calhas abandonment.

Refreshed against the **"Mestrado - June 22, 5:30 PM"** spec revision: that revision adds the
EAP work-breakdown (§H below — the largest new gap), category 6.4 (componentes/acessórios), the
ceiling branch of 8.2, and an explicit *incluir arrimo* instruction on 5.1.

## A. Spec categories entirely absent from code

| Spec category | Spec'd join / calc / unit | In code? |
|---|---|---|
| **5.3 Vergas/contravergas** | derived from openings; width + 30cm/side; **m** | ❌ no group, no derivation |
| **5.4 Encunhamento** | derived from wall length; **m** | ❌ no group |
| **7.5 Impermeabilização** | roof slabs → manta asfáltica; m² | ❌ no group (spec also tags it calc/historical) |
| **8.4 Rodapé/soleira/peitoril** | material + dimensões; **m** | ❌ no group, no linear extraction |
| **6.4 Componentes/acessórios** | priced only if itemized separately in cost table | ❌ no group, no conditional itemization |

## B. Categories present but materially diverging

- **Contrapiso unit mismatch** — spec prices contrapiso **per m³** (`cost/m³ × area`); code's
  `GROUP_SPECS` sets contrapiso unit to **M2**. A real unit divergence that changes the number,
  not just the match.
- **7.2 Telhamento — no slope adjustment** — spec calls for **adjusted** area (`plan / cos(slope)`);
  code's `cobertura` uses raw `total_area_m2`, `conversion_factor = 1.0`.
- **7.3 Calhas — spec wants a match, code gives up** — spec defines a real join
  (`'calha' + material + altura`, grupo "Telhamento para cobertura", `cost/m × length`); code's
  `drenagem` review marks it **always `gap`** ("no calha composição in 2026-05"). Capability exists
  in spec, abandoned in code.
- **8.5 Pintura folded into revestimento** — spec treats pintura as its own category with a sequence
  (sanding → primer → putty → paint); code collapses it into `parede_revestimento` (TINTA→104642).
  No multi-step sequence.

## C. Join-key fidelity gaps (matched, but on weaker keys)

- **6.1 Portas / 6.2 Janelas** — spec join keys are *tipo de abertura* and *número de folhas*
  (structured); code only fuzzy-matches the name string (plus a few frozen review picks like
  OCULO→100674). No structured opening anchor analogous to the thickness anchor.
- **5.1 Vedações** — spec key is `segmento + material + espessura`; code anchors on thickness
  (block width) + fuzzy, with no explicit *segmento* dimension.
- **8.3 Forros** — spec note: also extract **perimeter** for edge finishing; code extracts area only.
- **8.2 Ceiling revestimento** — spec (June 22) wants ceiling slabs' non-structural layers matched
  to a sensible composition (gypsum regularization or chapisco + reboco); code's `forro` matches the
  ceiling surface to a single "Forros"/"Gesso" composição, no layer expansion.

## D. Geometric adjustments spec'd, not done

- **5.1 esquadria area reduction** — spec: subtract opening area from wall area; code uses gross
  `total_area_m2` for both alvenaria and finishes.
- **7.2 roof slope** (also in B above).

## E. General rules (REGRAS GERAIS) not enforced in code

| Spec rule | In code? |
|---|---|
| High-uncertainty → leave unassociated | ✅ via `gap` status |
| Make uncertainty explicit per estimate | ✅ via `confidence` / `by_confidence` |
| **Round UP to nearest size** when no exact dimension | ❌ |
| **Avoid zero-priced items** | ⚠️ only *reports* missing price; doesn't avoid zero-cost matches |
| **tipologia** (user-informed building type) | ❌ |
| **muro de arrimo** (5.1 now says *incluir arrimo*, with contention guard) | ❌ (no retaining-wall path at all — spec wants it *included*, code has neither inclusion nor guard) |
| **enable user adjustments** ("Como possibilitar ajustes?") | ❌ (costing is a frozen deterministic join; no adjustment hook) |

## F. Source classification taxonomy — wholly absent in code

The spec's entire §4 (13-group BIM / historical / conditional split) has no representation in the
pipeline:

- **Group 12** (calçadas, estacionamento, muros) — spec says from-BIM; code has no group.
- **Group 2 earthwork evidence rule** and the arrimo contention check — absent; the June 22 spec
  now *adds* arrimo to 5.1 (alvenarias), so the absence is doubly relevant.
- Conditional groups 3/4/9/10/11 — code extracts some (hidrossanitário via `louca_sanitaria`) but
  has no notion of the BIM-vs-historical conditionality. The June 22 spec re-sorts more items into
  this conditional bucket: **6.4** (componentes/acessórios), **7.1/7.3/7.4** (estrutura de cobertura,
  calhas/rufos/arremates, condutores pluviais), **12.3/12.5/12.6** — none modeled in code.

## G. Spec's own open gaps (unresolved on both sides)

Separating roof slabs by material/thickness, stacked-walls categorization, "standard-type"
default-pick rule, wet-area→contrapiso linkage, elements outside defined groups. The spec flags
these as undefined; code doesn't resolve them either.

## H. Service-level decomposition (EAP) — spec implies 1→many, code does 1→1

The June 22 spec adds an **EAP (Estrutura Analítica do Projeto)** that decomposes each discipline
into individual services. This is the largest new conceptual gap, because it changes the *cardinality*
of the match, not just a key or a unit:

- **Spec intent:** one BIM element should expand into the **full set of services** that build it —
  a wall finish into *chapisco + emboço + reboco (+ rejuntamento)*; pintura into *prep → sanding →
  sealer primer → putty → paint*; a floor into *regularização/contrapiso + piso + rejuntamento*; a
  structural element into *escavação + fôrmas + armaduras + concreto + desforma (+ impermeabilização)*.
- **Code reality:** `build_crosswalk.py` maps each `revit_type_key` to **exactly one** SINAPI
  `codigo` (best fuzzy candidate within the grupo). There is no 1→many expansion, no service
  sequence, no bill-of-services per element. `conversion_factor = 1.0`, one row in, one row out.
- **Consequence:** even where the single match is correct, the orçamento **under-counts** the
  composite services the EAP enumerates (the emboço/reboco/rejuntamento/preparo layers). This is a
  structural redesign, not a parameter tweak — it would require the crosswalk to emit a *set* of
  (codigo, factor) rows per element.
- **EAP group 2 (estrutural)** maps to Itens OP groups 3–4, which are **conditional**; code extracts
  **no structural elements at all**, so the entire estrutural EAP (sapatas → lajes) is unbuilt.

*Note — model-data gaps, not spec/code gaps:* the spec flags 7.1 (estrutura de cobertura), 7.4
(condutores pluviais) and rufos (7.3) as "não está presente no modelo" — absent from the source BIM,
so neither side can act until they're modeled.

## Where code exceeds the spec

Code adds groups the spec doesn't enumerate: `louca_sanitaria`, `guarda_corpo`, `rampa_escada`,
`fechamento_lote` (mapping loosely to spec's conditional groups 9–11 / circulação), each with
frozen review decisions.

## Net assessment

The code faithfully implements the **per-category config-table architecture** (spec §7.1) and the
**SINAPI-taxonomy-as-dimension** idea (§7.2), but the gaps cluster in four areas:

1. **Derived & linear quantities** (5.3, 5.4, 7.3, 8.4)
2. **Geometric / unit calcs** (roof slope, opening-area reduction, contrapiso m³)
3. The **source-classification governance layer** (§4), which is entirely unbuilt.
4. **Service-level decomposition** (§H, EAP) — the one structural gap: the spec now expects one BIM
   element to expand into a *bill of services*, while code maps it 1→1. This is the deepest divergence
   and would touch the crosswalk's output cardinality, not just its parameters.

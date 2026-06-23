# Spec gaps — `params.md` vs. crosswalk implementation

Divergences between the PrevIA BIM↔SINAPI matching spec (`/root/ideas/params.md`)
and the current pipeline (`src/parse_revit.py`, `src/build_crosswalk.py`,
`src/build_orcamento.py`). Scope here is the **real divergences only** — places where
the spec asks for something and the code is silent. Items the spec *itself* leaves
open (rodapé/soleira/peitoril extraction method, impermeabilização as calc/historical,
"standard type" pick rule, wet-area linkage) are deferred deliberately and not listed.

The core relational engine already matches the spec: per-category config table
(`GROUP_RULES` + `revestimento_grupos`), grupo + unit + thickness anchoring,
deterministic fuzzy fallback, and the UF/regime costing join. The gaps below are all
on the **derived-quantity** and **geometric-adjustment** frontier.

## 1. Derived linear items not generated (5.3, 5.4)

- **Spec:** §5.3 vergas/contravergas (derived from openings; opening width + 30 cm/side;
  height ≥10 cm or block height; unit **m**) and §5.4 encunhamento (derived from wall
  length; unit **m**).
- **Code:** no group, no generator. `GROUP_SPECS` in `parse_revit.py` only emits types
  for elements that exist in the Revit JSON; nothing derives quantities from openings or
  wall length.
- **Impact:** these line items are entirely absent from the orçamento.
- **Where to add:** a derivation step in `parse_revit.py` that reads opening geometry
  (`width_m`) and wall `length_m`, emits synthetic `verga`/`contraverga`/`encunhamento`
  types (unit M), plus matching `GROUP_RULES` entries.

## 2. Roof-slope area adjustment not applied (7.2)

- **Spec:** §7.2 telhamento uses **adjusted** area — `inclined area = plan area ÷ cos(slope)`.
- **Code:** `cobertura` group uses raw `total_area_m2` with `conversion_factor = 1.0`
  in `build_orcamento.py`; no slope term.
- **Impact:** roof quantities understated by `1/cos(slope)` (e.g. ~6% at 20°, ~15% at 30°).
- **Where to add:** extract a slope parameter per roof type in `parse_revit.py`; fold the
  `1/cos(slope)` factor into `conversion_factor` (or a new quantity adjustment) so the
  costing join stays a pure multiply.

## 3. Opening-area reduction from walls not applied (5.1)

- **Spec:** §5.1 vedações — verify reduction of esquadria (opening) area from wall area.
- **Code:** `paredes_alvenaria` uses gross `total_area_m2`.
- **Impact:** wall (alvenaria) and wall-finish quantities overstated by the opening area.
- **Where to add:** subtract door/window `area_m2` (aggregated per wall/level) from wall
  area during the `parse_revit.py` aggregation.

## 4. Opening join-keys not extracted as structured keys (6.1, 6.2)

- **Spec:** §6.1 portas join on *tipo de abertura* (from name); §6.2 janelas join on
  *tipo de abertura + número de folhas*.
- **Code:** both collapse to generic `rapidfuzz.token_set_ratio` over the descriptor
  string. The opening type / leaf count only help insofar as those words happen to appear
  in the SINAPI description; they are not parsed into structured anchors.
- **Impact:** weaker, less deterministic matches for doors/windows; no anchor narrowing
  like alvenaria/laje get from thickness.
- **Where to add:** parse opening type and leaf count from the Revit name in
  `parse_revit.py`; add an anchor pass in `build_crosswalk.py` analogous to
  `thickness_width_cm` that filters the pool before fuzzy ranking.

## 5. `muro de arrimo` guard absent (Group 2 conditional)

- **Spec:** a plain wall must **not** be classified as a retaining wall (muro de arrimo)
  from ambiguous type text — only with explicit contention evidence in the item name.
- **Code:** no retaining-wall path exists at all, so the misclassification risk is absent
  by omission rather than guarded. If a retaining-wall group is ever added, the guard must
  come with it.
- **Impact:** none today; a latent requirement to honor when Group 2 (terreno/movimento de
  terra) extraction is implemented.
- **Where to add:** when/if an `arrimo` group is introduced, gate it on explicit contention
  tokens in the name and exclude ambiguous plain-wall types.

## Related

- Tracked under the "crosswalk parameter tuning" future-work note.
- Items #2 and #3 are the two that materially change R$ totals.

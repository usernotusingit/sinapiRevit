# Orçamento coverage report — MG / SD

Project: **CÂMARA MUNICIPAL** · SINAPI 2026-05 · 186 line items

**Grand total: R$ 1,832,530.69**

## R$ by match confidence

| confidence | R$ | % of total |
|---|---:|---:|
| high | 456,484.19 | 24.9% |
| medium | 1,331,397.30 | 72.7% |
| low | 44,649.20 |  2.4% |

> **high** = reviewed/strong match · **medium** = grupo/thickness-anchored (semantically bounded, unit-checked) · **low** = verify. Only 2.4% of the total rests on low-confidence matches; 12 items are explicit gaps (excluded, priced manually).

## By chapter

| chapter | items | R$ |
|---|---:|---:|
| Vedações | 50 | 602,261.76 |
| Cobertura | 2 | 435,982.15 |
| Acabamentos | 64 | 402,055.94 |
| Esquadrias | 46 | 142,145.88 |
| Circulação | 13 | 135,993.58 |
| Hidrossanitário | 11 | 114,091.38 |

## Coverage by group (confidence counts)

| group | high | medium | low | none |
|---|---:|---:|---:|---:|
| cobertura | 0 | 1 | 0 | 0 |
| drenagem | 0 | 0 | 0 | 0 |
| fechamento_lote | 3 | 1 | 0 | 0 |
| forro | 1 | 3 | 0 | 0 |
| guarda_corpo | 4 | 3 | 0 | 0 |
| janela | 16 | 9 | 0 | 0 |
| louca_sanitaria | 6 | 2 | 3 | 0 |
| parede_revestimento | 5 | 36 | 1 | 0 |
| paredes_alvenaria | 0 | 50 | 0 | 0 |
| piso_interno | 5 | 4 | 0 | 0 |
| porta | 4 | 16 | 0 | 0 |
| rampa_escada | 1 | 0 | 0 | 0 |

## Explicit gaps — price manually (12)

No reliable SINAPI composição (missing item or unit mismatch). Excluded from the total above.

| group | revit type | reason |
|---|---|---|
| parede_revestimento | Parede básica - int - DIVISÓRIA DE GRANITO     | granite partition — not a paint finish; price manually |
| parede_revestimento | Parede básica - int - DIVISÓRIA NAVAL          | prefab partition panel — price manually |
| parede_revestimento | Parede básica - int - DIVISÓRIA NAVAL          | prefab partition panel — price manually |
| parede_revestimento | Parede básica - int - MEIO-FIO (10) | CONCRETO | curb modeled as wall — exclude from wall finish |
| parede_revestimento | Parede básica - int - MEIO-FIO (15) | CONCRETO | curb modeled as wall — exclude from wall finish |
| parede_revestimento | Parede básica - int - MEIO-FIO (30) | CONCRETO | curb modeled as wall — exclude from wall finish |
| parede_revestimento | Parede básica - int - MEIO-FIO (6) | CONCRETO  | curb modeled as wall — exclude from wall finish |
| parede_revestimento | Parede cortina - PELE DE VIDRO (---, COM MONTA | curtain-wall glazing — price as fachada/vidros manually |
| forro | Forro composto - LAJE (15) | CONCRETO PRÉ-MOLD | exposed slab — no suspended ceiling; price teto/pintura manu |
| drenagem | CALHA | ZINCO | roof gutter (calha) — no SINAPI composição in 2026-05; price |
| porta | PORTÃO DE METAL | metal gate — SINAPI 106463 is per M2; current qty unit misma |
| fechamento_lote | PORTÃO DE METAL | metal gate — SINAPI 106463 is per M2; current qty unit misma |

## Low-confidence matches (4)

Priced, but verify:

| group | revit | -> SINAPI código | desc |
|---|---|---|---|
| parede_revestimento | Parede básica - int - CERÂMICO         | 104641.0 | PINTURA LÁTEX ACRÍLICA ECONÔMICA, APLICAÇÃ |
| louca_sanitaria | ESCOVADO | 100863.0 | BARRA DE APOIO EM "L", EM AÇO INOX POLIDO  |
| louca_sanitaria | PROF = 40 | 86900.0 | CUBA DE EMBUTIR RETANGULAR DE AÇO INOXIDÁV |
| louca_sanitaria | PROF = 40 | 86900.0 | CUBA DE EMBUTIR RETANGULAR DE AÇO INOXIDÁV |

## Known limitations

- **Alvenaria (Vedações):** Revit wall types describe the *finish* (e.g. "Parede básica - int - ... / TINTA"), not the block. There is no masonry spec in the model, so block-type matching is unreliable (all low). Options: use wall `thickness_m` to pick block width, assign a documented default composição, or cost wall finishes only.
- **Fuzzy scores under-rate correct matches** when the Revit name carries extra tokens (cobertura→telha metálica termoacústica is correct yet scores 60). Confidence tiers are conservative; review promotes them.
- Wall finish areas use the model's single computed face area; verify if both faces are needed.
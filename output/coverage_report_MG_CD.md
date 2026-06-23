# Orçamento coverage report — MG / CD

Project: **CÂMARA MUNICIPAL** · SINAPI 2026-05 · 199 line items

**Grand total: R$ 2,986,546.11**

## R$ by match confidence

| confidence | R$ | % of total |
|---|---:|---:|
| high | 392,962.39 | 13.2% |
| medium | 2,460,600.67 | 82.4% |
| low | 132,983.05 |  4.5% |

> **high** = reviewed/strong match · **medium** = grupo/thickness-anchored (semantically bounded, unit-checked) · **low** = verify. Only 4.5% of the total rests on low-confidence matches; 17 items are explicit gaps (excluded, priced manually).

## By chapter

| chapter | items | R$ |
|---|---:|---:|
| Estrutura | 7 | 1,072,367.85 |
| Vedações | 52 | 641,809.95 |
| Acabamentos | 67 | 474,834.47 |
| Cobertura | 2 | 469,505.37 |
| Esquadrias | 47 | 140,843.22 |
| Hidrossanitário | 11 | 113,512.50 |
| Circulação | 13 | 73,672.75 |

## Coverage by group (confidence counts)

| group | high | medium | low | none |
|---|---:|---:|---:|---:|
| cobertura | 0 | 1 | 0 | 0 |
| contrapiso | 0 | 0 | 11 | 0 |
| divisoria_leve | 0 | 1 | 2 | 0 |
| drenagem | 0 | 1 | 0 | 0 |
| fechamento_lote | 0 | 0 | 2 | 0 |
| forro | 1 | 3 | 0 | 0 |
| guarda_corpo | 4 | 3 | 0 | 0 |
| janela | 16 | 9 | 0 | 0 |
| laje_interna | 1 | 6 | 0 | 0 |
| louca_sanitaria | 6 | 2 | 3 | 0 |
| parede_revestimento | 5 | 36 | 1 | 0 |
| paredes_alvenaria | 0 | 49 | 0 | 0 |
| piso_interno | 5 | 4 | 0 | 0 |
| porta | 4 | 4 | 0 | 0 |
| rampa_escada | 1 | 0 | 0 | 0 |
| vidro_fachada | 0 | 1 | 0 | 0 |

## Explicit gaps — price manually (17)

No reliable SINAPI composição (missing item or unit mismatch). Excluded from the total above.

| group | revit type | reason |
|---|---|---|
| forro | Forro composto - LAJE (15) | CONCRETO PRÉ-MOLD | exposed slab — no suspended ceiling; price teto/pintura manu |
| porta | PORTA DE VIDRO COM ESQUADRIA DE CORRER - 2 FOL | glass door (porta de vidro de correr) — not in esquadrias-po |
| porta | PORTA DE VIDRO COM ESQUADRIA DE CORRER - 2 FOL | glass door (porta de vidro de correr) — not in esquadrias-po |
| porta | PORTA DE VIDRO COM ESQUADRIA DE CORRER - 2 FOL | glass door (porta de vidro de correr) — not in esquadrias-po |
| porta | PORTA DE VIDRO COM ESQUADRIA DE CORRER - 3 FOL | glass door (porta de vidro de correr) — not in esquadrias-po |
| porta | PORTA DE VIDRO COM ESQUADRIA DE CORRER - 4 FOL | glass door (porta de vidro de correr) — not in esquadrias-po |
| porta | PORTA DE VIDRO COM ESQUADRIA DE CORRER - 4 FOL | glass door (porta de vidro de correr) — not in esquadrias-po |
| porta | PORTA DE VIDRO COM ESQUADRIA DE CORRER - 4 FOL | glass door (porta de vidro de correr) — not in esquadrias-po |
| porta | PORTA DE VIDRO COM ESQUADRIA DE CORRER - 4 FOL | glass door (porta de vidro de correr) — not in esquadrias-po |
| porta | PORTA DE VIDRO COM ESQUADRIA DE CORRER - 4 FOL | glass door (porta de vidro de correr) — not in esquadrias-po |
| porta | PORTA DE VIDRO DE CORRER - 4 FOLHAS - 250 x 22 | glass door (porta de vidro de correr) — not in esquadrias-po |
| porta | PORTA DE VIDRO DE CORRER - 4 FOLHAS - 400 x 29 | glass door (porta de vidro de correr) — not in esquadrias-po |
| porta | PORTA DE VIDRO DE CORRER - 4 FOLHAS - 670 | glass door (porta de vidro de correr) — not in esquadrias-po |
| porta | PORTÃO DE METAL | metal gate — SINAPI 106463 is per M2; current qty unit misma |
| fechamento_lote | Guarda-corpo - GRADIL V 200 01 PORTÃO 2 | metal gate — SINAPI 106463 is per M2; current qty unit misma |
| fechamento_lote | Guarda-corpo - GRADIL V 200 01 PORTÃO | metal gate — SINAPI 106463 is per M2; current qty unit misma |
| fechamento_lote | PORTÃO DE METAL | metal gate — SINAPI 106463 is per M2; current qty unit misma |

## Low-confidence matches (19)

Priced, but verify:

| group | revit | -> SINAPI código | desc |
|---|---|---|---|
| fechamento_lote | Guarda-corpo - GRADIL V 160 01 4 | 98522.0 | ALAMBRADO EM MOURÕES DE CONCRETO, COM TELA |
| fechamento_lote | Guarda-corpo - GRADIL V 200 01 | 98523.0 | ALAMBRADO EM PERFIS METÁLICOS RETANGULARES |
| divisoria_leve | Parede básica - int - DIVISÓRIA NAVAL  | 102248.0 | DIVISORIA CEGA (N1) - PAINEL PVC E=35MM -  |
| divisoria_leve | Parede básica - int - DIVISÓRIA NAVAL  | 102248.0 | DIVISORIA CEGA (N1) - PAINEL PVC E=35MM -  |
| contrapiso | Piso - int - PORCELLANATO BRANCO 90 X  | 88470.0 | CONTRAPISO COM ARGAMASSA AUTONIVELANTE, AP |
| contrapiso | Piso - int - PORCELLANATO BRANCO 90 X  | 88470.0 | CONTRAPISO COM ARGAMASSA AUTONIVELANTE, AP |
| contrapiso | Piso - ext - PASTILHA AZUL MARINHO 5 X | 88476.0 | CONTRAPISO COM ARGAMASSA AUTONIVELANTE, AP |
| contrapiso | Piso - int - LAMINADO EM CEREZO CARMEL | 88470.0 | CONTRAPISO COM ARGAMASSA AUTONIVELANTE, AP |
| contrapiso | Piso - Porcelanato esmaltado acetinado | 88470.0 | CONTRAPISO COM ARGAMASSA AUTONIVELANTE, AP |
| contrapiso | Piso - int - Porcelanato polido, PEI ≥ | 88470.0 | CONTRAPISO COM ARGAMASSA AUTONIVELANTE, AP |
| contrapiso | Piso - ext - SOLARIUM CLASSIC TRAVERTI | 102803.0 | REFORÇO SUPERFICIAL PARA CONTRAPISOS DE AR |
| parede_revestimento | Parede básica - int - CERÂMICO         | 104641.0 | PINTURA LÁTEX ACRÍLICA ECONÔMICA, APLICAÇÃ |
| contrapiso | Piso - Cerâmica antiderrapante, PEI IV | 88476.0 | CONTRAPISO COM ARGAMASSA AUTONIVELANTE, AP |
| contrapiso | Piso - ext - EPOXI CINZA (0,2) | CONTR | 102803.0 | REFORÇO SUPERFICIAL PARA CONTRAPISOS DE AR |
| contrapiso | Piso - int - CARPETE AZUL (5) | CONTRA | 87620.0 | CONTRAPISO EM ARGAMASSA TRAÇO 1:4 (CIMENTO |
| contrapiso | Piso - int - SOLEIRA EM GRANITO BRANCO | 102803.0 | REFORÇO SUPERFICIAL PARA CONTRAPISOS DE AR |
| louca_sanitaria | ESCOVADO | 100863.0 | BARRA DE APOIO EM "L", EM AÇO INOX POLIDO  |
| louca_sanitaria | PROF = 40 | 86900.0 | CUBA DE EMBUTIR RETANGULAR DE AÇO INOXIDÁV |
| louca_sanitaria | PROF = 40 | 86900.0 | CUBA DE EMBUTIR RETANGULAR DE AÇO INOXIDÁV |

## Known limitations

- **Alvenaria (Vedações):** Revit wall types describe the *finish* (e.g. "Parede básica - int - ... / TINTA"), not the block. There is no masonry spec in the model, so block-type matching is unreliable (all low). Options: use wall `thickness_m` to pick block width, assign a documented default composição, or cost wall finishes only.
- **Fuzzy scores under-rate correct matches** when the Revit name carries extra tokens (cobertura→telha metálica termoacústica is correct yet scores 60). Confidence tiers are conservative; review promotes them.
- Wall finish areas use the model's single computed face area; verify if both faces are needed.
# sinapiRevit — regenerate the deterministic orçamento outputs on demand.
# Outputs (output/*.parquet, *.xlsx, coverage_report_*.md) are gitignored; they
# reproduce byte-for-byte from source via the pipeline below. See tools/hash_gate.py.

PY      ?= python3
UF      ?= MG
REGIMES ?= SD CD SE

.PHONY: regen verify clean help

help:
	@echo "make regen   - rebuild crosswalk + all orçamento outputs ($(UF): $(REGIMES))"
	@echo "make verify  - assert outputs reproduce deterministically (hash gate)"
	@echo "make clean   - delete regenerable outputs from output/"

regen:
	$(PY) src/parse_revit.py
	$(PY) src/build_crosswalk.py
	$(PY) src/apply_review.py
	@for r in $(REGIMES); do $(PY) src/build_orcamento.py --uf $(UF) --regime $$r; done
	@for r in $(REGIMES); do $(PY) src/coverage_report.py --uf $(UF) --regime $$r; done
	@echo "[regen] done — outputs written to output/ (gitignored)"

verify:
	$(PY) tools/hash_gate.py

clean:
	rm -f output/fact_orcamento_*.parquet output/orcamento_*.xlsx output/coverage_report_*.md
	@echo "[clean] removed regenerable outputs (run 'make regen' to rebuild)"

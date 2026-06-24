# sinapiRevit — regenerate the deterministic orçamento outputs on demand.
# Outputs (output/*.parquet, *.xlsx, coverage_report_*.md) are gitignored; they
# reproduce byte-for-byte from source via the pipeline below. See tools/hash_gate.py.

PY      ?= python3
UF      ?= MG
REGIMES ?= SD CD SE

.PHONY: regen verify clean help hooks stamp-spec

help:
	@echo "make regen      - rebuild crosswalk + all orçamento outputs ($(UF): $(REGIMES))"
	@echo "make verify     - assert determinism (hash gate) + spec freshness (spec gate)"
	@echo "make stamp-spec - re-record params.md's fingerprint into the spec snapshot"
	@echo "make clean      - delete regenerable outputs from output/"
	@echo "make hooks      - point git at .githooks (auto-run by regen/verify)"

# Activate the determinism pre-commit hook. Git won't auto-install committed hooks
# (security), so we wire it on the first regen/verify in any clone — idempotent.
hooks:
	@if [ -d .git ] || git rev-parse --git-dir >/dev/null 2>&1; then \
		if [ "$$(git config core.hooksPath)" != ".githooks" ]; then \
			git config core.hooksPath .githooks && \
			echo "[hooks] core.hooksPath -> .githooks (determinism gate active)"; \
		fi; \
	fi

regen: hooks
	$(PY) src/parse_revit.py
	$(PY) src/build_crosswalk.py
	$(PY) src/apply_review.py
	@for r in $(REGIMES); do $(PY) src/build_orcamento.py --uf $(UF) --regime $$r; done
	@for r in $(REGIMES); do $(PY) src/coverage_report.py --uf $(UF) --regime $$r; done
	@echo "[regen] done — outputs written to output/ (gitignored)"

verify: hooks
	$(PY) tools/hash_gate.py
	$(PY) tools/spec_gate.py

# Re-record sha256(crosswalk/params.md) into params_spec_system_prompt.{json,md}.
# Run AFTER refreshing the spec snapshot + gap docs to match a new params.md — this
# turns the freshness gate green again. The content refresh is editorial; the stamp
# just records that it was done.
stamp-spec:
	$(PY) tools/spec_gate.py --stamp

clean:
	rm -f output/fact_orcamento_*.parquet output/orcamento_*.xlsx output/coverage_report_*.md
	@echo "[clean] removed regenerable outputs (run 'make regen' to rebuild)"

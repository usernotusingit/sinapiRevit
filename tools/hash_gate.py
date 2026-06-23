"""Determinism hash gate — verify committed orçamento outputs reproduce from source.

The pipeline is deterministic by contract: same code + same crosswalk + same SINAPI
month + same (uf, regime) => byte-identical output (build_orcamento asserts a SHA-256).
This gate enforces that contract at commit time: it rebuilds the whole pipeline from the
local raw inputs in a throwaway temp dir and checks that each regenerated
`fact_orcamento_<UF>_<REGIME>` matches the committed one (by the same content hash
build_orcamento uses) — and that the crosswalk CSV matches too.

Because the raw inputs (revit_model_summary.json, the SINAPI tables under data/) are
gitignored, this can only run where those inputs are present. If they're missing it
SKIPS (exit 0) rather than blocking — e.g. on a machine without the proprietary data.

Exit codes: 0 = consistent or skipped; 1 = drift detected (commit should be rejected).

Run:  python3 tools/hash_gate.py            # checks all regimes present in output/
      python3 tools/hash_gate.py SD CD      # checks the given regimes only
"""
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DATA = ROOT / "data"
OUTPUT = ROOT / "output"
REVIT_JSON = ROOT / "revit_model_summary.json"
UF = "MG"

# SINAPI snapshot tables the gate treats as source (produced monthly by parse_sinapi).
SINAPI_PARQUETS = [
    "dim_localidade.parquet", "dim_sinapi_composicao.parquet", "dim_sinapi_insumo.parquet",
    "fact_sinapi_custo.parquet", "fact_sinapi_preco_insumo.parquet",
]


def _content_hash(parquet_path: Path) -> str:
    """Replicate build_orcamento's canonical hash: the fact frame serialized as CSV."""
    import pandas as pd
    df = pd.read_parquet(parquet_path)
    return hashlib.sha256(df.fillna("").astype(str).to_csv(index=False).encode()).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inputs_present() -> bool:
    if not REVIT_JSON.exists():
        return False
    return all((DATA / p).exists() for p in SINAPI_PARQUETS)


def _regimes_to_check(argv):
    if argv:
        return [a.upper() for a in argv]
    found = []
    for reg in ("SD", "CD", "SE"):
        if (OUTPUT / f"fact_orcamento_{UF}_{reg}.parquet").exists():
            found.append(reg)
    return found


def _run(py, *args, cwd):
    r = subprocess.run([sys.executable, str(py), *args], capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        sys.stderr.write(f"\n[hash-gate] stage failed: {py.name} {' '.join(args)}\n{r.stderr}\n")
        raise SystemExit(2)


def main(argv):
    if not _inputs_present():
        print("[hash-gate] SKIP: raw inputs (revit_model_summary.json / SINAPI data/) not present.")
        return 0

    regimes = _regimes_to_check(argv)
    if not regimes:
        print("[hash-gate] SKIP: no committed fact_orcamento outputs to verify.")
        return 0

    tmp = Path(tempfile.mkdtemp(prefix="hashgate_"))
    try:
        # stage a clean rebuild environment from source inputs only
        shutil.copytree(SRC, tmp / "src")
        (tmp / "data").mkdir()
        for p in SINAPI_PARQUETS:
            shutil.copy2(DATA / p, tmp / "data" / p)
        shutil.copy2(REVIT_JSON, tmp / "revit_model_summary.json")

        # rebuild: parse_revit -> build_crosswalk -> apply_review -> build_orcamento(*regimes)
        _run(tmp / "src" / "parse_revit.py", cwd=tmp)
        _run(tmp / "src" / "build_crosswalk.py", cwd=tmp)
        _run(tmp / "src" / "apply_review.py", cwd=tmp)
        for reg in regimes:
            _run(tmp / "src" / "build_orcamento.py", "--uf", UF, "--regime", reg, cwd=tmp)

        ok = True
        print(f"[hash-gate] verifying {len(regimes)} regime(s) + crosswalk against output/")

        # crosswalk CSV (the deterministic input the outputs are built from)
        rebuilt_cw = tmp / "crosswalk" / "revit_sinapi_map.csv"
        repo_cw = ROOT / "crosswalk" / "revit_sinapi_map.csv"
        if repo_cw.exists():
            match = _file_hash(rebuilt_cw) == _file_hash(repo_cw)
            ok &= match
            print(f"  {'OK ' if match else 'DRIFT'}  crosswalk/revit_sinapi_map.csv")

        # each regime's fact_orcamento, by canonical content hash
        for reg in regimes:
            rel = f"output/fact_orcamento_{UF}_{reg}.parquet"
            repo_f = ROOT / rel
            if not repo_f.exists():
                print(f"  ----   {rel} (not committed; skipped)")
                continue
            match = _content_hash(tmp / rel) == _content_hash(repo_f)
            ok &= match
            print(f"  {'OK ' if match else 'DRIFT'}  {rel}")

        if not ok:
            print("[hash-gate] DRIFT: committed outputs do not reproduce from current source.")
            return 1
        print("[hash-gate] PASS: all committed outputs reproduce deterministically.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

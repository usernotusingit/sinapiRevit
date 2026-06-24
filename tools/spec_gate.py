"""Spec freshness gate — assert the params_spec snapshot matches crosswalk/params.md.

params.md (the Mestrado Google Doc synthesis — the design intent) now lives in-repo at
crosswalk/params.md. The agent-consumable snapshot crosswalk/params_spec_system_prompt
.{json,md} is a hand-authored projection of it. To stop that snapshot silently drifting
when params.md is revised, the snapshot embeds source_sha256 = sha256(params.md as of the
last sync). This gate recomputes that hash and FAILS if it no longer matches — i.e.
params.md was edited without the snapshot (and the gap docs) being refreshed + re-stamped.

Because params.md is now version-controlled, this gate is portable: it runs anywhere the
repo is checked out — no skip-when-absent path like the determinism hash gate has.

  python3 tools/spec_gate.py           # verify  (exit 1 on drift)
  python3 tools/spec_gate.py --stamp   # re-record the hash + sync date after refreshing

Exit codes: 0 = snapshot is fresh / stamp written; 1 = drift or missing source.
"""
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARAMS = ROOT / "crosswalk" / "params.md"
SPEC_JSON = ROOT / "crosswalk" / "params_spec_system_prompt.json"
SPEC_MD = ROOT / "crosswalk" / "params_spec_system_prompt.md"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _upsert_json(text: str, key: str, value: str, after: str) -> str:
    """Set top-level "key": "value" (string value), inserting after `after` if absent.

    Surgical text edit (not json.dumps) so the large `system` string and any non-ASCII
    bytes are left byte-for-byte intact.
    """
    line = f'  "{key}": "{value}",'
    pat = re.compile(rf'^  "{re.escape(key)}": ".*?",$', re.MULTILINE)
    if pat.search(text):
        return pat.sub(line, text, count=1)
    anchor = re.compile(rf'^(  "{re.escape(after)}": ".*?",)$', re.MULTILINE)
    return anchor.sub(lambda m: m.group(1) + "\n" + line, text, count=1)


def _upsert_md_row(text: str, key: str, value: str, after: str) -> str:
    """Set a `| key | value |` frontmatter row, inserting after the `after` row if absent."""
    line = f'| {key} | {value} |'
    pat = re.compile(rf'^\| {re.escape(key)} \| .*? \|$', re.MULTILINE)
    if pat.search(text):
        return pat.sub(line, text, count=1)
    anchor = re.compile(rf'^(\| {re.escape(after)} \| .*? \|)$', re.MULTILINE)
    return anchor.sub(lambda m: m.group(1) + "\n" + line, text, count=1)


def stamp() -> int:
    if not PARAMS.exists():
        print(f"[spec-gate] ERROR: {PARAMS.relative_to(ROOT)} not found; cannot stamp.")
        return 1
    digest = _sha(PARAMS)
    today = date.today().isoformat()

    j = SPEC_JSON.read_text(encoding="utf-8")
    j = _upsert_json(j, "source_sha256", digest, after="source")
    j = _upsert_json(j, "source_synced", today, after="source_sha256")
    SPEC_JSON.write_text(j, encoding="utf-8")

    m = SPEC_MD.read_text(encoding="utf-8")
    m = _upsert_md_row(m, "source_sha256", f"`{digest}`", after="source")
    m = _upsert_md_row(m, "source_synced", f"`{today}`", after="source_sha256")
    SPEC_MD.write_text(m, encoding="utf-8")

    print(f"[spec-gate] stamped source_sha256={digest[:12]}… source_synced={today}")
    print("  → the snapshot now records the current params.md; commit both together.")
    return 0


def verify() -> int:
    if not PARAMS.exists():
        print(f"[spec-gate] DRIFT: {PARAMS.relative_to(ROOT)} is missing (tracked source).")
        return 1
    spec = json.loads(SPEC_JSON.read_text(encoding="utf-8"))
    recorded = spec.get("source_sha256")
    if not recorded:
        print("[spec-gate] DRIFT: params_spec has no source_sha256 — run: make stamp-spec")
        return 1
    actual = _sha(PARAMS)
    if actual != recorded:
        print("[spec-gate] DRIFT: crosswalk/params.md changed since the spec snapshot was synced.")
        print(f"  recorded source_sha256 = {recorded[:12]}…  actual = {actual[:12]}…")
        print("  Fix: refresh params_spec_system_prompt.{md,json} + the gap docs to match the")
        print("       new params.md, then re-record the fingerprint:  make stamp-spec")
        return 1
    print(f"[spec-gate] PASS: params_spec snapshot matches crosswalk/params.md ({actual[:12]}…).")
    return 0


def main(argv) -> int:
    if argv and argv[0] == "--stamp":
        return stamp()
    return verify()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

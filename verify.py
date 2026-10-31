#!/usr/bin/env python3
"""One-command check of this package. Python 3.8+, standard library only.

    python verify.py

1. SHA-256 of the two deposit files must equal the hashes Stephen Hope
   confirmed against his own deposit; one disclosed edit — two absolute server paths in
   null_model_test.py were replaced by placeholders on 31 Oct 2026 (docs/PROBE_PROVENANCE.md).
2. The three built-in demos of the adapter must return the verdicts the
   package claims: a deliberately broken scorer is caught, a content-sensitive
   one is not, and with no genuine replies the result is UNTESTED, not "pass".

Exit code 0 only if every line is OK. Nothing here imports our engine.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent
PROBE = ROOT / "probe"

EXPECTED_SHA256 = {
    "null_input_probe.py": "ebb9bb1bf4fa9378e7faf1ae72df8c519f3026584ef6fd0f0e1c1fd07da9a549",
    # published copy: his file with two absolute server paths replaced (see docs/PROBE_PROVENANCE.md)
    "null_model_test.py": "180babb85e3c3593b3756a78b169e9a53ffca5e2be7fe771d703bc6b11f34d73",
}
EXPECTED_DEMOS = {
    "lookup": "NO_CHANGE_OBSERVED",   # broken on purpose: grade depends on position only
    "sensitive": "SENSITIVE",         # grade depends on the text
    "untested": "UNTESTED",           # no genuine reply supplied
}


def main() -> int:
    ok = True
    print("1. Deposit files (one disclosed edit: two server paths)")
    for name, want in EXPECTED_SHA256.items():
        got = hashlib.sha256((PROBE / name).read_bytes()).hexdigest()
        good = got == want
        ok &= good
        print(f"   {'OK  ' if good else 'FAIL'} {name}  {got}")

    print("2. Adapter demos")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for demo, want in EXPECTED_DEMOS.items():
        run = subprocess.run(
            [sys.executable, "probe_adapter_public.py", "--demo", demo],
            cwd=PROBE, capture_output=True, text=True, encoding="utf-8", env=env,
        )
        verdict = ""
        for line in run.stdout.splitlines():
            if line.strip().startswith("verdict:"):
                verdict = line.split(":", 1)[1].strip()
        good = run.returncode == 0 and verdict == want
        ok &= good
        print(f"   {'OK  ' if good else 'FAIL'} --demo {demo:<9} expected {want:<18} got {verdict or '(none)'}"
              + ("" if run.returncode == 0 else f"  exit={run.returncode}"))
        if not good and run.stderr:
            print("        " + run.stderr.strip().splitlines()[-1])

    print("\nALL OK" if ok else "\nSOMETHING FAILED — please tell us what, per line.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

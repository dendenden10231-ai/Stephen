#!/usr/bin/env python3
"""Download the four DeepSeek runs of Helix Standard Test Set v1.1 (Zenodo 19501062).

    python fetch_test_set.py            -> ./hst_data/

Standard library only. We do not republish the dataset; this fetches it from Zenodo.
"""
import sys
import urllib.request
from pathlib import Path

RECORD = "19501062"
FILES = [
    "baseline_deepseek_500_20260408_140000.jsonl",
    "constitutional_run1_500_20260408_142543.jsonl",
    "constitutional_run2_500_20260408_145253.jsonl",
    "constitutional_run3_500_20260408_151855.jsonl",
    "summary_stats.json",
    "final_comparison_report_20260408.txt",
    "README.md",
]

out = Path(sys.argv[1] if len(sys.argv) > 1 else "hst_data")
out.mkdir(exist_ok=True)
for name in FILES:
    url = f"https://zenodo.org/records/{RECORD}/files/{name}?download=1"
    with urllib.request.urlopen(url) as resp:
        (out / name).write_bytes(resp.read())
    print("ok", name)

"""Stephen Hope's null_input_probe.py (unmodified) applied to his own
Helix Standard Test Set v1.1 (Zenodo 19501062), deposited DeepSeek replies.

Two scorers, both taken from his own reports:
  A  "success"   — summary_stats.json success_rate: a reply came back (HTTP-level)
  B  "markers"   — final_comparison_report: which epistemic markers a reply carries
Plus one extra arm OUTSIDE his probe, labelled as ours: a reply consisting only
of the markers, to see whether the marker score reads substance or form.
"""
import ast
import io
import json
import random
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

PROBE_DIR, DATA_DIR = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(PROBE_DIR))
import null_input_probe as probe  # noqa: E402  (his file, unmodified)

RUNS = {
    "baseline (no system prompt)": "baseline_deepseek_500_20260408_140000.jsonl",
    "run 1: point-form invariants": "constitutional_run1_500_20260408_142543.jsonl",
    "run 2: Helix-TTD strict": "constitutional_run2_500_20260408_145253.jsonl",
    "run 3: canonical whitepaper": "constitutional_run3_500_20260408_151855.jsonl",
}
MARKERS = ["FACT", "HYPOTHESIS", "ASSUMPTION", "VERIFIED", "INFERENCE", "PREMISE"]


def reply_of(row):
    raw = row.get("deepseek")
    try:
        obj = ast.literal_eval(raw) if isinstance(raw, str) else raw
        return obj.get("response") if isinstance(obj, dict) else None
    except (ValueError, SyntaxError):
        return None


class Success:          # A: the reliability figure — independent of the text by construction
    def score(self, text, test_id):
        return "OK" if text is not None else "FAIL"


class Markers:          # B: marker usage as counted in his comparison report
    def score(self, text, test_id):
        found = [m for m in MARKERS if re.search(r"\[" + m + r"(?:\]|:|\s)", text or "")]
        return "+".join(found) or "none"


def probe_once(scorer, replies):
    buf = io.StringIO()
    with redirect_stdout(buf):
        verdict, rows = probe.run([{"id": str(k)} for k in range(len(replies))],
                                  scorer, replies, random.Random(20261030))
    arms = {a: 0 for a in ("empty", "neutral", "noise", "deranged", "refusal")}
    tested = moved = 0
    for _, ref, _, m in rows:
        if ref is None:
            continue
        tested += 1
        if m:
            moved += 1
            for a in m:
                arms[a] += 1
    return verdict, tested, moved, arms


out = {}
for name, fname in RUNS.items():
    rows = [json.loads(l) for l in open(DATA_DIR / fname, encoding="utf-8") if l.strip()]
    replies = [reply_of(r) for r in rows]
    res = {"positions": len(replies), "with_reply": sum(r is not None for r in replies)}
    for label, scorer in (("A_success", Success()), ("B_markers", Markers())):
        v, t, mv, arms = probe_once(scorer, replies)
        res[label] = {"verdict": v, "tested": t, "moved": mv, "inert": t - mv, "moved_by_arm": arms}
    # Our extra arm (not part of his probe): markers only, no content.
    mk = Markers()
    real = [mk.score(r, k) for k, r in enumerate(replies) if r is not None]
    only = [mk.score(" ".join(f"[{m}]" for m in s.split("+")) if s != "none" else "", k)
            for k, s in enumerate(real)]
    res["ours_markers_only_same_score"] = sum(a == b for a, b in zip(real, only))
    res["marker_distribution_top"] = sorted(
        {s: real.count(s) for s in set(real)}.items(), key=lambda x: -x[1])[:4]
    out[name] = res

print(json.dumps(out, indent=1, ensure_ascii=False))

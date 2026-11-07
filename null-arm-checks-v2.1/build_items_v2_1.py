# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""build_items_v2_1.py: rebuild the mutation items from passages_reconstructed.json with the v2.1 oracles and the widened
measure vocabulary, keep a trace of every candidate, and compare with the frozen v2 items (nothing in v2 is changed).

    python3 build_items_v2_1.py          writes mutation_items_v2_1.json (kept + dropped, with status/reason) and
                                         exclusions_v2_1.json (candidates for which no variant could be built)
    python3 build_items_v2_1.py --check  verifies both files byte-for-byte against a rebuild

Output files are deterministic (sorted keys, LF).
"""
from __future__ import annotations

import collections
import json
import sys

import mutation_set as ms

HERE_ITEMS, HERE_EXCL = "mutation_items_v2_1.json", "exclusions_v2_1.json"


def run() -> tuple[str, str]:
    passages = json.load(open("passages_reconstructed.json", encoding="utf-8"))
    exclusions: list = []
    items = ms.build(passages, exclusions)
    v2 = {x["id"]: x for x in json.load(open("mutation_items_v2.json", encoding="utf-8"))}
    kept = [x for x in items if x["status"] == "kept"]
    kept_ids = {x["id"] for x in kept}
    summary = {
        "candidates_with_variant": len(items), "kept": len(kept), "dropped": len(items) - len(kept),
        "v2_kept": len(v2), "v2_ids_still_kept": len(set(v2) & kept_ids),
        "v2_ids_no_longer_kept": sorted(set(v2) - kept_ids),
        "new_in_v2_1": sorted(kept_ids - set(v2)),
        "new_by_mutation": dict(collections.Counter(x["mutation"] for x in kept if x["id"] not in v2)),
        "no_variant_candidates": len(exclusions),
        "no_variant_by_reason": dict(collections.Counter(
            (e["reason"].split(":")[0]) for e in exclusions)),
    }
    return (json.dumps(items, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            json.dumps({"summary": summary, "exclusions": exclusions}, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


def main() -> int:
    items, excl = run()
    if "--check" in sys.argv:
        ok = open(HERE_ITEMS, encoding="utf-8").read() == items and open(HERE_EXCL, encoding="utf-8").read() == excl
        print("v2.1 items and exclusion log: rebuild identical" if ok else "v2.1 items or exclusion log differ from a rebuild")
        return 0 if ok else 1
    open(HERE_ITEMS, "w", encoding="utf-8", newline="\n").write(items)
    open(HERE_EXCL, "w", encoding="utf-8", newline="\n").write(excl)
    s = json.loads(excl)["summary"]
    print(json.dumps(s, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

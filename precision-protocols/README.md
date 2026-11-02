# precision-protocols — dated measurement records, 1 and 2 November 2026

These are the machine-readable records behind the precision figures quoted in the
2 November letter. Each was produced by a script in the private repository (`102`)
and is published here unedited, except where noted below.

| file | what | command that produced it | SHA-256 as published |
|---|---|---|---|
| `fresh4-core-v57-2026-11-01.json` | fresh4: VitaminC clean hold-out, seed 8888, 800 pairs (400 REFUTES / 400 SUPPORTS) — HELIX v5.7, strict and alarm modes, status distribution, timing, core hashes | `PYTHONUTF8=1 python3 scripts/замер_fresh4_ядро.py` | `bf4a9178bc73bf3f…` (see the note) |
| `aggrefact-1117-v57-2026-11-01.json` | AggreFact-SOTA test split, 1 117 pairs — HELIX v5.7, both modes, per-pair statuses | `PYTHONUTF8=1 python3 scripts/замер_aggrefact_1117.py --метка v5.7-точность-01-11` | `ec13335d5772ee92fc3c6492f44d0445c860591b5d4772f3ee392387b7b9416b` |
| `aggrefact-1117-main-base-2026-11-01.json` | the same corpus on the pre-v5.7 main base — the A/B counterpart of the row above | `PYTHONUTF8=1 python3 scripts/замер_aggrefact_1117.py --метка main-база` | `52d20bde5d31bd8ae6439f4a0da116b9ee323fb3da781d45f9851045f0896823` |

The full 64-character hash of every file, and of the private original it came from,
is in `_hashes.json`.

## What was changed, and what was not

One file was edited before publishing, and the edit is one string. In
`fresh4-core-v57-2026-11-01.json` the sample path was recorded as an absolute path on
the author's machine; it is replaced by a repository-relative one:

- from `C:\Users\Admin\Desktop\102\docs\замеры\bucket1_rows_fresh4.csv`
- to `102/docs/замеры/bucket1_rows_fresh4.csv`

Nothing else was touched — no reformatting, no re-serialization. The private
original's hash is `74255810bf6c99d5049c26ad52940756b030aea7dbccea48d319766b2a5f9c79`;
the published copy's is `bf4a9178bc73bf3f…`, recorded with both values in
`_hashes.json`. This is the same treatment we applied to Stephen's own probe files
and documented in `probe-package-2026-10-30/PROBE_PROVENANCE.md`: we do not publish
each other's machine layouts, and we say so where we do it.

## What these files do and do not contain

They carry per-pair ids, labels, statuses and aggregate metrics. They do **not**
contain the AggreFact row texts: the corpus is CC-BY-ND-4.0 (NoDerivatives) and gated,
so ids and the selection rule are published instead of the text, as explained in
`probe-package-2026-10-30/corpus-license-note.md`. That is a licence constraint, not
a concealment.

## Reproducing the fresh4 row

`bucket1_rows_fresh4.csv` (800 pairs) is part of the private repository, so a reader
cannot re-run our engine from here — the engine is closed. What a reader can do is
check the arithmetic: every number in the JSON is a count over the status column of
the same file, and the confidence intervals are Wilson 95 % on those counts.

# HELIX × null-input probe — a package for Stephen Hope

Prepared 30 October 2026 by Dzianis Vashkevich (HELIX / Mr. Helix / AK-MASTER,
helixcom.org) for Stephen Hope (Helix AI Innovations Inc., helixaiinnovations.ca).
The two companies are unrelated; no priority is claimed in either direction.

This repository lets you check, on your own machine and without any access to
our code, what we reported after running **your** probe on **our** instruments.

## Check it in five minutes

Python 3.8+ only, no dependencies, Windows / macOS / Linux:

```bash
git clone <this repository>
cd stephen-hope-helix-probe
python verify.py
```

Expected output, verified on Windows 11 with a default console on 30 Oct 2026:

```
1. Deposit files, byte for byte
   OK   null_input_probe.py  ebb9bb1bf4fa9378e7faf1ae72df8c519f3026584ef6fd0f0e1c1fd07da9a549
   OK   null_model_test.py  5a8f3a14313c0edc3357ac652e4826397fc4569e715f166c30954878516301f8
2. Adapter demos
   OK   --demo lookup    expected NO_CHANGE_OBSERVED got NO_CHANGE_OBSERVED
   OK   --demo sensitive expected SENSITIVE          got SENSITIVE
   OK   --demo untested  expected UNTESTED           got UNTESTED

ALL OK
```

What each line proves:

| line | proves | does not prove |
|---|---|---|
| SHA-256 of your two files | they are your deposit, byte for byte — the hashes you confirmed in your PART 1 | anything about our instruments |
| `--demo lookup` | your probe catches a scorer whose grade depends only on the position (the answer-key shape you found in your own battery) | — |
| `--demo sensitive` | a scorer that reads the text is not falsely flagged | — |
| `--demo untested` | with no genuine reply the verdict is `UNTESTED`, never "pass" | — |

## Our results — what is checkable and what is an assertion

| instrument | your verdict | positions | status for a reader |
|---|---|---|---|
| HELIX core (number/inequality reconciliation) | `SENSITIVE (partial)` | 45 moved of 60, 15 inert | **assertion**: the scorer is in our private tree. Per-position grades under every arm are in `results/`; the 60 positions are identified by (id, model, origin) in `probe/positions_60.json`, so the corpus can be regenerated (row texts withheld for the CC-BY-ND-4.0 licence, see `docs/corpus-license-note.md`) |
| AK-MASTER mechanical battery | `SENSITIVE` | 12 of 12 | **assertion**, grades in `results/` — including the defect you singled out: length-matched noise returning a clean `F0|W0` |
| Mr. Helix quote reconciliation | `SENSITIVE` | 6 of 6 | **assertion**, grades in `results/` |

Re-run on 30 Oct 2026 gave the same numbers to the digit. To make the first
row reader-verifiable rather than reported, see the hosted-endpoint offer in
[`OFFER.md`](OFFER.md).

## Layout

| path | content |
|---|---|
| `verify.py` | the one-command check above |
| `probe/null_input_probe.py`, `probe/null_model_test.py` | your deposit, unmodified |
| `probe/probe_adapter_public.py` | our adapter: injectable scorer, same corpora and seed 20261028, no import of our engine; prints UTF-8 so it does not crash on a default Windows console |
| `probe/positions_60.json` | the 60 HELIX positions keyed by (id, model, origin) + SHA-256 of each summary |
| `results/` | per-position grades (`*.json`, `results-per-position.md`) and the probe's unedited stdout |
| `docs/PROBE_PROVENANCE.md`, `docs/corpus-license-note.md` | hashes, dates, licence reasoning |
| `OFFER.md` | further cross-checks we can run with you, free and paid |

The same probe package is also public at
https://github.com/dendenden10231-ai/HELIX_GOVERNANCE/tree/main/probe-package-2026-10-30

## Defects found on our side while building this, disclosed

- `positions_60.json` first keyed positions by `id`; in our 1 117-row corpus
  only 862 ids are distinct, so `id` alone would mis-assign replies. Fixed: the
  key is (id, model, origin), all 60 distinct, with a summary digest fallback.
- The adapter crashed with exit code 255 on a default Windows console before
  printing a verdict (it prints "—"). Fixed in the adapter; your files untouched.

"I'd rather you find what's wrong with it than I never learn" — the same
standard applies here. If any line of `verify.py` fails for you, that is the
most useful thing you can send us.

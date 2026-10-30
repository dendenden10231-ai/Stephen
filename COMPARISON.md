# Two ways of looking at the same judge, side by side

Topic for both: your article "No second refinery".

| | **File 1: HELIX on its own** | **File 2: your null-arm probe design** |
|---|---|---|
| Folder | [`live-run/`](live-run/REPORT_helix_native_run_en.md) | [`judge-probe-on-this-topic/`](judge-probe-on-this-topic/README.md) |
| Who chooses the evidence | HELIX, by live search | You and us, fixed per claim and per arm |
| Retrieval is tested | **Yes** (what it finds and what it misses) | **No**, deliberately bypassed |
| Question it answers | What does the product conclude, and how well does it search and hedge? | Does the judge's label depend on the evidence it is given? |
| Controlled | No, one run, not deterministic | Yes, arms A–G built mechanically from the genuine evidence |
| Measures | Findings, levels, refusals, coverage | Sensitivity and specificity, refusal contract R1–R5 |
| Cost of the run | about $2.42 (spend-counter estimate) | about $3 for arms A+G, about $7 for all arms (estimate) |
| State | **Done** | **Built, not run** |

## What each can and cannot tell you

- File 1 can show a real defect in search (it never reached Reuters, S&P Global or RBN) and a real strength (it refused to confirm the $28 gap and said the ranking was low-confidence). It **cannot** say whether the judge would give the same verdict if the evidence were swapped for noise.
- File 2 can show whether the judge is content-blind or length-sensitive. It **cannot** say whether the product finds the right sources.
- The two are complementary, not alternatives. A judge can search poorly and read well, or the reverse.

## Where they already touch

- Your `[AS GIVEN]` on the $28 crude gap: your caution held. File 1 could not reproduce the figure on the benchmark it used (about $24.8, different window).
- Your `[AS GIVEN]` on "Russia produces 70% of its gasoline": file 1 did not test it. Our manual check (file 1, section 6) found it holds as a late-August low, which fits the way you held it back. In file 2 it is claim c02, where your design expects a refusal rather than a label.

Everything here is a single run on one topic. Twelve claims are twelve.

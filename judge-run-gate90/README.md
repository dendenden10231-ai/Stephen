# Row-level labels of our judge run on your arms (05 Nov 2026)

This is the per-claim data behind section 6 of our PR #4 appendix (comment 6659028944), so that you can
re-score it yourself instead of trusting our summary.

- File: `gate90_метки_05_11.json` (SHA-256 `c452789db1a7a8143ce0a49e1474dd8b8c641cb0ea9571d660c6af58d9af86b7`).
- `рецепт_выбора`: how the 30 claims were chosen (SHA-256 of the claim id; selection hash `a8aaaff0c21e6bdc`).
- `проход_1_A`: pass 1, arm A only, **before** our wrapper fix — 9 of 30.
- `проход_2`: pass 2, same 30 claims, **after** the fix — arms A, G_deranged, C_num_noise: A 29 of 30,
  G_deranged 0 of 30 false determinate, C_num_noise 6 of 30 false determinate.
- Arms file used: your `null-arm-checks-v2/arms_v2.json`, SHA-256 `2d1771c38f2e67d0f8fb0aad871a700b492cf77cfdd59949f352acf3b02be3b5`.

What it does not show (as in the appendix): k=1, 30 of your 48 claims, and pass 2 reuses the claims that exposed
the defects, so it is a development result, not a held-out measurement. The six false-determinate C rows are
listed by id in the file. Labels were copied from the server-side job logs; the raw job files remain on the
server and we can extract any of them on request.

## Addendum: held-out run on the 18 unused claims (2026-11-05, later the same day)

File: `heldout18_метки_05_11.json` (SHA-256 `e5a9e7ed2497e35245b7b3b161327d1c272e924be0adb4450a2e6a02ed02b10e`). The 18 claims are the 48 with all three arms minus the 30 used
above (selection hash `77e427d047729a58`). Same judge, same wrapper as pass 2 (after the fix). k=1 per arm.

| arm | held-out result |
|---|---|
| A_genuine | **17 of 18** correct (0.944) |
| G_deranged | **0 of 18** false determinate |
| C_num_noise | **7 of 18** false determinate (0.389), all SUPPORTED |

- Pooled with the 30-claim slice (48 claims, but the first 30 were used to find and fix the defects, so only the
  18 are held-out): A 46 of 48, G 0 of 48, C 13 of 48 (0.27).
- The single A miss is `c03.s0.unit_swap` ("barrels per week" in the claim, "b/d" in the evidence; the judge said
  SUPPORTED, expected REFUTED). It is the same day-versus-week unit class as our open defect M53.
- **C is not fixed.** 7 of 18 is above the 0.10 threshold from the planning document and worse than the 6 of 30
  on the development slice. The planned fix (a gate on direct support, in progress on our side) is not applied to this run.
- Operational note: arm A was run twice because two instances of our script started at once (our mistake). Both runs
  gave identical labels on all 18 rows. Cost by our counter: $2.2445 for the whole held-out run, $1.1243 of it the duplicate A.
- Caveats: k=1, 18 claims from one corpus, thresholds unvalidated.

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

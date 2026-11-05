# USGS second-domain audit package — what is here and how to check it

Prepared 2026-11-05 for Stephen (external reviewer) and for the audit thread on PR #4.
Nothing in this package was sent anywhere by us; publication is the owner's decision.

All five artifacts were produced with **0 model calls and 0 USD**: they are deterministic
Python over HTTP GET answers from the public USGS catalogue, or over our own frozen files.

## Files

| file | what it is |
|---|---|
| `corpus_frozen.json` | The frozen source corpus: 12 event identifiers requested from the USGS catalogue, 11 usable records, 1 absent. Frozen 2026-11-03, **never re-shot**. Each record holds the request URL, HTTP status, SHA-256 of the raw answer, magnitude, depth, place, event time, update time, review status and the catalogue text. |
| `руки_usgs_заморозка.json` | 56 test arms in 6 families built on that corpus, re-frozen 2026-11-05 with a declared provenance for the identifier list. Fields per arm: `family`, `expected`, `claim`, `evidence`, `source_id`, `comparable_quantity`, `sensor_verdict`, `sensor_in_scope`, `sensor_matches_expected`. |
| `список_запросов.json` | The single source of the 12 identifiers, with a provenance class and a file-level evidence pointer on every line. Added to the requested five files; see "Addition" below. |
| `проба_происхождения_05_11.json` | Live measurement of 2026-11-05 answering one question: does `us7000tugp` exist in the catalogue at all. 5 GET requests, 0 model calls. |
| `проба_окна_повтор_05_11.json` | Re-measurement of the same window later on 2026-11-05, both by the `count` route and by the `geojson` route, with UTC request timestamps. It exists because a second reviewer on our side got one event more than we did. |
| `README_EN.md` | This file. |

## How to verify the hashes

There are **two different digests** for the arms file, and confusing them is easy. Both are
given in full so that either can be checked without our code.

1. Byte-level SHA-256 of each file (`sha256sum` on Linux/macOS, `certutil -hashfile <f> SHA256`
   on Windows). Expected values are listed in `SHA256SUMS.txt`, and the
   corpus value is the pre-commitment one:

   ```
   f282d84e07d5d5656d97f4808c1415fcb32189c1ead65c29c47423156af00b5c  corpus_frozen.json
   ```

2. The **freeze digest of the arms** — `5708832f72365a07902103583f6cfc091594406fd64c0f4f949751b68300075b`
   — is *not* the hash of the file's bytes. It is the SHA-256 of the canonical serialization of
   the `руки` array only (`json.dumps(..., ensure_ascii=False, sort_keys=True, indent=2)`,
   UTF-8). That is what the field `sha256` inside the file declares, and it is what our
   earlier messages quoted. Reproduce it standalone:

   ```
   python -c "import json,hashlib;d=json.load(open('руки_usgs_заморозка.json',encoding='utf-8'));\
   print(hashlib.sha256(json.dumps(d['руки'],ensure_ascii=False,sort_keys=True,indent=2).encode('utf-8')).hexdigest())"
   ```

   The previous arms digest was
   `1aa37726986f7d04f6f68d566fc8705aa906f6d7e49149d2c08e12fae3d196f2` (freeze of 2026-11-03).
   It is superseded: the 2026-11-05 re-freeze added the provenance statement and rewrote the
   evidence text of the refusal arm. Any publication quoting `1aa37726…` refers to the older
   arms, not to these.

## How the identifier list was obtained — the honest account

Until 2026-11-05 the list had **no provenance artifact at all**. It was hard-coded twice:
10 identifiers in the probe script of 2026-11-02 and 12 identifiers in the freeze script of
2026-11-03. The two copies diverged, and no run ever recorded which query produced the two
added identifiers. `список_запросов.json` now holds one list with a class per line:

| class | count | meaning |
|---|---|---|
| `записанный_запрос` (recorded request) | **5** | the identifier lies inside `docs/замеры/проба_домена_usgs_2026-11-02.json` — one recorded query, window 2026-10-25 to 2026-11-01, `minmagnitude=5`, `limit=5` |
| `не_записан` (not recorded) | **6** | present in working lists, but no run produced it; what checked it is unknown, so it cannot serve as evidence of a request |
| `сконструирован` (constructed) | **1** | `us7000tugp`, deliberately typed as a negative control; its absence was then confirmed by measurement |

So: **6 of the 12 identifiers have no recorded origin, and 1 was constructed.** We state this
directly rather than summarizing it as "absence confirmed".

## `us7000tugp` is a constructed negative control, not a catalogue record

The arm that depends on it is `R_absent_source` (exactly one arm of the 56), whose expected
verdict is `REFUSAL`: a claim about an event that has no obtainable evidence must not be
labelled supported or refuted.

Measured 2026-11-05 by `scripts/проба_происхождения_usgs.py` (5 GET, 0 model calls):

- window `starttime=2026-10-24`, `endtime=2026-11-04`, `orderby=time`, `limit=20000`,
  `format=geojson`, **no magnitude filter on purpose** — 3 236 distinct event ids returned,
  list digest prefix `77dd57a2b254f15a` (as of ~11:03 UTC; the re-measurement below gives
  3 237 because the catalogue is live);
- `us7000tugp` is **not** among them, and the `eventid` route answers **HTTP 404**;
- three controls from the same window on the same route answer **HTTP 200**
  (`us7000tule`, `us7000tuhv`, `aka2026vpcige`), so "absent" is not "we cannot query".

The window count is a live-catalogue number and moves as USGS adds or revises events. A second reviewer on our side queried the same window on 2026-11-05 and got **3 237**, one more than
our **3 236**. We re-measured instead of arguing (`проба_окна_повтор_05_11.json`, 4 GET,
0 model calls):

- at 11:39:37 UTC the `/fdsnws/event/1/count` path answered **3237**;
- at 11:39:38 UTC the `geojson` route with our exact parameters answered **3237** distinct
  ids, list digest prefix `a38eb1d01c2d696f`;
- the first probe, at ~11:03 UTC the same day, had answered **3236** with digest prefix
  `77dd57a2b254f15a`;
- so the reviewer's number was right, there is **no route discrepancy**, and the difference
  is one event the catalogue gained inside the window during those ~36 minutes.

One parameter note that costs nothing to repeat: `format=count` on the `/query` path is
**invalid** (HTTP 400, the service lists the accepted formats); the way to ask for a quantity
is the separate `/count` path. Both are recorded in the same artifact.

The absence claim does **not** rest on any of these counts. At 11:39:39 UTC `us7000tugp` was
still not in the list and still answered **HTTP 404** on the `eventid` route, while three
control identifiers from the same window answer 200 on that route.

## What the corpus freeze did and did not change

- `corpus_frozen.json` was **not** re-shot. The pre-commitment digest `f282d84e…00b5c` still
  binds exactly the same bytes, and the record for `us7000tugp` inside it still says
  "absent from the catalogue" with HTTP 404. Re-freezing a published pre-commitment
  retroactively would have been worse than admitting the methodological gap.
- The arms file **was** re-shot, because a provenance field had to be added and the refusal
  arm's evidence text had to declare the identifier as constructed.

## Scope limits of the numbers inside

- Of the 56 arms, the bare sensor is competent on **33** (`sensor_in_scope: true`) and agrees
  with the expected label on **33 of 33**. The three families outside its competence are
  `C_noise_no_quantity`, `C_num_same_value` and `R_absent_source`; those are decided by the
  composition seam, not by the sensor, and the sensor's `OK` on them is not a pass.
- These arms are a domain-transfer probe, not a calibrated benchmark: one catalogue, 56 arms,
  k=1, no confidence thresholds calibrated on them.

## Addition to the requested file list

The task named five files. `список_запросов.json` and `проба_окна_повтор_05_11.json` are a
sixth and a seventh, added because the README's central claim — the 5 / 6 / 1 provenance
split — is unreadable without the first, and because the second reviewer's number (3 237)
deserves an answer with timestamps rather than a sentence. Neither contains machine paths
beyond repository-relative ones, nor secrets. If the reviewer prefers the package to be
exactly the five requested files, these two can be dropped without touching the others.

## Your audit list, item by item (self-check: `python audit_selfcheck.py`, output in `audit_selfcheck_output.txt`)

You named four things you would audit. We ran each ourselves first, deterministically (no model, no network):

| your item | result | how |
|---|---|---|
| passages genuinely from the catalogue | **PASS** for `A_supported` (11 of 11: magnitude and place equal the stored record). **Declared exception:** the evidence of `C_num_contradicting` (11) and `D_distorting` (11) is *altered by construction* (e.g. `magnitude 5.3` where the stored record says 4.8; `depth 23.0 km` where it says 10), because a contradicting or distorting arm needs a value the record does not hold | `audit_selfcheck.py` checks 2 and last line |
| every label known by construction, not by oracle | **PASS**: the expected label is a function of the family only (56 of 56); the sensor verdict is recorded but is not an input to any label | check 1 |
| noise arms carry no comparable quantity | **PASS** with the split you wrote: `C_noise_no_quantity` has no digit at all (11); `C_num_same_value` repeats only the claim's own number (11); `C_num_contradicting` carries exactly one contradicting quantity per arm (11) — the per-arm count you asked for in the manifest is 1 | checks 3 |
| distorting arms actually distort | **PASS**: in all 11 `D_distorting` arms the evidence value differs from the claim value | check 4 |

No record requires a paid tier or a key: all 12 request URLs are the plain public FDSN `eventid` GET
(`earthquake.usgs.gov`). Your condition ("a paid-tier record belongs in the freeze header") is therefore
vacuous: the header says none.

## Known defects in this package — found by the same self-check, not hidden

1. **The sensor's `comparable_quantity` field misreads the magnitude.** In 33 arms whose claim is about a
   magnitude (`A_supported`, `C_num_same_value`, `C_num_contradicting`, 11 each) the field says
   `spatial_distance` with values such as `4800.0`: the sensor read "magnitude 4.8 at 199 km" as 4.8 km and
   converted to metres. In `R_absent_source` it says `mass_stock`. The labels do not depend on this field,
   and the sensor's *verdicts* on the 33 in-scope arms still agree with the expected labels, but "agrees 33 of 33"
   is therefore **agreement of the verdict, not evidence that the sensor understood the quantity**. We did not
   change the frozen file; the field is the sensor's reading, not ground truth. The unit classifier needs a
   magnitude class; that is an open item on our side.
2. **Our checker's conflicting-sources defect (agrees where it should refuse) is not fixed.** We told you the
   freeze would not be chosen to hide it. The 56 arms contain no `R_pair` family, so this freeze neither exercises
   nor hides it.
3. `D_distorting` and `C_num_contradicting` evidence differs from the catalogue (see the first table): do not read
   those 22 passages as quotes.

## Noise contract

`NOISE_CONTRACT.md` — the three rules in your wording, with the arm family each one is exercised by.

## Checksums

`SHA256SUMS.txt` — `sha256sum -c SHA256SUMS.txt` on Linux/macOS. This README itself is listed there, so
any later edit is visible as a changed hash rather than a silent one. The two digests that matter are unchanged:
corpus `f282d84e07d5d5656d97f4808c1415fcb32189c1ead65c29c47423156af00b5c`, arms freeze
`5708832f72365a07902103583f6cfc091594406fd64c0f4f949751b68300075b` (dated 2026-11-05, issued before you score
these arms; our own judge has not been run on them — the only verdicts inside the file are those of our
deterministic sensor, recorded per arm, 0 model calls).

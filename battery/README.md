# The AK-MASTER public battery endpoint

Live since 2 November 2026. This is the hosted endpoint agreed in the 30 October
exchange: an endpoint rather than source, per-position discipline, `UNTESTED` where
no genuine reply is supplied, and the exact check list published.

| | |
|---|---|
| check list | `GET https://helixcom.org/api/ak/battery/checks` |
| grade one position | `POST https://helixcom.org/api/ak/battery/grade` with `{"text": "...", "position": "2"}` |
| published copy of the list | `battery-check-list-2026-11-02.json`, SHA-256 `8cd44e575e6a9ce9b6eb7a81309faf4f68963842188c954f901a7cbbc413491a` |
| cost | 0 $, no model call, no network call |

## What the list actually says

The list is **computed, not typed**. The battery is run over the 12 PROBE-AK
calibration scenes (the same corpus the published null-input probe grades use) and
the emitted check codes are collected:

- **29 checks emitted; 28 model-free; 1 paid.**
- The paid check is `6.TST-TW` (the hostile-reader test). It is not dropped from the
  list. It returns `NOT_CONFIGURED` with the sentence *"this does not mean the text
  passed the test"*.
- The request schema accepts only `text` and `position`. There is no field that can
  reach the judge flag, so no caller — including a mistaken one — can spend money.
- `UNTESTED` on empty input, never a pass, per the probe's own rule.
- The grade string keeps the format of our published probe scorer,
  `F{fail_count}|W{warning_count}|{sorted FAIL/WARN codes}`, so numbers from this
  endpoint are directly comparable with the results in
  `probe-package-2026-10-30/results-per-position.md`.

## Caps

10 requests per minute per address, 60 graded positions per address per day,
2 000 per day in total. The values are returned inside the `/checks` response, as is
the honest caveat that the counter is per process, so a restart resets it.

## Correction to our own earlier statement

Our published response of 30 October said *"of the 28 AK-MASTER checks, 27 are
model-free"*. That figure came from a 29 August run over a whole book, where the
battery emitted 28 codes. Measured on the calibration corpus on 2 November the
battery emits **29 codes, 28 model-free and 1 paid**. Both numbers are dated where
they appear; the endpoint publishes the current one, because a list the reader can
verify beats a number the reader must trust.

## Proven, not promised

A regression test patches `call()` on all five model providers and the DNS resolver,
then posts a satirical, declarative paragraph — the exact case `TST-TW` exists for.
The request still returns HTTP 200 with `model_calls: 0` and `NOT_CONFIGURED` on the
paid check. Worst adversarial input measured on 2 November: 20 000 characters of
repeated news-style sentences costs 915 ms, no runaway matching.

## Why this is a form screen, not a fact checker

`AK-MASTER screens literary FORM. It does not check facts, numbers or truth` — that
sentence is returned in every grade response. Your objection about the noise arm
(`F0|W0|` with one identical set of form warnings on every position) was correct
about a form detector, so the public description now says exactly that rather than
implying more.

## Running your probe against it

The contract in `probe-package-2026-10-30/probe_adapter_public.py` applies unchanged:
implement `score(text, test_id) -> str` as an HTTP call to `/api/ak/battery/grade`,
keep the same arms and seed (20261028), and expect `UNTESTED` for any position with
no genuine reply. Nothing in this endpoint needs our source code.

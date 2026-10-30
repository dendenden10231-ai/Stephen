# AK-MASTER — the literary engine

> **About this English edition.** Translated from the Russian product passport on
> 30 October 2026. The body is the edition of 21 August 2026 with the update of
> 7 October; every figure carries the date it was measured. File paths refer to
> our private repository. Model providers have changed since August; current
> measured figures are in [`../OFFER.md`](../OFFER.md).

## Numbers and state as of 27 October 2026

| What | 21 August | 7 October | 27 October | Command |
|---|---|---|---|---|
| canon blocks: total / enforced by code / document | 14 / 13 / 1 | 14 / 13 / 1 | **14 / 13 / 1** (re-measured 30 Oct: unchanged) | `python3 -m engine.coverage_validator` |
| blocking gaps | 0 | 0 | **0** (cross-checks 4 of 4) | same |
| engine modules | 134 | 156 | **161** | `ls engine/*.py` |
| site routes (whole site) | 170 | 182 | **253 HTTP + 1 WebSocket** | `scripts/посчитать_маршруты.py`; the same number is served by `GET /api/meta/counts` |
| tests | 4 360 | 5 912 | **5 107 root suite + 2 927 HELIX suite** (`pytest --collect-only`) | `python3 -m pytest --collect-only -q` |
| engine and canon changes since 21 Aug | — | 91 | **104** | `git log --since=2026-08-21 -- engine discipline` |

Why fewer tests are visible than on 7 October: 5 912 does not reproduce today —
the root `tests/` collects 5 107 and `helix_pipeline/tests/` 2 927 (8 034 in
total). The 7 October measurement was not saved with a command that gives exactly
those two numbers, so it is kept as a historical record, not a current count.

**On the site:** a workshop menu (How to use, Books, Write, Discuss, Narrate,
Book passport, Check a chapter); chapter check = free mechanical analysis (27 of
28 checks without a model) plus an optional paid judge; **the free analysis
agreed with the paid judge on 11 of 12 categories** on a whole book. The
instrument analysed 29 books, 2 428 scenes, 7.2 million characters.

---

## History: edition of 21 August 2026

**Measured: 21 August 2026, commit `dcb6903`.** Every number below was produced
by a command on that day, and the command is given next to it. Do not trust a
number in a document — run it: documents age, commands do not.

---

## Update of 7 October 2026: what changed since August

*Measured by commands on 7 Oct 2026. The edition below is from 21 August and its
numbers are stale; the correct ones are here.*

| What | 21 August | 7 October | Command |
|---|---|---|---|
| Engine modules | 134 | **156** (22 new) | `ls engine/*.py \| grep -v __init__ \| wc -l` |
| Site routes (AK-MASTER and shared) | 170 | **182** of 201 | `/openapi.json` of the live site |
| Canon blocks enforced by code / blocking gaps | 13 / 0 | **13 / 0** | `python3 -m engine.coverage_validator` |
| Tests (shared suite with Mr. Helix) | 4 360 | **5 912**, 0 failures | `python3 -m pytest -q` |
| Engine and canon changes | — | **91** commits | `git log --since=2026-08-21 -- engine discipline` |

**New detectors** (each names the place in words): repetitive gestures, empty
dialogue, repetitive weather, broken time intervals, forbidden verbatim phrases,
traces of machine generation, invisible characters, scene type from a
description (the SCN code before writing).

**Analysis without a model.** The whole library — 29 books, 2 428 scenes — was
run without a single model call. The free analysis agreed with the paid judge on
11 of 12 failure categories.

**The paid judge.** 42–46 % of non-literary ballast (repetitions, service
reports) was removed from the canon the judge receives on every call; all the
literature stays. A prefilter for the most expensive check, TST-TW: precision
69 %, recall 51 % — it saves 57 % of judge calls and issues no verdict itself.

**On the site:** a "Check a chapter" screen (free analysis, judge optional), a
book passport (a deliberate authorial device is not read as a defect), 24 canon
tools over MCP for Claude, Cursor and Claude Desktop.

**Narration:** Russian and Polish via Azure Speech, English via Mistral; the
Russian letter "ё" is restored automatically where the reading is unambiguous.

---

## What it is, in one paragraph

A tool that writes a book under discipline rather than "improving the style".
The difference is fundamental. An ordinary AI assistant makes text smoother.
AK-MASTER checks **whether the text holds together as a narrative**: did the
hero pay for what he got; can the text tell testimony from conjecture; is a
device passed off as an event; is a motive replaced by a pretty phrase.

The rule set is called the AK-6.7 canon (base) and AK-6.8 (extension) — more
than thirty named protocols, each with its own trigger condition and marker.

## Who it is for

For an author writing something long who is afraid of losing coherence by the
twentieth chapter. Not for turnkey text generation: the engine does not replace
writing, it sets the boundaries within which writing stays honest.

---

## How it can be checked

| What | Number | Command |
|---|---|---|
| Canon blocks: total / enforced by code / document only | **14 / 13 / 1** | `python3 -m engine.coverage_validator` |
| Blocking gaps | **0** | same |
| Source-canon paragraphs parsed | **444** | same |
| Engine modules | **134** | `ls engine/*.py \| grep -v __init__ \| wc -l` |
| Site routes | **170** of 189 shared | `python3 -c "from api.main import app; print(len(app.openapi()['paths']))"` |
| Tests | **4 360 passed, 0 failed, 18 skipped** | `python3 -m pytest -q` |

**What "13 of 14" means.** The fourteenth block is marked `DOC_ANCHOR` — a
decision not to enforce it in code, not a gap. The distinction matters: a system
that paints the unresolved green is useless.

---

## How it is built

`engine/` (134 modules) and `discipline/` (the canon texts). One FastAPI service,
the same process as the other two products.

Discipline is applied **before generation, not after**. Before writing a scene
the author closes eleven gate fields: scene type, point of view, the hero's
price, two readings, a kinesics plan and so on. An unclosed field does not block
writing — the scene goes out as a draft with an honest note of which field was
missing.

## Three things this engine does that a typical assistant does not

**It tells "not filled" from "filled with generic words".** A field filled with
"a scene about love" gets the status WEAK, not CLOSED. Formally filled — not in
substance.

**It checks a canon code for membership, not for shape.** `SCN-99` looks like a
real scene code, but there is no such code in the canon — the field does not
close. Found on 20 August and fixed: before that an invented code stamped a
canonical pass.

**It measures coverage against what was promised, not what was written.** If the
plan promised three turns in a chapter and the text has one, coverage honestly
drops and the book does not get a PASS.

---

## Honest history, failures included

**The canon was nearly lost.** The version in `main` diverged from a branch that
was about to be deleted. It was restored from that branch and checked line by
line. A good argument for discipline over history, not only over code.

**Twelve failing tests explained by the environment.** An earlier edition of this
passport said "2817 passed, 12 failed" and attributed the failures to a conflict
between the `mcp` package and the system `PyJWT` in the test environment. The
diagnosis confirmed itself: today **4 360 passed, 0 failed**. Same tests,
different environment.

**Lemmatiser migration.** The move to `pymorphy3` at one point created a cluster
of false positives in several detectors. Fixed, but it remains a reminder: a
dependency on an NLP library is not free and needs its own supervision.

**A gate that could not be passed.** The gate read eleven fields, but the request
model declared none of them — they could not be sent from the site at all.
Discipline worked as a rubber stamp, not as a gate. Fixed.

---

## What this engine does NOT do

- It does not write the book for the author and does not claim to.
- It does not judge artistic quality. "Well written" is not its category; its
  category is "holds together or falls apart".
- It has no external users. Three years of development, zero outside authors who
  have run their book through it.
- It is not certified under load.

---

## Where to look next (private repository)

| File | What is there |
|---|---|
| `discipline/КАКОЙ_КАНОН_БРАТЬ.md` | which canon to take and why |
| `docs/AK_MASTER_CANON_CLOSURE_REPORT.md` | how the canon was closed, with findings |
| `docs/WORK_PLAN.md` | the live plan, read by a program |

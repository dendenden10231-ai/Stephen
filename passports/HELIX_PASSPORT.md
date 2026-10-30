# HELIX — deterministic audit of a language model's output

> **About this English edition.** Translated from the Russian product passport on
> 30 October 2026. The top section is the state as of 23–25 October; the rest is
> the history from August to 7 October, and where its numbers are stale the
> dated sections above win. File paths refer to our private repository.
>
> **Re-measured 30 October 2026:** 113 core modules (38 577 lines); 51 876 lines
> of specification in 23 files; 949 states named by the specs / 0 unreachable
> across 5 contract specs. The research provider and the paid judge run on
> Gemini; Azure is no longer used for the judge.

## State as of 23 October 2026

**Measured 23 Oct 2026, evening, commit `4cc5c3b`.** Every number was produced by
a command on that day.

| What | Number | Command |
|---|---|---|
| Engine modules | **110** (113 on 30 Oct) | `ls helix_pipeline/engine/*.py \| grep -v __init__ \| wc -l` |
| HELIX tests | **2 818, zero failures** (plus 1 223 in `mr_helix`) | `python3 -m pytest helix_pipeline/tests -q`, `python3 -m pytest mr_helix/tests -q` |
| States named by the specs / of them the code cannot return | **949 / 0** | `python3 -m helix_pipeline.engine.helix_contract_audit` |
| Specification lines | **51 758** (51 876 on 30 Oct) | `cat helix_pipeline/docs/specs/*.md \| wc -l` |
| Live site | `helixcom.org/api/helix/healthz` → 200, research provider `gemini` | `curl` |

### Measured accuracy (on an open dataset, $0)

**Clean control, version 4.3 (24 Oct 2026).** Sample fresh4: VitaminC (only real
English-Wikipedia edits with numbers, SUPPORTS/REFUTES), seed 8888, 400 + 400
pairs, none of the 4 000 pairs on which rules were tuned or checked before. The
v4.3 rules were not tuned on it.

| Version | Precision | Recall | F1 | False alarms |
|---|---|---|---|---|
| HELIX v4.1 | 0.895 | 0.682 | 0.774 | 0.080 |
| **HELIX v4.3** | **0.901** | **0.705** | **0.791** | **0.0775** |

Speed of v4.3 on a CPU: 0.191 s for 800 pairs, about 0.24 ms per pair (best of 5
runs, one machine). Wilson intervals for the 400 + 400 pairs were not
recomputed; on HaluBench the picture is weaker (below). The table below is the
earlier v4.1 measurement on fresh3; after rule selection that sample no longer
counts as clean.

HELIX number reconciliation (`привязка_чисел.py`, v4.1) against the open model
Vectara HHEM-2.1-Open. Dataset — VitaminC, only real English-Wikipedia edits with
a number in the claim; labels by humans, not by us. **Sample fresh3: 800 pairs
(400 "supports", 400 "refutes"), seed named before the run, rules not tuned on it
(we once inspected the sample for money pairs).**

| Method | Precision | Recall | False alarms | F1 |
|---|---|---|---|---|
| HELIX v4.1, "contradiction" | **0.896** [0.859–0.924] | **0.755** [0.711–0.795] | **0.087** [0.064–0.119] | **0.820** |
| HELIX v4, same pairs | 0.884 | 0.740 | 0.098 | 0.805 |
| HELIX v3 (before fixes), same pairs | 0.873 | 0.603 | 0.087 | 0.713 |
| Vectara HHEM-2.1-Open | 0.591 [0.539–0.640] | 0.530 [0.481–0.578] | 0.367 [0.322–0.416] | 0.559 |

Conformal threshold calibration ("false alarms no higher than α") was recomputed
for v4.1: at α = 10 % we measured 10.5 % on fresh3 (interval 7.9–13.9 % contains
10 %).

**A second dataset — HaluBench (numeric slice, 1 481 pairs, six sources) — gives a
different picture.** HELIX catches 9 % of hallucinations (flag precision 0.74,
false alarms 3 %); Vectara HHEM at threshold 0.5 catches 76 % but calls 54 % of
correct answers hallucinations (F1 0.656 vs 0.163 for HELIX). HELIX is a narrow
high-precision filter for numeric claims, not a general hallucination detector;
"better than HHEM" holds only for VitaminC numeric edits.

**Limits of the measurement that must not be omitted:**
- on VitaminC — only numeric claims from English Wikipedia; not measured on
  Russian, Polish or model outputs; on HaluBench financial questions HELIX recall
  is 0.12;
- the v3 → v4 gain comes almost entirely from one class — money amounts (mostly
  film box office): 49 of 52 refutations vs 1 of 52; outside money +7 correct at
  −1 false;
- false alarms were 0.075 on the development sample and 0.098 on the new one: the
  honest number is the second;
- this is not "HELIX is better than HHEM in general": HHEM is a general text
  consistency model, HELIX checks numbers.

### Added since 7 October

- **Wikipedia anchoring.** The points of a topic article are checked against
  primary sources one by one, each with a status: confirmed, refined, refuted or
  unchecked. The report shows separately what was found beyond the article.
- **Heuer's matrix.** Implemented from chapter 8 of Heuer (CIA, 1999):
  diagnosticity counted on contradictions only; the conclusion-reversal set
  searched per Heuer; sensitivity to a single piece of evidence; verbal
  confidence per ICD 203.
- **Two source axes** per STANAG 2511: source class A–D sits next to the ECT
  evidence level, not inside it. Independence is taken as the minimum, not the
  mean.
- **Number reconciliation:** units and multipliers; numbers written in words;
  "more / less" comparisons; years not confused with quantities; a new status
  "contradicts the source" separated from "not found".
- **Paywall bypass.** If a page is closed, the abstract is fetched by DOI:
  OpenAlex → Semantic Scholar → Crossref, with a check that the topic matches.
- **GOVERNANCE v1.4:** law checked against the text of the EU AI Act; decision log
  (OAS) as a SHA-256 chain; synthetic-content signals shown to a human only,
  without automatic downgrade; a single "human required" matrix; signs of model
  text degeneration (Phase 9) computed by code from the literature: n-gram
  repetition, vocabulary diversity, compression, truncation.
- **Justification registers** for all four specifications. For every rule it is
  recorded what it rests on: L — literature; P — invented, not calibrated; N —
  source not named; F — factual error. Specifications read in full:
  INTELLIGENCE, GOVERNANCE, TRACE (5 959 lines) and GI (8 965 lines). Literature
  checked via OpenAlex.
- **Providers:** Gemini and Qwen for research and news. Comparison of one news
  item by two models — `/api/newsroom/compare`.
- **Statistics of scientific papers:** statcheck — recomputing p-values from t, F
  and χ².
- **Two axes all the way (D-5).** Next to the ECT evidence level the report shows
  "confidence of the conclusion" (ICD 203): source properties — anonymity,
  retelling, document provenance, conflict of interest — limit the conclusion,
  not the evidence level. The `ect` field is not changed.
- **Source topic and a free cascade (I-5).** For an unreadable page an open
  version is sought (OpenAlex, Crossref, NASA NTRS); the document is checked for
  "is it about this" before numbers are reconciled. The threshold is not
  calibrated.
- **"Check it yourself" page:** `helixcom.org/check` — a claim and a source, a
  verdict by code without a model, "agree / disagree" feedback.

### Position among competitors

A table of 15 companies is kept internally. What we can show already: the
verdict is computed by code, not by a second model; two source axes per
intelligence-analysis standards; a check for circular "AI citing AI" references;
a hash-chained decision log; number-reconciliation accuracy on an open dataset
with intervals. What they have and we do not: customers; certificates (ISO
42001, SOC 2); calibrated thresholds; an external audit.

### Honest limits as of 23 October

- Most thresholds and multipliers are **not calibrated**. This is recorded in the
  registers rule by rule.
- Accuracy is measured on one task: number reconciliation. There is no accuracy
  yet for the seven fabrication types as a whole.
- No customers, no external audit, one author.

---

## Update of 25 October 2026: measured on news and papers

| Measurement | Result |
|---|---|
| Number reconciliation, AggreFact-SOTA test news summaries (1 117 pairs) | signal precision 0.77, false alarms 0.02, catches 16 % of errors (numeric only) |
| Same on new news (val, 1 236, no tuning) | precision 0.85, false alarms 0.02, catches 21 %; 2 s for the whole set |
| Competitor on the same data: Vectara HHEM-2.1-Open | catches 68 %, false alarms 15 %, ~3 s per news item; our measurement matched the published one (BAcc 76.56 vs 76.55) |
| statcheck against the reference program (144 631 results from papers) | agreement 0.9998, extra alarms 0 |
| Effect sizes from 2 000 PubMed abstracts | precision 100 of 100 (sample), recall ≈ 0.94 |

**Where HELIX is better:** 7× fewer false alarms, 1 500× faster than HHEM, names
the place of the discrepancy. **Where it is worse:** it does not see errors that
are not in numbers (87 % of errors in news).

---

## History: measurement of 21 August 2026, commit `dcb6903`

## What it is, in one paragraph

A layer that checks a language model's answer for fabrication — and does it
**with arithmetic in Python, not with another model's opinion**.

That difference is the whole product. The usual defence against hallucinations is
a second model grading the first in prose. It inherits exactly the error it is
meant to catch: a confident-sounding classifier is wrong as confidently as what it
grades.

HELIX starts from a narrower and harder promise. The model is trusted only to read
and label: "this looks like a claim", "this source is anonymous", "this document
is dated three weeks after the event it describes". **Every consequence of that
labelling** — how far the evidence level drops, whether a human is needed, how a
conflict between two facts is resolved — is computed by named, tested Python
functions.

The system prompt **forbids the model to return any number** except four 0–3
scores on dimensions. It cannot state a confidence score or a verdict. An attempt
to return its own number raises an exception.

## What it catches

Seven fabrication types, each with its own marker:

| Type | What it is |
|---|---|
| Invented source | a reference to a work that does not exist or does not contain what is attributed |
| Stale as current | "currently" on cutoff-date data — especially dangerous for laws, positions, prices |
| Unfounded amplification | "studies show" → "many studies prove" |
| Non-existent expert | "according to specialists" without names |
| Invented consensus | "generally accepted" where the debate is active |
| Coincidence as cause | "led to" between data from different studies |
| Circular AI-to-AI reference | a model's output used as a source for a model's output |

## How it was checkable in August

| What | Number (21 Aug) | Command |
|---|---|---|
| States named by the specs / code cannot return | 922 / 0 (949 / 0 since October) | `python3 -m helix_pipeline.engine.helix_contract_audit` |
| Executable core patches with behavioural tests | 38 / 38 | `gi_coverage_validator` |
| HELIX tests | 2 154, zero failures | `python3 -m pytest helix_pipeline/tests -q` |
| Engine modules | 78 | `ls helix_pipeline/engine/*.py \| grep -v __init__ \| wc -l` |
| Specification lines the code is checked against | 51 348 | `cat helix_pipeline/docs/specs/*.md \| wc -l` |

**There are TWO checks, and one is not enough.** The coverage validator answers
"symbol declared, a test calls it". It honestly said "99 of 99" on the sibling
product while the code could not return 127 of 583 states for any input.
Implemented by symbol ≠ complete by contract.

## Four vectors and the order between them

`INTELLIGENCE → TRACE → GOVERNANCE → MARKET`. The order is topological, not a
matter of taste: TRACE has nothing to compute until INTELLIGENCE has collected
sources; GOVERNANCE checks a finished answer.

| Vector | State |
|---|---|
| **INTELLIGENCE** — investigation with live search | closed, all 33 protocols checked line by line |
| **TRACE** — risk index, matrix of competing hypotheses | closed, three protocols built from scratch during the audit |
| **GOVERNANCE** — audit of model output, seven fabrication types | closed, verdict visible on the site since 20 Aug |
| **MARKET** | built later as a text panel; the full vector awaits the author's decision |

The core under all four is GI v6.2, about 68 protocols.

## GOVERNANCE — what is built in and how it works

**Why.** A company that puts a chatbot in front of customers is liable for its
words. Precedent — Moffatt v. Air Canada (2024): the bot invented a discount and
the court made the airline pay it. The EU AI Act (Art. 9) requires high-risk
systems to manage risk. GOVERNANCE checks the model's answer **before the customer
sees it**.

**How the check runs** (spec §8, nine steps):

| Step | What is done | Where in the code |
|---|---|---|
| 0 | Regulatory mode: is it high-risk, does a customer see the answer | `governance_service.py` |
| 1 | Each claim into one of 4 zones: stable knowledge, specialist, fresh data, source references | `additive_confidence_score.py` |
| 2–3 | Seven fabrication types and "AI cites AI" recursion (FA-02) | `governance_classifier.py`, `fa02_recursive_hallucination.py` |
| 3.5 | APORIA — "too smooth": not a single caveat, all facts agree | `aporia.py` |
| 4 | Audit of every named source: does it exist, does it match | `ai_output_pde.py` |
| 5 | Emotional/political heat (NGI 0–12), narrative injection in the request (ANI), moral panic (MPF), environment (CHF) | `ngi.py`, `ani.py`, `mpf.py`, `chf.py` |
| 6 | AI-agent behaviour; locks GL-01..14 (no self-verification, immunity to user pressure, etc.) | `phase9_runtime.py`, `gl_locks.py` |
| 7 | Reliability score 0–100 | `additive_confidence_score.py` |
| 8 | Is a human needed: 8 reasons for a full stop, 12 for auto-action with a record | `governance_hitl.py` |

**The reliability score is addition, not a model's opinion.** Start at 30 (AI
output is unproven by default). Zone: references −10, stable knowledge +20. Each
independently verified fact +10 (up to +50). Penalties: invented source −15 each,
stale −5, "coincidence as cause" −5, circular reference −20, recursion −30;
deliberate disinformation (H-TYPE-8) −40. APORIA −5/−10/−15. Result: 81+ usable,
41–60 check, 0–20 stop and a human. Every one of these numbers in the code matched
the spec.

**The model does not compute.** Its prompt (spec §16, verbatim in
`governance_classifier.py`) allows returning only labels, quotes and four 0–3
scores. The current date is passed into the prompt — otherwise the model takes
its cutoff date for "today" and declares already-happened events fabricated (this
happened, see below).

## Update of 7 October 2026: three vectors on the site

| Vector | 6 October | 7 October |
|---|---|---|
| **INTELLIGENCE** (fact gathering) | search rounds and a number gate | + §3 protocols from text labelling: source anonymity, source freshness relative to the event (SAP-4), external claim check (SAP-6), document provenance (PDE), Popper test (SSD), heat (NGI), "too smooth" (APORIA), version divergence (EFR), chronology (TIE); plus the §4–§9 report procedure |
| **TRACE** (planted-document check) | always skipped | **always runs**: 14 of 36 protocols without a human — "who benefits" (ICoI), Popper, heat, planted version (ANI), source silence (SAD), authority pressure (SDF), corporate schemes (FA), source monopoly (FA-11), environment (CHF), APORIA, moral panic (MPF), bridges M3/M6, matrix of competing hypotheses. The manipulation risk index uses the HMP/RDI questionnaire a human fills in |
| **GOVERNANCE** (answer check) | seven types, heat, EU law | + full layer: claim zones (§2), "too smooth", moral panic, planted version, irrefutability stamps, check of every named source (PDE), **reliability score 0–100 (§5)** and **full "human required" list (§6)** |

The model only labels text everywhere; existing Python functions compute. What is
absent from the text is marked "not run" with a reason; investigation state known
only to a human is not filled in by the machine.

**The "what a human must check" rule — the owner's decision.** A claim counts as
**verified** if it is supported by (1) a **primary source** — the own publication
of whoever made the statement or holds the document, actually found by the
search; or (2) **two or more independent sources** — different sites, all actually
found. Only the remaining claims go to a human, as a list with a percentage.

**Live runs of 7 October:**

| Topic | Sources | Verified by the system | To a human | Decision |
|---|---|---|---|---|
| "The Great Wall of China is visible from space" | 18 | **10** (7 primary NASA/ESA, 3 two-independent) | **6 (38 %)** — mostly the author's caveats and conclusions | **pass**, list recommended to a human |
| News of Microsoft/Meta cutting Claude spending | 22 | 0 | all | **human required** — honestly: everything traces back to one paywalled article in The Information; TRACE showed "source independence = 0" |

**Found and fixed along the way (each by a live run):**
1. Labellers cut off mid-word — hidden reasoning tokens count against the length
   cap. Caps raised.
2. The checker declared pages fabricated that the search had found a minute
   earlier: it checked against its own memory. Now it receives the list of found
   sources — zero false fabrications.
3. Fabrication types had been labelled from the wrong spec section since August
   (§3 instead of §13). Fixed.
4. Support for a claim was searched only next to it; now the labeller names every
   source in the text that supports the same thing.

## For corporations and audit firms (marketing section, 6–7 October)

*Historical: at that time the model provider was Azure OpenAI; today it is
Gemini. Promises are split into "works on the site now" and "built in code".*

**Whose pain it is:** a company that put AI in front of customers (every word of
the bot is the company's word); the EU AI Act (risk management, documented
decisions, human oversight); an audit or consulting firm that must prove the
figures and references in an AI-assisted report are not invented; compliance,
legal, analysts and PR receiving AI summaries that feed management decisions.

**Why HELIX and not "another model checking a model":**
1. The model does not judge the model; a program decides by an open formula.
2. Every number decomposes: each score, index and threshold has a formula and a
   line of written spec.
3. The model is forbidden to invent numbers.
4. Seven fabrication types with a quote for each finding (spec §13), plus the §3
   signs.
5. A figure without a source does not pass: between research rounds a gate cuts
   the sentence, lists it and tasks the next round with finding a source.
6. A skip is called a skip: "not run" with a reason, never "clean".
7. Independence of sources, not their count: five sites retelling one article are
   one source.
8. The current date is passed to the model.
9. EU AI Act mapping in every report.
10. A decision log (OAS); at the time it lived in memory for the request — the
    downloaded report served as the trail.
11. The report as a Word (.docx) or Markdown file.

**Live example, 6 October 2026** — a news piece on Microsoft and Meta cutting
internal Claude spending (primary source a paywalled article in The Information):
25 sources found including Reuters, an Nvidia press release and Microsoft Foundry
documentation; Yahoo, Benzinga, PYMNTS, EconoTimes and even Reuters flagged as
retelling one article; a per-claim table ("cut by a third" — partly true, a
spending forecast not a budget; "exactly 10×" — partly true, heavily distorted;
"fall only because of Meta's own tool" — fabrication; "Nvidia and Palantir
officially confirmed because of price" — unconfirmed; "stopped selling Claude via
Azure" — false). The morning's first run had defects (fragments, a false block, an
unanswered question); they were found, fixed and covered by tests the same day.

**Honest limits a customer must know before buying:** no independent external
audit; accuracy on labelled external data was not measured at the time (it has
been since — see the 23–25 October sections); no external customers; no load
certification. Offer to first customers: a free pilot on their own examples in
exchange for "right / wrong" labels.

---

## Honest history, failures included

**Invented thresholds found and removed.** An archived `governance_math.py` held
four `CONFIDENCE_THRESHOLDS` bands (HIGH ≥ 0.90 and so on). Checked against the
spec: **these thresholds appear nowhere in its text**. Removed and kept removed.
Bringing them back would break the system's own rule: a number only by a formula
with visible inputs, never inserted.

**"All on trust" — found by the author in his own work.** Part of the claimed
coverage rested on trusting docstrings and earlier manifest status rather than
line-by-line reading. 36 previously unopened files were read in full and
re-checked. No new discrepancies — the manifest was honest — but the fact that the
check was needed is recorded without smoothing.

**The classifier declared real events fabricated.** A live production run:
GOVERNANCE returned CRITICAL "temporal hallucination — inventing court decisions
that do not exist" on events that had already happened. Cause in the code: the
current date was not passed, and the model used its training cutoff as "now".
Fixed: one false CRITICAL and a BLOCK verdict became zero and PASS.

**The verdict drifted between identical requests.** The maths is deterministic,
but the event it rests on drifted: the classifier temperature was not set at all.
A shared constant 0.0 was introduced. Honest caveat: this does not make the model
fully deterministic, but removes the part of non-determinism we control.

**Contract debt: 179 states the code could not return.** Found on 20 August by
the second kind of audit when the first already showed 100 %. Closed to zero.

**The Custom Connector door did not answer for eleven days.** The MCP server was
mounted and silent: 404 at the documented address. Three independent causes, all
found and fixed on 20 August.

---

## What HELIX does NOT do

- **It does not guarantee a correct verdict on a new topic.** The contract audit
  proves a state exists in the code and can be returned. It does not prove it is
  returned under the right conditions.
- It does not replace a human where the spec requires one.
- It is not certified under load.
- It has no independent verification: all evidence comes from one person's
  repository. **The product's own audit names this its main structural weakness**,
  not something conceded under pressure.

**HELIX is not Mr. Helix.** Mr. Helix is built on top of this architecture but is
a separate engine with its own organs.

# Mr. Helix — investigation in non-fiction

> **About this English edition.** Translated from the Russian product passport on
> 30 October 2026. The body is the edition of 21 August 2026; every figure
> carries the date it was measured. File paths refer to our private repository.
> Since August Mr. Helix gained a voice interface, "deeds versus words", an
> essay-reflection mode, forecasts on the ICD 203 scale with Brier scoring,
> GJR-GARCH volatility statistics and a MARKET vector for news with Heuer's ACH.
> Current measured figures are in [`../OFFER.md`](../OFFER.md).

## Numbers as of 27 October 2026

| What | Number | Command |
|---|---|---|
| capsules / incomplete | 99 / 0 | `python3 -m mr_helix.engine.capsule_contract_audit` |
| states / code cannot return | 583 / 0 (re-measured 30 Oct: unchanged) | same |
| capsules with a return contract | 98 / 99 — capsule 00.13 "OAS log" writes a log entry and has no verdicts | same |
| capsules with behavioural tests | 99 / 99 | `python3 -m mr_helix.engine.capsule_coverage_validator` |
| capsules reachable from live entry points | 99 / 99 | `python3 -m mr_helix.engine.live_path_audit` |

Static reachability is not a filled input: on a sample full analysis 91 capsules
ran, 8 had no input and say why (e.g. "the party's silence is not in the
analysis"), 0 were "not about news".

## Update of 10–11 October 2026: voice, deeds, forecasts, statistics, money

| What | How it works now | Why |
|---|---|---|
| **Voice** | the Mr. Helix persona (prompt v5.0) comes first in every round and in the synthesis; the HELIX service instruction no longer overrides it | the owner: "dry, as if the HELIX system worked, not Mr. Helix" — the cause was found in code |
| **Deeds, not words** | every conclusion separates "declared" from "visible in deeds": deliveries, prices, licences, ships, decisions, money. A declaration without a deed is flagged | the owner: "more in words than in deeds" |
| **Source rules** | reprints (MSN, Yahoo, aggregators, Reuters/AP retellings) are one source; an anonymous source is capped at ECT-3; "breaking" and the first 24 h are less reliable; a screenshot or post without the original is quarantined until the original is found | research reports commissioned by the author |
| **Who benefits — Heuer's ACH** | three hypotheses: H1 intent, H2 information asymmetry, H-NULL "benefit only after the fact". The hypothesis with the fewest contradictions wins. No traces of preparation before the event — "intent not proven" | |
| **Organ loop** | after the draft the Mr. Helix organs check the text; findings go back to the model for correction; a correction that made things worse is rejected | the spec was built in, but organ findings went nowhere |
| **No self-blocking** | everything that used to be a refusal became a list of reasons; the owner publishes with "Publish under my responsibility", the reasons stay in the issue | |

**Forecasts and a track record.** Every analysis ends with "What happens next":
2–3 scenarios, each with a word on the US intelligence **ICD 203** scale and a
number (almost no chance 1–5 % … almost certain 95–99 %), a signal, a check date
and a "came true if" criterion. Code extracts the forecasts and stores them;
blind closing, Brier score and Brier Skill Score against the base rate;
calibration bins only from 30 closed forecasts. **No accuracy figure is claimed
until forecasts close.**

**Market volatility statistics.** For market news (oil, diesel, gas, gold,
indices, large companies) Mr. Helix downloads two years of daily prices and
computes GJR-GARCH(1,1) volatility, a Cornish-Fisher significance threshold
("the news moved the market" or "within noise"), a 21-trading-day corridor, shock
half-life and a fear index (OVX / VIX); futures roll days are excluded. **Not
financial advice.**

**MARKET for news.** Participants and money flows, verbatim quotes (code checks
they exist in the sources, links only from those found), a market risk index,
ACH with the winning hypothesis, traces of positions **before** the event,
retransmitters not counted as independent, and an **answer depth 0–100** with the
gaps named. Not a trading signal.

**Live runs.** Diesel, 10 Oct: from a dry text with 17 sources to voice and
deeds. Trump, Zelensky and refineries, 11 Oct: MARKET depth 92/100; diesel move
"within noise"; 16 claims, 8 confirmed, 27 sources, analysis strength 70/100,
reader card **"Exaggerated"**; 16 model calls, 25 searches, **€1.36**.

**What is still missing:** a blind comparison against a plain model; closed
forecasts (so no accuracy number yet); a source reliability index (needs history).

## What it really does — checked against code 8–9 Oct, re-checked 27 Oct 2026

**Works on the site:**
- Analysis of any pasted text by nineteen organs in one call, without a model
  and free: ghost experts, invented consensus, "may" turning into "proven",
  a source without an address, AI citing AI, a forecast presented as an event,
  claims glued into one, urgency language, virality and "everyone already knows",
  "us versus them", citation laundering. Every AI conclusion gets the lowest
  evidence level (AI-ECT-1) until an external source confirms it.
- In every investigation the organs check the system's own report before
  publication: the language of war and the enemy, "beneficial therefore false"
  and "beautiful therefore true", a reference without verifiable origin.
- Word-level analysis of up to 4 source articles of a news item; every quote is
  checked by code for verbatim presence.

**Called from the site, but may have no input on live news** (their values come
from a labeller or a human): "who benefits" by interest type; source
independence ("seven outlets retelling one wire = one source"); source
authenticity and retelling depth; memetic warfare; six information-attack
tactics with a prescribed defence each (version flooding, term capture,
pre-bunking against future evidence, Gish gallop, creeping normalisation, the
liar's dividend); synthetic persuasion in five forms; the compound-risk rule
(three or more pressure sources at once require a human); the "beauty replaces
evidence" detector (0–4 against the evidence level).

**Honest boundary.** Pressure on the newsroom (HMP, RDI), media forensics and
interests named in no source are not filled in by the machine: a human assesses
them, or they are marked "not assessed".

---

## History: edition of 21 August 2026

**Measured: 21 August 2026, commit `dcb6903`.** Every number was produced by a
command on that day; the command is given next to it.

```
Status: architecture accepted · no production certification
```

The second line is not a lawyer's caveat but an honest status. What exactly is
not certified and why is in "What is missing".

---

## What it is, in one paragraph

An agent that **investigates** rather than retells. Given a question, it looks
for sources, weighs their independence, tests competing explanations and answers
with an indication of how well each statement is supported. It does not please
and does not smooth over: if there is no support, it says so.

The key difference from "smart search": every conclusion has an **evidence
level**, and it is computed by rules, not by how convincing it feels. Fine
writing does not raise the evidence level — this rule is built in and checked by
a test.

## Three vectors of reasoning

| Vector | The question it asks |
|---|---|
| **TRACE** | who wins if this is true? are there traces of a document created to be found? |
| **INTELLIGENCE** | is this confirmed — or does it only sound convincing? |
| **GOVERNANCE** | is this a fact or a convincing fabrication? |

---

## How it can be checked

| What | Number | Command |
|---|---|---|
| Capsules: total / incomplete | **99 / 0** | `python3 -m mr_helix.engine.capsule_contract_audit` |
| States named by the specs / code cannot return | **583 / 0** | same (re-measured 30 Oct 2026: unchanged) |
| Capsules with behavioural tests | **99 / 99** | `python3 -m mr_helix.engine.capsule_coverage_validator` |
| Engine modules | **29** | `ls mr_helix/engine/*.py \| grep -v __init__ \| wc -l` |
| Test files | **38** | `ls mr_helix/tests/*.py \| wc -l` |
| Site routes | **11** of 189 | `python3 -c "from api.main import app; print(len(app.openapi()['paths']))"` |
| Specification lines | **31 453** | `cat mr_helix/docs/spec/*.md mr_helix/docs/core/*.md \| wc -l` |

Mr. Helix tests are part of the root run (**4 360 passed, zero failures** on that
date) and are not counted separately.

> **The rule of this passport, set by the author and applied to the passport
> itself:** do not trust a number in a document — run it. At least twice a
> written number disagreed with the real count. An earlier edition said "571
> tests" and "112+ capsules"; that day's measurement gave 99 capsules and a
> shared run of 4 360.

---

## How it is built: six packs

| Pack | What it does |
|---|---|
| **PACK 00** Integration Nervous System | ties everything together: signal translation, prohibitions, arbitration |
| **PACK 01** Root Epistemic Organs | root epistemics: evidence levels, the null hypothesis |
| **PACK 02** Environment / CHF | modern environmental failures: attention collapse, memetic warfare, synthetic persuasion |
| **PACK 03** Voice / Soul / Literary Intelligence | voice: a continuation of AK-MASTER's literary discipline |
| **PACK 04** Vector Orchestration | the order of the three vectors and conflict resolution |
| **PACK 05** Failure Recovery / Red Team | what to do when something breaks |

### The stabilisation layer — why it is needed at all

The ecosystem has two engines, and **they read the same signal in opposite
ways**. Narrative gravity is, for the literary engine, a tool to amplify; for
the investigator, a threat to suppress. Each is right in its own logic.

The stabilisation layer does not say what something is. It says **what something
can NOT become**:

- **TLX** — signal translation between the engines, 59 rules;
- **Prohibitions F01..F09** — paths that must never exist. For example: the
  emotional core does not assign an evidence level; the investigator does not
  control syntax; the investigator does not assign an archetype;
- **CPX T1..T5** — a pre-written verdict for a disagreement. Not arbitration:
  "an ECT-4 fact is not changed, lowered or softened for narrative convenience.
  Never."

Checked by a command: 9 prohibitions, 59 TLX rules, 135 cross-links, 32
failure-atlas entries.

---

## The rule that may not be broken

```
The literary engine may enter Mr. Helix only as a compressed core.
Never whole.
```

This is the author's rule, not a caveat: the thirteen laws of the core are
allowed, the full tables and the archive are forbidden entirely. **The literary
force of a text never overrides the epistemic check.**

---

## Honest history, failures included

**A branch officially shelved.** An early path was built without specifications;
an independent check found 88 tests out of the 91 claimed. The branch was shelved
and a rule introduced: **every module must have a specification BEFORE the code is
accepted**. Everything built since was built under that rule.

**The operator registry was inflated.** The spec named 49 mathematical operators;
44 were actually built. Corrected from the real data, not adjusted in the
document.

**Contract debt: 127 of 583 states the code could not return** — while the first
kind of check showed "99 of 99". Found on 20 August by the owner's question "what
did you compare it with". Closed to zero.

**Completeness was counted from the wrong source.** There are five requirement
maps and six specs — PACK_00 has no map at all, and a report built from the maps
silently lost fifteen capsules of a whole pack. A test now guards this.

**A test lost six times.** `test_spec_scenario_b_manifest_theater_matches_case2`
disappeared in independent branch merges at least six times. If the file again
shows 14 tests instead of 16, it is the same bug, not a new one.

**Four of nine prohibitions did not act.** The gate held five of the nine
canonical prohibitions; on F01, F02, F03 and F05 it answered "link unknown", that
is, **did not block**. And these were not a random four: three of them guard
exactly the boundary where the investigator intrudes on the literary engine's
decisions. Completed.

---

## What is missing

- **A live Red Team run against a real model.** All documents honestly call what
  was done an "in-session simulation": 18 cases × 3 variants = 54 of 54 PASS, but
  a simulation. **That is the reason for the wording "no production
  certification".**
- **External users.** Zero outside investigators to date.
- **Independent verification.** All the evidence comes from one person's
  repository — named the main structural weakness by the product's own audit.
- `micro_adapter.py` relies on a specification that is not in the repository. Not
  silently rewritten: the author decides whether to update it or keep it as a
  separate lightweight artefact.

---

## Where to look next (private repository)

| Question | File |
|---|---|
| What to load into the model as the system prompt | `mr_helix/docs/core/MR_HELIX_v5_FINAL_SYSTEM_PROMPT_v5_0.md` |
| Entry point to all specs | `mr_helix/docs/core/MR_HELIX_v5_READ_ME_FIRST_MINIMAL_HANDOFF_v0_1.md` |
| How the contract debt was closed | `mr_helix/docs/MR_HELIX_CAPSULE_CLOSURE_REPORT.md` |
| The stabilisation layer in detail | `mr_helix/docs/STABILIZATION_LAYER_ANALYSIS.md` |

**Mr. Helix is not HELIX.** It is built on top of the HELIX architecture, but it
is a separate engine with its own organs and its own task: HELIX audits a model's
output, Mr. Helix conducts an investigation.

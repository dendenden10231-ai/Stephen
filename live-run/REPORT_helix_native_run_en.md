# HELIX native run on the headline thesis of "No second refinery"

Run date: 30 October 2026 · investigation id `e045d986-544` · product: https://helixcom.org (HELIX tab)
Original machine-generated report, unedited (Russian): [`helix-report-original-ru.md`](helix-report-original-ru.md)

This is **file 1 of 2**. It shows what HELIX does **on its own**: it searches, reads, judges and writes, with no evidence supplied by us.
File 2 is the run of **your null-arm probe design** on the same topic: [`../judge-probe-on-this-topic/`](../judge-probe-on-this-topic/README.md).
How the two differ and what each can and cannot show: [`../COMPARISON.md`](../COMPARISON.md).

## 1. What was submitted

Your article's headline thesis, as one sentence, typed into the product's "What to check" box:

> Diesel broke its all-time record price in September 2026 (US national average above $5.85 a gallon, then above $6.05) while crude oil was about $28 a barrel cheaper than at the June 2022 record, so the crisis is at the refineries (lost refining capacity), not at the wellhead.

Settings: default. Search depth 3 rounds, no HMP/RDI bands chosen, no publication deadline, no document attached.
We submitted **only the headline thesis**, not your five vectors (Jazan, Gulf war, Russia, the calendar, TMX) and not the 23-claim audit. Those were not tested here.

Run cost (the product's own spend counter, an estimate from tokens × list price, not a bill): 34 model calls, about **$2.42**, `gemini-3.1-pro-preview`, about 17 minutes.

## 2. What HELIX returned, in one table

| Part of the thesis | HELIX finding | Level it gave itself |
|---|---|---|
| Diesel at an all-time record in September 2026 | Confirmed. Retail diesel reached $6.53/gal in the week of 21 September. | ECT-4 |
| "Above $6.05" on 11 September specifically | **NON LIQUET.** That figure appears only in AAA trackers, not in the official EIA tables it could read. | not established |
| Crude "about $28 cheaper" than June 2022 | **Not reproduced on the benchmark HELIX used.** EIA: WTI averaged $97.31 in September 2026 against a $122.11 peak on 8 June 2022, a gap of about **$24.8**. | ECT-4 for the $24.8; $28 is NON LIQUET |
| Refining capacity was lost | Partly. It found US closures (LyondellBasell, Phillips 66, Valero, 540 kb/d over 2025–26), reported via trade press, not an EIA table. | ECT-3 |
| So the crisis is "at the refinery" | **Not established in this run, and not the leading hypothesis.** The best-scoring hypothesis (H3) was an **export-driven stock draw**: distillate exports up to a record 1.7 mb/d (norm 1.3) drew inventories down about 29 mb while the remaining refineries ran at 96.8–98%. The pure-capacity hypothesis (H1) was listed as "not found in this run". | confidence in the ranking: low |

The ranking is stated by the product as low-confidence: dropping one piece of evidence from one independent source would change the leader.

## 3. Where our run and your article meet

We set these down as things we learned from your work, and as questions we would be glad to hear your view on. You have spent four decades in this field; we have spent two years building a tool, so we hold our reading loosely.

1. **The $28 gap.** Your sourcing note held this figure back as `[AS GIVEN]`, an analysis-site computation against a Brent range. That caution was well placed: HELIX, comparing a **WTI monthly average with the WTI single-day peak**, arrived at about $24.8. The two numbers use different benchmarks and different windows, so they may simply be answering different questions. We would value your view on which window is the right one for the claim.
2. **"Capacity" and "exports" may be two ends of one chain.** HELIX's best-scoring hypothesis says exports drained US stocks. Your article names a possible ban on roughly 3 mb/d of US refined-product exports as a live policy question. One reading, which we have not verified: a surge in US distillate exports could be the **channel** through which the foreign refinery losses in your five vectors reach the US pump. If so, the two accounts would fit together. HELIX tested neither the foreign losses nor that link. It tested only the headline sentence, and mostly on US-domestic evidence. Your five vectors deserve a run of their own.
3. **Scope.** HELIX's 1.7 mb/d is distillate exports. Your 3 mb/d is all refined products, so the two figures count different things.

## 4. What HELIX said about its own answer

- Verdict: **HITL_REQUIRED**, decided by GOVERNANCE. It advises, it does not delete: the answer is shown with the grounds.
- Grounds: a `TYPE-8 ADVERSARIAL_DEPLOYMENT (HIGH)` flag on **its own generated narrative**, for manipulative metaphors and a "they are robbing you" framing ("artificial vacuum"). This is a flag on HELIX's text, not on your article.
- One sentence was withdrawn by the pre-output gate (claims with no source in that round) and is listed, not passed on.
- Independently confirmed claims: **0**. Items passed to a human: **5 of 5**.
- Answer risk index (CIRI) 46; narrative gravity (NGI) 11, CRITICAL; confidence 0.6 against a 0.30 human-review threshold; credibility score §5: 0/100 (CRITICAL).
- Risk Index: `NOT_RUN`. It needs two bands (HMP, RDI) that a person chooses, and the product refuses to invent them. TRACE ran 15 of 36 protocols.
- A falsifier it wrote for its own leading hypothesis: crack spread holding above $90 in October–November with free exports.

## 5. Where our own tool fell short

This section is about HELIX, not about your article.

- 159 links from 103 sites. Of 73 pages it tried to read, **56 were read; 14 returned HTTP 403 and 3 were empty.**
- Sources the product itself classed as primary: `eia.gov`, `sec.gov`. It also reached `aaa.com` and `stlouisfed.org`, classed as reference. Most of the rest are secondary or aggregator sites.
- **Not among its sources:** Reuters, S&P Global, RBN Energy, IEA, Bloomberg. We found Reuters, S&P Global and RBN by hand, with a separate search, after the run. HELIX did not surface them.
- One retrieved figure looks wrong and is flagged by HELIX itself for a human: it cites EIA at $3.967 for 7 September, which is far from every other diesel figure in the run. We did not chase it; it may be a different series.
- Single run. The pipeline is not deterministic. We did not repeat it.

## 6. Our own spot-checks, outside the HELIX run

Done by hand, with pages we opened ourselves, to see how your sourcing holds up. In each case we are reporting what we found, and the sourcing you chose looks careful:

| Your figure | What we found |
|---|---|
| East Coast distillate stocks 19.3 mb, week ending 28 Aug | EIA weekly table: 19,318 kb. Matches. |
| Russian gasoline output "about 70% of demand" | Reuters, 28 Aug: about 80,000 t/d against 115,000 t/d, i.e. 70%, at the end of August. The same report gives an August average of about 80% and supply with imports of about 85%. So "70%" is a late-August low, not an average. |
| Diesel crack record $112.17/bbl | RBN Energy: a new record of $107.72 on 10 September; a market-data site shows weekly values of $114.5–115.8 later in September. Different measures and dates, so the "record" depends on the series. |
| Haifa "no significant impact" versus later documents | S&P Global, 20 March: Bazan confirmed a strike on infrastructure "essential to its operations" and that most production units were still operating. |

## 7. What this file is not

It is **not** your null-arm probe. There are no arms A–G here, and the evidence was not controlled. It shows the product's end-to-end behaviour on a topic you analysed. The controlled test of whether the judge **reads** its evidence is file 2.

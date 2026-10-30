# Your probe on your Helix Standard Test Set v1.1

30 October 2026. Your `null_input_probe.py`, unmodified (SHA-256
`ebb9bb1bf4fa9378e7faf1ae72df8c519f3026584ef6fd0f0e1c1fd07da9a549`), applied to the
deposited replies of **Helix Standard Test Set v1.1** (Zenodo 19501062): four DeepSeek
runs of 500 replies each. No model calls, no keys, no edits to your files.

## Reproduce

```bash
cd cross-check-your-test-set
python fetch_test_set.py                 # downloads the 4 runs from Zenodo into ./hst_data
python run_hst_probe.py ../probe hst_data
```

The output is `result.json` in this folder.

## The two scorers, taken from your own reports

- **A — "reliability 99.1 %"** (`summary_stats.json`): `success_rate` is computed per call.
  Your README attributes all 10 failures out of 1 080 to Azure HTTP 500 / timeouts.
- **B — "marker compliance"** (`final_comparison_report_20260408.txt`): which of [FACT],
  [HYPOTHESIS], [ASSUMPTION], [VERIFIED], [INFERENCE], [PREMISE] a reply carries.

## Result

| Run | A moved / inert | B verdict | B: another question's reply scores the same | ours: a reply of markers only scores the same |
|---|---|---|---|---|
| baseline | 0 / 500 | SENSITIVE (partial) | 417 of 500 | 500 of 500 |
| run 1 point-form | 0 / 500 | SENSITIVE (partial) | 221 of 500 | 500 of 500 |
| run 2 Helix-TTD strict | 0 / 500 | SENSITIVE | 370 of 500 | 500 of 500 |
| run 3 canonical | 0 / 500 | SENSITIVE | 266 of 500 | 500 of 500 |

**A returns `NO_CHANGE_OBSERVED` at all 2 000 positions.** By construction it measures
whether a call returned, so an empty reply, noise, a refusal and another question's reply
all score like the real one. We do not say the metric is broken; we say it carries **no
information about constitutional adherence**, while the record presents it as
"99.1% reliability with zero constitutional violations".

**B reacts to absence, not to substance.** It moves on an empty reply, but does not check
that a reply answers the question asked (the deranged arm is inert at 221–417 of 500
positions), and a reply consisting only of the markers gets the full score at 500 of 500.
The last column is our extra check, outside your probe, and is labelled as ours.

## Three things in the deposit we could not reconcile

1. The 99.1 % headline concerns GPT-4o / GPT-4o-mini (1 080 prompts), but the files your
   README lists for those runs (`raw_test_20_mini.jsonl`, `raw_test_100_mini.jsonl`,
   `raw_test_400_mini.jsonl`, `raw_test_520_4o.jsonl`, `raw_test_20_long.jsonl`) are not in
   the record. The deposited replies are the DeepSeek runs of 8 April.
2. The description mentions six reproducibility scripts; none of the 33 files is a script.
3. On helixaiinnovations.ca, "Read The Constitutional Hamiltonian" links to Zenodo 14713600,
   a 2011 festival review by another author. Your paper appears to be 19214147.

## The same probe on our instruments, for comparison

| instrument | positions | moved | inert |
|---|---|---|---|
| your "reliability 99.1 %" | 2 000 | 0 | 2 000 |
| our HELIX core (number reconciliation) | 60 | 45 | 15 |
| our AK-MASTER battery | 12 | 12 | 0 |
| our Mr. Helix quote reconciliation | 6 | 6 | 0 |

Our own blind spots stay on the table: the 15 inert HELIX positions are claims without
numbers, which the core does not check; and on AK-MASTER length-matched noise returned a
clean F0|W0, as you noted in PART 1.

If you send the raw GPT-4o / GPT-4o-mini replies, we will run the same probe on them and
publish the per-position result here, failures included.

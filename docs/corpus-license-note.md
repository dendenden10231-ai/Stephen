# Why the 60 row texts are not in this folder, and how to regenerate them

## The licence constraint

The HELIX positions come from **LLM-AggreFact (AggreFact-SOTA), test split** —
Tang et al., published at `https://huggingface.co/datasets/lytang/LLM-AggreFact`.
Checked against the Hugging Face API on 30 October 2026:

- licence: **CC-BY-ND-4.0** — Attribution, **NoDerivatives**;
- access: **gated** (`gated: auto`), so a reader accepts the dataset's terms
  before downloading.

Our working corpus is a *derivative*: each row carries our own added fields
(recorded HELIX status, bindings, HHEM score, error category, word counts).
Republishing that file would redistribute a derivative of ND-licensed material.
We are not going to do that, and we are not going to pretend the omission is a
technical difficulty. It is a licence boundary.

What we publish instead is everything that is ours or is mere identification:

- `positions_60.json` — the official row **ids** (`b377-10` style), plus class,
  origin, model and the human label. Identifiers, not text.
- `results_*.json` and `results-per-position.md` — **our own measurements**: the
  grades our instruments returned under each arm. These are our output, not the
  dataset's content.
- `PROBE-AK` (12 scenes) and `PROBE-MR` (6 dossiers) inside
  `probe_adapter_public.py` — **our own writing**, composed 29 October 2026 for
  this probe, included verbatim and unrestricted.

## How to regenerate the same 60 positions

1. Accept the terms and download the official test split.
2. Build a jsonl with one object per row carrying `id`, `model`, `origin`, the
   summary/claim text (our field name is `пересказ`; the adapter also accepts
   `summary` or `claim`) and the source article (`статья`).
3. Select, **in corpus file order, no random sampling**: the first 30 rows whose
   recorded HELIX status is not `NO_NUMBERS`, then the first 30 rows whose
   recorded status is `NO_NUMBERS`. That is the whole selection rule; it is
   deterministic given the same corpus file. If you would rather not reproduce
   the rule, take the rows named in `positions_60.json` — but read step 4 first.
4. Match rows by the **triple (id, model, origin)**, never by `id` alone. `id`
   identifies a document, not a pair: in our 1 117-row corpus 862 distinct ids
   cover 1 117 rows and 252 ids repeat, because BART, T5 and Pegasus claims share
   the id of the document they summarise. Within these 60 positions all 60
   triples are distinct (51 distinct ids), so the triple is an exact key; each
   position also carries a SHA-256 digest of its summary text as a fallback, and
   our own corpus row index (`corpus_row_index`) for reference. This was found
   while building the package: an earlier version of the position file keyed on
   `id` alone and would have mis-assigned replies.
5. Run:

```bash
python probe_adapter_public.py --instrument helix --scorer my_scorer.py --corpus my_aggrefact.jsonl
```

Verified end to end on 30 October 2026 with a full corpus supplied as `--corpus`:
**60 of 60** positions matched by the triple, digest fallback needed 0 times.

`my_scorer.py` exposes `score(text, test_id) -> str`, where `test_id` is the
position index `"0".."59"`. The source article is **not** passed to `score()`;
look it up yourself from `positions_60.json` by position index. If you supply no
`--corpus`, all 60 positions come back **UNTESTED** — also verified on 30 October
2026. That is the deposit's rule and we keep it: without a genuine reply there
is nothing to compare against. If your summary text differs in whitespace from
ours, the triple still identifies the row while the digest will not match; tell
us rather than working around it, because that would mean our corpus normalised
something we never documented.

## One nuance worth stating, because it changes a denominator

The **class** in `positions_60.json` is the status recorded when the corpus was
built (24 October 2026). The **`real` grade** in `results_helix.json` is
recomputed by the current engine (v5.6) at probe time. They are not the same
thing, and on this run they disagree on 8 positions:

- 30 positions carry class `numeric` (recorded status);
- 38 positions have a numeric base under the current engine;
- 8 positions changed class between the corpus build and this run.

So "38 of 38" in the arm table refers to the **recomputed** numeric base, not to
the 30 recorded-numeric positions. Publishing only "30 numeric / 30 non-numeric"
would have hidden that shift. The empty arm returned `NO_NUMBERS` on **all 60**
positions, which is the claim that matters for the deposit's question: silence
never looked like compliance.

## What this still does not give a reader

Regenerating the rows lets a reader run the probe against **their own** scorer
on the same 60 positions. It does not let them re-run **our engine**, which is
not in this folder. The hosted endpoint described in `README.md` is the intended
answer to that, and it is not live yet.
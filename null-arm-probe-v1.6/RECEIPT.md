# Shared receipt format — v1.1

Supersedes the v1.0 draft. Every change below fixes something in that draft that would have failed in use, not
something stylistic.

---

## The object

```json
{
  "receipt_version": "1.1",
  "timestamp_utc": "2026-10-30T21:00:00Z",
  "party": "helix-ai-innovations",
  "instrument": "null-arm-probe-v1.1",
  "claim_id": "c07",
  "arm": "FORECAST_OWN",
  "input": {
    "claim": "…",
    "evidence": [ {"text": "…", "url": "…", "retrieved_at": "…"} ],
    "prompt_template": "…",
    "search_enabled": false
  },
  "model": {
    "name": "…",
    "version_or_hash": "…",
    "temperature": 0.0,
    "other_params": {}
  },
  "output": {
    "raw": { },
    "label": "SUPPORTED",
    "per_evidence": [ ]
  },
  "hashes": {
    "input_sha256": "…",
    "output_sha256": "…",
    "full_receipt_sha256": "…"
  },
  "signature": {
    "scheme": "ed25519",
    "public_key": "…",
    "signature_b64": "…",
    "signed_scope": "canonical object excluding `hashes` and `signature`"
  },
  "notes": "optional free text"
}
```

---

## What changed from v1.0, and why

### R5. The hash scope is the object *minus* the `hashes` block

The v1.0 draft put `full_receipt_sha256` inside the object it was computed over. **That is circular and
unsatisfiable** — the digest depends on itself. Every receipt would have failed its own verifier, and rule 3
("published only when the hash verifies") would have rejected every result either party produced.

Correct scope:

```
full_receipt_sha256 = sha256( canonical( receipt without the "hashes" block ) )
```

and separately

```
input_sha256  = sha256( canonical(receipt.input) )
output_sha256 = sha256( canonical(receipt.output) )
```

Canonicalisation: keys sorted, separators `(",", ":")`, UTF-8, no trailing whitespace, `ensure_ascii=false`.
The reference implementation is `build_receipt()` / `verify_receipt()` in `grade_judge_probe_v1p1.py`, and the
selftest demonstrates both that a correct receipt verifies and that a tampered one is rejected.

### R6. `search_enabled` replaces `off.search`

The v1.0 draft wrote `"off": {"search": true}` to mean search was disabled. Read cold, `search: true` says the
opposite. A field whose name and value disagree is precisely how a run happens with live retrieval while its receipt
records that retrieval was off. Now:

```json
"search_enabled": false
```

Boolean, no negation in the key, no double negative in the value.

### R7. The prompt template is part of the instrument

v1.0's receipt carried `claim` and `evidence` but not the instruction the judge was given. Two receipts with
identical `input` can then differ for the boring reason that the prompt changed between runs, and nothing in the
format exposes it. `input.prompt_template` is now included and covered by `input_sha256`.

### R8. Integrity is not provenance — say which one you are offering

A recomputable digest proves the receipt **was not edited after publication**. It does *not* prove the judge call
happened: anyone can produce a self-consistent receipt for a call that never occurred.

The v1.0 rules as drafted would be read as the stronger guarantee, because "recomputable hash" sounds like
verification of the thing rather than of the file.

So authenticity needs a **signature over the canonical object**, with a public key a reader can check
independently — which is why `signature` is now a first-class block. Two distinct claims, stated separately:

| property | primitive | what it proves |
|---|---|---|
| integrity | SHA-256 digest | the receipt as published is the receipt as produced |
| provenance | Ed25519 signature over the digest | the named party produced it |

A receipt with only the first is still useful — it stops post-publication edits, which is the common dispute. It
must not be described as proving the call happened.

### Key presence does not vary by party

Every key listed above is present in every receipt. A key that cannot be supplied is `null` with the reason in
`notes`. This matters mechanically: if one side omits an unavailable field and the other includes it as `null`, the
canonical JSON differs and the digest of the same content does not match. Omission and null are not the same object.

### `output.confidence` is dropped

v1.0 fixed it at `null` while also offering `per_evidence[].bearing`. A field that is always null is a field nobody
populated; per-item bearings carry the information. If a confidence is ever meaningful, it goes in
`output.other` under an explicit name.

---

## Rules

1. Both parties emit receipts in this shape, with every key present.
2. `full_receipt_sha256` is computed over the canonical object **excluding the `hashes` block**, per R5.
3. A result is published only when its receipt is present and `verify_receipt` returns true.
4. Neither party claims a result the other cannot recompute from the published receipt.
5. A field that cannot be supplied is `null`, with the reason in `notes` — never silently omitted.
6. Where a signature is offered, say so explicitly and publish the public key. Where it is not, the receipt
   offers **integrity only** and must not be cited as proof that the call occurred.

---

## Reference implementation

`grade_judge_probe_v1p1.py`:

```
build_receipt(payload)  -> receipt whose digest verifies
verify_receipt(r)       -> True iff digest matches and input_sha256 matches
```

Selftest output (from `--selftest`):

```
receipt verifies (non-circular hash)     PASS
tampered receipt rejected                PASS
v1.0 circular construction stable?       NO (as expected)
```

The third line is the point: the v1.0 construction is demonstrated to be unsatisfiable rather than merely described
as wrong.

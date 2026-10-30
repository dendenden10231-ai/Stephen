# Provenance of the probe files

Both files below are the deposit's own instruments, copied **byte for byte**.
A rewritten probe would not be evidence; these hashes let a reader check that nothing was changed.

| file | SHA-256 | origin |
|---|---|---|
| `null_input_probe.py` | `ebb9bb1bf4fa9378e7faf1ae72df8c519f3026584ef6fd0f0e1c1fd07da9a549` | deposit of 28 Oct 2026, Stephen Hope, "The Gate and the Corridor" (20–21 Oct 2026) |
| `null_model_test.py` | `5a8f3a14313c0edc3357ac652e4826397fc4569e715f166c30954878516301f8` | deposit of 28 Oct 2026, Stephen Hope, "The Gate and the Corridor" (20–21 Oct 2026) |

Deposit received 28 October 2026; vendored into the production tree the same day.
Adapter written by us: `probe_adapter_public.py` in this folder (the production adapter is
`scripts/проба_нулевого_входа_28_10.py` in the private tree; this public copy has the same
corpora and the same seed, with the scorer made injectable so a reader can point it at any instrument).

Run dates: 28 Oct 2026 (HELIX core), 29 Oct 2026 (AK-MASTER battery, Mr. Helix quote check),
30 Oct 2026 (all three re-run for this package; verdicts and counts identical).

## Checking the hashes yourself

Both hashes above were computed on 30 October 2026 against the deposit originals
as received (`Downloads\Новая папка (2)\null_input_probe.py`, `null_model_test.py`)
and against the copies in this folder; the two pairs matched exactly. The
originals use LF line endings.

`.gitattributes` in this folder sets `* -text`, so git performs no line-ending
normalization on checkout: a clone hashes identically on Windows, macOS and
Linux. To check:

```bash
sha256sum null_input_probe.py null_model_test.py
```

If your clone ever produces different hashes, check `core.autocrlf` in your git
configuration before concluding the files were altered.
# Provenance of the probe files

Both files below are the deposit's own instruments, copied **byte for byte** — with one
disclosed exception: two server paths in `null_model_test.py` were removed by us on 31 Oct 2026
(see "What we edited" below). Everything else in both files is his text, unchanged.
A rewritten probe would not be evidence; these hashes let a reader check exactly what changed.

| file | SHA-256 | origin |
|---|---|---|
| `null_input_probe.py` | `ebb9bb1bf4fa9378e7faf1ae72df8c519f3026584ef6fd0f0e1c1fd07da9a549` | deposit of 28 Oct 2026, Stephen Hope, "The Gate and the Corridor" (20–21 Oct 2026) |
| `null_model_test.py` (as received) | `5a8f3a14313c0edc3357ac652e4826397fc4569e715f166c30954878516301f8` | deposit of 28 Oct 2026, Stephen Hope, "The Gate and the Corridor" (20–21 Oct 2026) |
| `null_model_test.py` (as published here) | `180babb85e3c3593b3756a78b169e9a53ffca5e2be7fe771d703bc6b11f34d73` | same file, two absolute server paths replaced by placeholders on 31 Oct 2026 |

Deposit received 28 October 2026; vendored into the production tree the same day.
Adapter written by us: `probe_adapter_public.py` in this folder (the production adapter is
`scripts/проба_нулевого_входа_28_10.py` in the private tree; this public copy has the same
corpora and the same seed, with the scorer made injectable so a reader can point it at any instrument).

Run dates: 28 Oct 2026 (HELIX core), 29 Oct 2026 (AK-MASTER battery, Mr. Helix quote check),
30 Oct 2026 (all three re-run for this package; verdicts and counts identical).

## What we edited, and why

His script carried two absolute paths from his own machine:

```python
sys.path.insert(0, "/home/steve/helix/repos/lattice/ops")        # line 34
pathlib.Path("/home/steve/.config/helix/gate-keys.env")           # line 82
```

No secret value was in the file — it reads the key at run time. But publishing the file published
the account name and the exact location of the key file, so we replaced both strings with inert
placeholders and left the surrounding code as he wrote it. Nothing else in the file was touched;
the diff is two lines. The original hash above still identifies his deposit as received, so anyone
holding the original can prove which copy they are looking at. We will tell him in the next message
rather than let him find an unexplained diff in his own file.

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
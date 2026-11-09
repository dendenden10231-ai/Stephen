# Addendum 2026-11-05: magnitude class recomputed (frozen files untouched)

You listed the magnitude class as open. This file closes the measurement half of it; the frozen
arms file and its digest are **not modified**.

**Defect.** The sensor's quantity classifier picked a class from one token and took the first number
in the text, so "magnitude 4.8 at 199 km" was read as 4800 metres (`spatial_distance`).

**What was recomputed.** The same 56 arms, evidence and claims unchanged, with `comparable_quantity`
re-derived by the corrected classifier. File: `руки_usgs_пересчёт_сенсора.json`.

| | value |
|---|---|
| arms whose `comparable_quantity` changed | 34 of 56 |
| now `seismic_magnitude` (dimensionless) | 22 |
| now no comparable quantity (no number to compare) | 12 |
| were `spatial_distance` | 33 |
| were `mass_stock` | 1 |
| arms whose `sensor_verdict` changed | 0 |
| sensor in scope / agrees with expected label | 33 / 33 (unchanged) |

So the misclassification was in the metadata field only; no verdict moved. 0 model calls, 0 USD.

**Digests.** Frozen arms digest (unchanged): `5708832f72365a07902103583f6cfc091594406fd64c0f4f949751b68300075b`.
Recomputed file declares digest `dc3acd30bb8aa7f61595f7483518fc7a66452a2aa3031272b2c78fdf799434e9`
(same rule as the frozen file: SHA-256 of `json.dumps(d['руки'], ensure_ascii=False, sort_keys=True, indent=2)`, i.e. of the
**`руки` array only**, not of the whole object — hashing the whole object gives `604e0a26…`, which is not the declared digest;
byte-level SHA-256 of the file is in `SHA256SUMS.txt`). Corrected 2026-11-06 after Stephen's re-score; the earlier sentence here was wrong. Anything quoting the field values of the frozen
file as "what the sensor believed the quantity to be" should cite this addendum instead.
Caveat: the corrected classifier is our code; the check you can run is to compare the 34 changed rows by hand.

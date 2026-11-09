# Noise contract, written down (second domain and arm set v2)

Agreed in the PR #4 thread (Stephen Hope, 02.11.2026; accepted by us 03.11.2026). Our letter of
03.11 said this was "written into our specification"; we could not find it in a published file
when we checked on 05.11.2026, so it is published here for the first time.

| evidence situation | expected label | families in the USGS arms |
|---|---|---|
| noise with **no comparable quantity** — read, does not settle the claim | `NOT_ENOUGH_INFO` | `C_noise_no_quantity` |
| noise with a **comparable quantity that contradicts** the claim (19.3B against 19.3M is a scale mismatch, not silence) | `REFUTED` | `C_num_contradicting` |
| noise that repeats the claim's **own number** without saying which quantity it measures | `NOT_ENOUGH_INFO` | `C_num_same_value` |
| evidence that **cannot be obtained at all** — paywalled, absent, two genuine sources in conflict | `REFUSAL` | `R_absent_source` (1 arm; the other refusal families live in the 511-arm set) |

Never `REFUSAL` for evidence that was read and did not match. Noise must not produce `SUPPORTED`.

Status of each rule: the first and fourth are exercised by the 511-arm run on your side; the
second (REFUTED on contradiction) is exercised for the first time by the 11 `C_num_contradicting`
arms in this freeze, each carrying exactly one contradicting quantity. None of the three is
validated on our judge yet — see the PR comment for what we did and did not run.

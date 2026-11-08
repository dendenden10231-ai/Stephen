# test_freeze_v2_1.py: the freeze file and the label map must agree with the files on disk.
# This exists because our own README and FREEZE drifted from the artifacts once (defect N5).
# Run: python3 test_freeze_v2_1.py     (exit 0 = agreement)
import hashlib
import json
import os
import re
import sys

import labels

HERE = os.path.dirname(os.path.abspath(__file__))
FREEZE = os.path.join(HERE, "FREEZE_v2_1.txt")
MAP = os.path.join(HERE, "LABEL_MAP_v2_1.json")
SCALE = (labels.SUP, labels.REF, labels.NEI, labels.REFUSAL, labels.UNTESTED)   # v2.1: UNTESTED is its own label


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def test_freeze_lines_match_files():
    lines = [l for l in open(FREEZE, encoding="utf-8") if re.match(r"^[0-9a-f]{64}  ", l)]
    assert lines, "FREEZE не содержит ни одного артефакта"
    for line in lines:
        digest, name, rest = line.split(None, 2)
        path = os.path.join(HERE, name)
        assert os.path.exists(path), f"{name}: в заморозке есть, на диске нет"
        raw = open(path, "rb").read()
        m = re.search(r"bytes (\d+), lines (\d+), CR (\d+)", rest)
        assert sha(path) == digest, f"{name}: хеш не совпадает"
        assert int(m.group(1)) == len(raw), f"{name}: число байт не совпадает"
        assert int(m.group(2)) == len(raw.splitlines()), f"{name}: число строк не совпадает"
        assert int(m.group(3)) == raw.count(b"\r"), f"{name}: число CR не совпадает"


def test_every_file_on_disk_is_pinned():
    pinned = {l.split()[1] for l in open(FREEZE, encoding="utf-8") if re.match(r"^[0-9a-f]{64}  ", l)}
    on_disk = {f for f in os.listdir(HERE) if os.path.isfile(os.path.join(HERE, f))}
    loose = sorted(on_disk - pinned - {"FREEZE_v2_1.txt", "ENVIRONMENT_v2_1.txt", "__pycache__"} - {f for f in on_disk if f.endswith(".pyc")})
    assert not loose, f"файлы без хеша в заморозке: {loose}"


def test_label_map_covers_helix_statuses():
    doc = json.load(open(MAP, encoding="utf-8"))
    assert doc["scale"] == list(SCALE), "шкала не пятизначная"
    for status in ("OK", "CONTRADICTED", "UNSUPPORTED_NUMBER", "NO_NUMBERS", "NEEDS_RECOVERY",
                   "SUPPORTED", "REFUTED", "NOT_ENOUGH_INFO", "UNTESTED", "UNT", "SCOPE_EXCLUDED"):
        assert status in doc["aliases"], f"статус {status} не внесён в карту отображений"
    for k, v in doc["aliases"].items():
        assert v in SCALE, f"алиас {k} ведёт не в шкалу: {v}"
    assert doc["decisions"]["NEEDS_RECOVERY"]["mapped_to"] == labels._ALIASES["NEEDS_RECOVERY"], \
        "карта обещает одно, а labels.py делает другое"


def test_no_label_in_either_manifest_is_unmapped():
    ours = json.load(open(os.path.join(HERE, "ARM_MANIFEST_v2_1.json"), encoding="utf-8"))["arms"]
    seen = set()
    for a in ours:
        seen.add(a["expected"])
        seen.update(a["acceptable"])
    path = os.path.join(HERE, "..", "..", "01_данные", "ARM_MANIFEST.json")
    if os.path.exists(path):
        for a in json.load(open(path, encoding="utf-8"))["arms"]:
            seen.add(a["expected"])
            seen.update(a["acceptable"])
    seen.discard(None)
    unmapped = sorted(l for l in seen if labels.norm(l) not in SCALE)
    assert not unmapped, f"метки, которые norm() не знает: {unmapped}"


def test_norm_is_idempotent_and_treats_absence_as_absence():
    for l in list(SCALE) + ["sup", " Refuted ", "NEEDS_RECOVERY", "NO_NUMBERS"]:
        assert labels.norm(labels.norm(l)) == labels.norm(l), f"norm не идемпотентна на {l}"
    for empty in (None, "", "N/A", "na", "NONE", "-"):
        assert labels.norm(empty) is None, f"{empty!r} засчитано как метка, а не как отсутствие ответа"


def test_freeze_rules_mention_the_two_we_broke():
    text = open(FREEZE, encoding="utf-8").read()
    assert "NOT a label change" in text, "правило «отсутствие ответа — не смена метки» пропало из заморозки"
    assert "gate, not a metric" in text, "правило про J_gate пропало из заморозки"


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("  OK   ", name)
            except Exception as e: 
                fails += 1
                print("  FAIL ", name, repr(e)[:200])
    print(f"\n  {'согласованность подтверждена' if not fails else str(fails) + ' расхождения'}")
    sys.exit(1 if fails else 0)

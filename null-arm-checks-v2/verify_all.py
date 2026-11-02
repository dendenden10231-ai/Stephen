# verify_all.py: one command that has to be green before anything is shown to anyone. Exit code is the verdict.
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
SUITES = [("test_checks.py", "исходные проверки v1"),
          ("test_v2.py", "инварианты черновика"),
          ("test_freeze.py", "согласованность заморозки и карты отображений")]
FLAGGED = [("scoring_v2.py", "--selftest"), ("scoring_v2.py", "--baselines")]
CJK = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")


def run(args):
    p = subprocess.run([PY, "-X", "utf8"] + args, cwd=HERE, capture_output=True, env=ENV)
    out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
    return p.returncode, out


def freeze_audit():
    """Re-run the generator and require that FREEZE comes out byte-identical."""
    target = os.path.join(HERE, "FREEZE_v2.txt")
    before = open(target, "rb").read()
    rc, out = run(["freeze_v2.py"])
    after = open(target, "rb").read()
    return rc == 0 and before == after, ("заморозка пересоздана идентично" if before == after
                                        else "FREEZE меняется на глазах: файл отредактирован без перезапуска генератора")


def idempotent_rebuild():
    digests = {f: hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest()
               for f in ("arms_v2.json", "ARM_MANIFEST_v2.json")}
    rc, out = run(["build_arms_v2.py"])
    same = all(hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest() == d
               for f, d in digests.items())
    return rc == 0 and same, "генератор даёт те же байты" if same else "генератор не идемпотентен"


def text_hygiene():
    bad = []
    for f in sorted(os.listdir(HERE)):
        if not f.endswith((".py", ".md", ".txt", ".json")):
            continue
        t = open(os.path.join(HERE, f), encoding="utf-8", errors="ignore").read()
        if CJK.search(t):
            bad.append(f)
    return not bad, "иероглифов в русских файлах нет" if not bad else f"иероглифы в: {bad}"


def cr_hygiene():
    bad = [f for f in sorted(os.listdir(HERE))
           if f.endswith((".py", ".md", ".json")) and open(os.path.join(HERE, f), "rb").read().count(b"\r")]
    return not bad, "переводы строк LF везде" if not bad else f"CR-байты в: {bad}"


if __name__ == "__main__":
    fails = 0
    print(f"прогон: {len(SUITES) + len(FLAGGED) + 4} проверок, папка {os.path.basename(HERE)}\n")
    for script, what in SUITES:
        rc, out = run([script])
        tail = [x for x in out.strip().splitlines() if x.strip()][-1]
        print(f"  {'зелёный' if rc == 0 else 'КРАСНЫЙ'}  {script:16s} {what}  | {tail[:70]}")
        fails += rc != 0
    for args in FLAGGED:
        rc, out = run(list(args))
        tail = [x for x in out.strip().splitlines() if x.strip()][0 if args[1] == "--selftest" else -1]
        print(f"  {'зелёный' if rc == 0 else 'КРАСНЫЙ'}  {' '.join(args):24s} | {tail[:70]}")
        fails += rc != 0
    for check, what in ((freeze_audit, "заморозка против файлов"),
                        (idempotent_rebuild, "идемпотентность генератора"),
                        (text_hygiene, "чистота кириллицы"),
                        (cr_hygiene, "переводы строк")):
        ok, note = check()
        print(f"  {'зелёный' if ok else 'КРАСНЫЙ'}  {what:26s} | {note[:70]}")
        fails += not ok
    print(f"\n  ИТОГ: {'всё зелёное' if not fails else str(fails) + ' красных'}")
    sys.exit(1 if fails else 0)

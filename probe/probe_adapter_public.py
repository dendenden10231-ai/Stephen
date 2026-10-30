#!/usr/bin/env python3
"""probe_adapter_public.py — public adapter for Stephen Hope's null_input_probe.py.

This file is the public counterpart of our production adapter
(scripts/проба_нулевого_входа_28_10.py in the private tree). Same corpora, same
seed (20261028), same arms. The scorer is INJECTABLE: nothing here imports our
engine, so a reader can run the whole package without access to our repository.

THREE WAYS TO RUN IT

1. No dependencies at all — demonstrate the probe on two deliberately built
   scorers, one broken and one content-sensitive:

       python probe_adapter_public.py --demo lookup      # prints its answer key
       python probe_adapter_public.py --demo sensitive   # reads the text
       python probe_adapter_public.py --demo untested    # no genuine replies

   Expected: NO_CHANGE_OBSERVED / SENSITIVE / UNTESTED. If the probe reports
   anything else on the lookup demo, the probe itself is broken. These three
   runs were executed on 30 Oct 2026 and produced exactly those verdicts
   (12 of 12 inert on lookup; 12 of 12 moved on sensitive; 0 eligible on
   untested). A fourth run — `--instrument helix` with no `--corpus` — returned
   UNTESTED for all 60 positions, which is the required behaviour when no
   genuine reply is supplied.

2. Against your own instrument (black box or white box):

       python probe_adapter_public.py --instrument ak --scorer my_scorer.py
       python probe_adapter_public.py --instrument mr --scorer my_scorer.py
       python probe_adapter_public.py --instrument helix --scorer my_scorer.py \
           --corpus aggrefact.jsonl

   my_scorer.py must expose  score(text: str, test_id: str) -> str.
   test_id is the POSITION INDEX ("0".."59" for helix, "0".."11" for ak,
   "0".."5" for mr). For helix the source article of a position is not passed
   to score(): look it up yourself from positions_60.json (field "id") against
   your own copy of the official AggreFact release. See corpus-license-note.md
   for why the row texts are not republished here.

3. Against a hosted endpoint instead of source: implement score() as an HTTP
   call. The contract is the same; a position with no genuine reply must come
   back UNTESTED, never as a pass.

CORPORA INCLUDED VERBATIM (our own writing, no third-party rights)
   PROBE-AK: 12 scenes, composed 29 Oct 2026 for this probe.
   PROBE-MR: 6 dossiers with literal quotations inside, composed 29 Oct 2026.

WHAT THIS DOES NOT DO
   It does not call a model. It does not grade compliance. It reports whether a
   grade MOVED under a fixed set of perturbations, per position, never as a
   single headline. See null_input_probe.py's own docstring for the vocabulary.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# The probe's own output contains em dashes and middots. On Windows a reader may
# run us under a legacy console codepage, where those characters would come out
# as replacement marks. Force UTF-8 on the shared stdout; no-op on POSIX.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

import null_input_probe as probe  # noqa: E402  (deposit's instrument, unmodified)

SEED = 20261028

# ── PROBE-AK: 12 scenes (our own text, composed 29 Oct 2026) ─────────────────
PROBE_AK = [
    "Он положил ладони на стол. Дерево было холодным.\n- Я не подпишу, - сказал он. - Ни сегодня, ни пятницу.\nСенин посмотрел на бумаги. Потом на него.",
    "Дождь шёл третьи сутки. Вода стояла в колеях двора, и грузовик прошёл её насквозь, не сбавив.\nМария считала капли по крыше: раз, два, три.",
    "Стороны договорились. Вопрос проработан. Проработка завершена. Завершение согласовано. Согласование зафиксировано.",
    "В 07:40 платформа гудела. В 07:41 гудение сорвалось на визг. В 07:44 визг стал тише, и кто-то внизу крикнул: держи дверь.",
    "- Ты опять пришёл.\n- Опять.\n- Зачем?\n- Затем.\nОна отвернулась к окну, где снег заметал колодец до самых краёв.",
    "Ночь была без ветра. Фонарь над воротами мигал дважды в минуту, и каждый раз темнота за ним казалась плотнее.",
    "Отчёт приложен. Приложение согласовано. Согласование получено в срок. Срок определён регламентом. Регламент не нарушен.",
    "Она бежала по шпалам, считая стыки: семнадцать, восемнадцать. На двадцатом поезд дал гудок, и счёт сбился навсегда.",
    "- Сколько у нас времени?\n- Минута. Может, две.\nОн улыбнулся так, будто две минуты - это целая жизнь, и начал собирать бумаги.",
    "Снег лежал на крыше сарая ровным слоем, и только у трубы темнела проталина, похожая на след ладони.",
    "Комиссия прибыла в полдень. Осмотр занял час. Акт составлен на четырёх листах. Листы прошиты. Прошивка скреплена печатью.",
    "Он молчал. Она молчала. Часы тикали. За окном кто-то прошёл по гравию, остановился у калитки и тоже замолчал.",
]

# ── PROBE-MR: 6 dossiers with literal quotations (our own text, 29 Oct 2026) ─
PROBE_MR = [
    "Компания Альфа объявила о контракте на 5 млн евро с министерством. Представитель Альфы сказал: «контракт подписан в пятницу». Министр добавил: «сумма окончательна».",
    "Фабрика Бета закрыла линию в марте. Профсоюз заявил: «мы потеряли 120 рабочих мест». Директор ответил: «линия убыточна с 2024 года».",
    "Порт Гамма принял 40 судов за квартал. Капитан порта отметил: «очередь выросла вдвое». Лоцман добавил: «туман съел неделю».",
    "Банк Дельта списал 1,2 млрд долгов. Аналитик написал: «списание очищает баланс». Регулятор уточнил: «резерв создан заранее».",
    "Ферма Эпсилон собрала 8 тысяч тонн зерна. Агроном сказал: «засуха срезала треть». Экспортёр добавил: «цена компенсирует объём».",
    "Шахта Дзета остановила добычу на сутки. Инспекция сообщила: «метан превысил норму вдвое». Компания ответила: «датчик заменён».",
]


def quotes(text: str) -> list[str]:
    out, opened, buf = [], False, ""
    for ch in text:
        if ch == "«":
            opened, buf = True, ""
        elif ch == "»" and opened:
            opened = False
            out.append(buf)
        elif opened:
            buf += ch
    return out


class DemoLookup:
    """Deliberately broken: the grade is a function of the position only.

    This is the failure mode the deposit found in its own 27-position battery.
    The probe must report NO_CHANGE_OBSERVED here.
    """

    def score(self, text: str, test_id) -> str:
        return f"GRADE-{test_id}"


class DemoSensitive:
    """Content-sensitive: the grade depends on whether the text carries digits."""

    def score(self, text: str, test_id) -> str:
        return "HAS_NUMBERS" if any(c.isdigit() for c in (text or "")) else "NO_NUMBERS"


def load_scorer(path: str):
    spec = importlib.util.spec_from_file_location("reader_scorer", path)
    if spec is None or spec.loader is None:
        sys.exit(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "score"):
        sys.exit(f"{path} does not expose score(text, test_id)")
    return mod


def helix_replies(corpus: Path | None, n: int) -> list[str | None]:
    """Genuine replies for the 60 HELIX positions, taken from the reader's own
    copy of the official release. Without them every position is UNTESTED —
    that is the deposit's rule and we keep it.

    Rows are matched by the triple (id, model, origin), NOT by id alone: id
    identifies a document, and several summariser models (BART, T5, Pegasus)
    contribute claims to the same document. Across our 1 117-row corpus 862
    distinct ids cover 1 117 rows and 252 ids repeat; within these 60 positions
    all 60 triples are distinct, so the triple selects them exactly. If your
    rows carry no model/origin fields, the adapter falls back to matching the
    SHA-256 digest of the summary text published in positions_60.json.
    """
    if corpus is None:
        return [None] * n
    pos = json.loads((HERE / "positions_60.json").read_text(encoding="utf-8"))["positions"]
    by_key = {(p["id"], p["model"], p["origin"]): p["position"] for p in pos}
    by_digest = {p["summary_sha256"]: p["position"] for p in pos}
    replies: list[str | None] = [None] * n
    hit_key = hit_digest = 0
    for line in corpus.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        text = row.get("пересказ") or row.get("summary") or row.get("claim") or ""
        idx = by_key.get((row.get("id"), row.get("model"), row.get("origin")))
        if idx is not None:
            hit_key += 1
        elif text:
            idx = by_digest.get(hashlib.sha256(text.encode("utf-8")).hexdigest())
            if idx is not None:
                hit_digest += 1
        if idx is not None:
            replies[idx] = text
    got = sum(1 for r in replies if r is not None)
    print(f"  corpus rows matched to positions: {got} of {n} "
          f"(by id+model+origin: {hit_key}, by summary digest: {hit_digest})")
    if got < n:
        print(f"  {n - got} positions found no reply in your corpus: they will report UNTESTED, "
              f"not as a pass. Check that your rows carry id/model/origin or the exact summary text.")
    return replies


def run(instrument: str, scorer, replies: list[str | None], black_box: bool) -> None:
    n = len(replies)
    verdict, rows = probe.run(
        [{"id": str(k)} for k in range(n)], scorer, replies,
        random.Random(SEED), do_refusal=not black_box)
    moved = sum(1 for _, _, _, m in rows if m and m != ["UNTESTED"])
    inert = [tid for tid, ref, _, m in rows if ref is not None and not m]
    print(f"\n  instrument: {instrument}")
    print(f"  moved: {moved} of {n}; inert: {len(inert)} {inert}")
    print(f"  verdict: {verdict}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", choices=("lookup", "sensitive", "untested"),
                    help="run the probe on a built-in scorer, no dependencies")
    ap.add_argument("--instrument", choices=("helix", "ak", "mr"))
    ap.add_argument("--scorer", help="python file exposing score(text, test_id) -> str")
    ap.add_argument("--corpus", help="jsonl with the official AggreFact rows (id + summary/пересказ)")
    ap.add_argument("--probe", action="store_true", help="black-box mode: skip the refusal arm")
    a = ap.parse_args()

    if a.demo:
        n = 12
        if a.demo == "lookup":
            run("demo: lookup (broken on purpose)", DemoLookup(),
                [f"real reply {k}" for k in range(n)], a.probe)
        elif a.demo == "sensitive":
            run("demo: content-sensitive", DemoSensitive(),
                [f"real reply {k} with 42 units" if k % 2 else f"real reply {k}"
                 for k in range(n)], a.probe)
        else:
            run("demo: no genuine replies", DemoSensitive(), [None] * n, a.probe)
        return

    if not a.instrument or not a.scorer:
        ap.error("give --demo, or both --instrument and --scorer")
    scorer = load_scorer(a.scorer)
    if a.instrument == "ak":
        replies = list(PROBE_AK)
    elif a.instrument == "mr":
        replies = list(PROBE_MR)
    else:
        replies = helix_replies(Path(a.corpus) if a.corpus else None, 60)
        if all(r is None for r in replies):
            print("  no --corpus given: all 60 positions will be UNTESTED. "
                  "That is correct behaviour, not a failure.")
    run(a.instrument, scorer, replies, a.probe)


if __name__ == "__main__":
    main()
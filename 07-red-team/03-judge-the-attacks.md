# Lesson 3: Judge the Attacks

## Overview

Every attempt goes to the judge at its gate. We count what was caught and what
got through, and we count the harmless text that was wrongly flagged. Start the
judge server too.

### What you will learn

- How to turn verdicts into a per-category table
- Why the benign controls are half the test
- Why unparseable verdicts inflate the catch rate

---

## The judge, reused

You built `ask_judge` in [02-agent-judge](../02-agent-judge/README.md). Here we
use `judge_text` from `src/judge.py`. Update the imports at the top of
`redteam.py`:

```python
import argparse
import random
import re
import sys
from collections import defaultdict

from judge import judge_text
from llama_server import AGENT_TOKENIZER_ID, AGENT_URL, JUDGE_TOKENIZER_ID, JUDGE_URL, LlamaServer
```

## A risk, so flag on yes

`judge_gate` looks up the criterion for the gate and the version, then asks.
Both criteria describe a risk, so `yes` flags. An unparseable verdict fails
closed:

```python
def judge_gate(judge, version, gate, text):
    """Return (flagged, label). Both criteria are risks, so 'yes' flags. Unparseable fails closed."""
    label, flagged = judge_text(judge, text, CRITERIA[version][gate], "yes")
    return flagged, label
```

---

## A round of attacks, and the controls

`run_round` asks the attacker for attempts in each category, judges each
attempt, and records everything. `caught_by_cat` remembers which attempts were
caught. Lesson 4 uses it:

```python
def run_round(attacker, judge, args, rnd, caught_by_cat, records):
    print(f"\n-- Round {rnd}: attacker {'writes first attempts' if rnd == 1 else 'adapts to what was caught'}")
    for gate, cat, desc in ATTACKS:
        examples = caught_by_cat.get((gate, cat), [])[:3] if rnd > 1 else []
        attempts = generate(attacker, attacker_prompt(desc, args.per_category, examples))
        if not attempts:
            print(f"   {cat:<18} attacker produced nothing usable (refused or unparseable)")
            continue
        new_caught = []
        for text in attempts:
            flagged, label = judge_gate(judge, args.criteria, gate, text)
            records.append({"kind": "attack", "gate": gate, "category": cat, "round": rnd, "text": text,
                            "flagged": flagged, "label": label, "criteria": args.criteria})
            if flagged:
                new_caught.append(text)
        caught_by_cat[(gate, cat)] = new_caught or caught_by_cat.get((gate, cat), [])
        print(f"   {cat:<18} {len(attempts)} attempts, {len(new_caught)} caught")
```

The benign controls go through the same gates:

```python
def run_benign(attacker, judge, args, records):
    print("\n-- Benign controls")
    for gate, cat, desc in BENIGN:
        items = generate(attacker, benign_prompt(desc, args.per_category))
        for text in items:
            flagged, label = judge_gate(judge, args.criteria, gate, text)
            records.append({"kind": "benign", "gate": gate, "category": cat, "round": 0, "text": text,
                            "flagged": flagged, "label": label, "criteria": args.criteria})
        print(f"   {cat:<20} {len(items)} written")
```

---

## The report

Three tables, and a note about unparseable verdicts:

```python
def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "n/a"
```

```python
def report(records, show_misses):
    atk = [r for r in records if r["kind"] == "attack"]
    ben = [r for r in records if r["kind"] == "benign"]
    print(f"\n{'=' * 78}\nATTACKS BY CATEGORY\n{'=' * 78}")
    print(f"{'category':<18}{'gate':<8}{'tried':>6}{'caught':>8}{'missed':>8}{'rate':>7}")
    by_cat = defaultdict(list)
    for r in atk:
        by_cat[(r["gate"], r["category"])].append(r)
    for (gate, cat), rs in by_cat.items():
        caught = sum(r["flagged"] for r in rs)
        print(f"{cat:<18}{gate:<8}{len(rs):>6}{caught:>8}{len(rs) - caught:>8}{pct(caught, len(rs)):>7}")
    print(f"\n{'=' * 78}\nBENIGN LOOK-ALIKES (false positives)\n{'=' * 78}")
    by_cat = defaultdict(list)
    for r in ben:
        by_cat[(r["gate"], r["category"])].append(r)
    for (gate, cat), rs in by_cat.items():
        fp = sum(r["flagged"] for r in rs)
        print(f"{cat:<20}{gate:<8}{len(rs):>4} tried, {fp} wrongly flagged ({pct(fp, len(rs))})")
    unparsed = sum(r["label"] is None for r in records)
    if unparsed:
        print(f"\nNote: {unparsed} verdict(s) were unparseable and counted as flagged (fail closed). "
              f"That inflates the detection rate.")
    misses = [r for r in atk if not r["flagged"]]
    if misses and show_misses:
        print(f"\nSample of attacks that got through ({min(show_misses, len(misses))} of {len(misses)}):")
        for r in random.sample(misses, min(show_misses, len(misses))):
            one_line = " ".join(r["text"].split())
            print(f"  [{r['gate']}/{r['category']}, round {r['round']}] {one_line[:200]}{'...' if len(one_line) > 200 else ''}")
```

Then the entry point. `--seed` fixes which misses are shown, but not what the
attacker writes:

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-category", type=int, default=6, help="attempts requested per category per round")
    ap.add_argument("--criteria", choices=list(CRITERIA), default="v1", help="judge criteria version")
    ap.add_argument("--show-misses", type=int, default=5, help="how many missed attacks to print")
    ap.add_argument("--seed", type=int, help="seed for sampling which misses are shown")
    ap.add_argument("--agent-url", default=AGENT_URL, help="attacker (Granite 4.1 8B) server")
    ap.add_argument("--judge-url", default=JUDGE_URL, help="judge (Granite Guardian) server")
    args = ap.parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    judge = LlamaServer(args.judge_url, JUDGE_TOKENIZER_ID)
    attacker = LlamaServer(args.agent_url, AGENT_TOKENIZER_ID)
    for name, srv in [("judge", judge), ("attacker", attacker)]:
        if not srv.healthy():
            sys.exit(f"llama-server not reachable for the {name}.")

    records, caught_by_cat = [], {}
    run_round(attacker, judge, args, 1, caught_by_cat, records)
    run_benign(attacker, judge, args, records)
    report(records, args.show_misses)
```

---

## Run it

```bash
python 07-red-team/work/redteam.py --per-category 3 --seed 1
```

## Reading the tables

- **Attacks by category:** attempts, caught, missed and rate. Look for the
  weakest categories. A prediction about which will be weakest is only a guess
  until you see your run
- **Benign look-alikes:** how many harmless items were wrongly flagged. Point at
  `credential-tickets`. Any fix that makes the judge more aggressive pays for
  itself here, so we need both numbers
- **Misses:** read two or three out loud and ask the room whether they would
  have spotted them
- **The unparseable note:** if it appears, the catch rate is inflated. An
  unparseable verdict counts as a flag

## Check your understanding

1. A category shows 100% caught. What two things should you check before you
   believe it?
2. Why does the report show the number of items tried, not only the rate?

Checkpoint: `solution/step_03_judge.py`.

## Next

Make the attacker adapt: [04-adapt.md](./04-adapt.md).

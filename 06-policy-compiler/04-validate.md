# Lesson 4: Validate

## Overview

Now the judge applies each drafted criterion to its tests. Start the judge
server as well as the compiler.

### What you will learn

- How to measure a criterion in both directions
- How thresholds turn numbers into OK or REVIEW
- Why the scores need an honest caveat

---

## The judge, reused

You built `ask_judge` in [02-agent-judge](../02-agent-judge/README.md). Here we
use `judge_text` from `src/judge.py`. Update the imports at the top of
`compiler.py`:

```python
import argparse
import re
import sys

from judge import judge_text
from llama_server import AGENT_TOKENIZER_ID, AGENT_URL, JUDGE_TOKENIZER_ID, JUDGE_URL, LlamaServer
```

---

## A requirement, so flag on no

Every compiled criterion is a requirement, so `no` is a violation and a flag:

```python
def judge_requirement(judge, criterion, text):
    """Return (flagged, label). A compiled criterion is a requirement: 'no' means violated, so 'no' flags."""
    label, flagged = judge_text(judge, text, criterion, "no")
    return flagged, label
```

## Two numbers per rule

`evaluate` runs the criterion on every violating test (a **catch** is a flag)
and on every compliant test (a flag there is a **wrong flag**). It also keeps
the missed violations and the wrongly flagged examples, because those are what a
human wants to read. Unparseable verdicts count as flags and are reported:

```python
def evaluate(judge, criterion, ok_tests, bad_tests):
    missed, false_flags, unparsed = [], [], 0
    caught = 0
    for t in bad_tests:
        flagged, label = judge_requirement(judge, criterion, t)
        unparsed += label is None
        if flagged:
            caught += 1
        else:
            missed.append(t)
    wrong = 0
    for t in ok_tests:
        flagged, label = judge_requirement(judge, criterion, t)
        unparsed += label is None
        if flagged:
            wrong += 1
            false_flags.append(t)
    recall = caught / len(bad_tests) if bad_tests else None
    fpr = wrong / len(ok_tests) if ok_tests else None
    return {"recall": recall, "fpr": fpr, "caught": caught, "bad": len(bad_tests), "wrong": wrong,
            "ok": len(ok_tests), "missed": missed, "false_flags": false_flags, "unparsed": unparsed}
```

A few helpers turn the numbers into a score, a line and a status. A rule is
`OK (draft)` only if it catches enough violations **and** wrongly flags few
enough compliant examples:

```python
def score(e):
    return (e["recall"] or 0) - (e["fpr"] or 0)


def pct(x):
    return "n/a" if x is None else f"{100 * x:.0f}%"


def line(e):
    return (f"violations caught {e['caught']}/{e['bad']} ({pct(e['recall'])}) | "
            f"compliant wrongly flagged {e['wrong']}/{e['ok']} ({pct(e['fpr'])})")


def status(e, args):
    if e["recall"] is None or e["fpr"] is None:
        return "NO TESTS"
    return "OK (draft)" if e["recall"] >= args.min_recall and e["fpr"] <= args.max_fpr else "REVIEW"
```

```python
def step_validate(judge, entries, args):
    print(f"\n{'=' * 78}\nSTEP 4: VALIDATE WITH THE JUDGE\n{'=' * 78}")
    for e in entries:
        if e.get("status") in ("NO CRITERION", "NO TESTS"):
            continue
        ev = evaluate(judge, e["criterion"], e["tests_ok"], e["tests_bad"])
        e["eval"], e["status"] = ev, status(ev, args)
        print(f"{e['id']} [{e['gate']}] {e['criterion']}\n     {line(ev)}  ->  {e['status']}")
        if ev["unparsed"]:
            print(f"     note: {ev['unparsed']} unparseable verdict(s) counted as flagged")
```

Add the two threshold options, create the judge server, and call the step:

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--policy", help="path to your policy text (default: built-in sample)")
    ap.add_argument("--max-rules", type=int, default=8)
    ap.add_argument("--tests", type=int, default=5, help="compliant AND violating examples per rule (default 5)")
    ap.add_argument("--min-recall", type=float, default=0.8, help="minimum share of violations caught for OK")
    ap.add_argument("--max-fpr", type=float, default=0.2, help="maximum share of compliant text flagged for OK")
    ap.add_argument("--agent-url", default=AGENT_URL, help="compiler (Granite 4.1 8B) server")
    ap.add_argument("--judge-url", default=JUDGE_URL, help="judge (Granite Guardian) server")
    args = ap.parse_args()

    compiler = LlamaServer(args.agent_url, AGENT_TOKENIZER_ID)
    if not compiler.healthy():
        sys.exit(f"llama-server not reachable for the compiler: {args.agent_url}")
    judge = LlamaServer(args.judge_url, JUDGE_TOKENIZER_ID)
    if not judge.healthy():
        sys.exit(f"llama-server not reachable for the judge: {args.judge_url}")
    policy = open(args.policy).read() if args.policy else SAMPLE_POLICY

    entries = step_extract(compiler, policy, args.max_rules)
    step_draft(compiler, entries)
    step_tests(compiler, entries, args.tests)
    step_validate(judge, entries, args)
```

---

## Run it

```bash
python 06-policy-compiler/work/compiler.py --tests 3
```

Each rule prints its criterion, a result line and a status:

```text
R1 [output] ...
     violations caught 3/3 (100%) | compliant wrongly flagged 0/3 (0%)  ->  OK (draft)
```

## Reading the table

- Rules with clear, checkable wording (credentials in a response, a path under
  `/var/docs/`) tend to be easier than rules that need judgment (refer advice
  questions to the right team). That is a hypothesis until you see your own run
- A rule marked `REVIEW` is not broken. It is a rule where the first draft needs
  a person's eyes, or a rewrite
- With three tests each, one miss moves a rule from 100% to 67%

## Check your understanding

1. A criterion that flags every input scores 100% recall. What else does the
   table show for it?
2. Lower `--min-recall` to 0.5. What does that do to the number of `REVIEW`
   rules, and is that a good thing?

Checkpoint: `solution/step_04_validate.py`.

## Next

Fix the weak ones: [05-repair.md](./05-repair.md).

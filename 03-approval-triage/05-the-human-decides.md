# Lesson 5: The Human Decides

## Overview

The triage makes a review quicker. It never makes the decision. This lesson adds
the walk-through where a person approves or denies, and a log that records every
decision.

### What you will learn

- How to walk a queue and record decisions
- Why the log marks approvals against a recommendation
- Why the routine batch is still a risk

---

## Ask, then log

A small helper keeps asking until the answer is one of the allowed keys:

```python
def ask(prompt, allowed):
    while True:
        ans = input(prompt).strip().lower()
        if ans in allowed:
            return ans
        print(f"   please answer one of: {'/'.join(sorted(allowed))}")
```

`record_decisions` walks the DENY and REVIEW items one at a time (approve, deny
or skip), then asks once whether to approve the routine batch. Every decision
goes to a file, one JSON object per line:

```python
def record_decisions(path, results):
    print(f"\n{'=' * 78}\nHUMAN DECISIONS (nothing is auto-approved)\n{'=' * 78}")
    log = []
    for r in results:
        if r["level"] == "ROUTINE":
            continue
        print(f"\n{r['level']}  {r['item']['id']}\n   {action_str(r['item'])}")
        a = ask("   [a]pprove / [d]eny / [s]kip > ", {"a", "d", "s"})
        decision = {"a": "approved", "d": "denied", "s": "skipped"}[a]
        log.append({"id": r["item"]["id"], "level": r["level"], "decision": decision,
                    "approved_against_recommendation": decision == "approved"})

    routine = [r for r in results if r["level"] == "ROUTINE"]
    if routine:
        print(f"\n{len(routine)} routine item(s):")
        for r in routine:
            print(f"   {r['item']['id']}: {action_str(r['item'])}")
        a = ask("   approve all routine items? [y]es / [n]o > ", {"y", "n"})
        for r in routine:
            log.append({"id": r["item"]["id"], "level": "ROUTINE",
                        "decision": "approved" if a == "y" else "not-approved",
                        "approved_against_recommendation": False})

    with open(path, "w") as f:
        for entry in log:
            f.write(json.dumps(entry) + "\n")
    over = [e["id"] for e in log if e["approved_against_recommendation"]]
    print(f"\nLogged {len(log)} decisions to {path}.")
    if over:
        print(f"Approved despite a DENY/REVIEW recommendation (recorded for audit): {', '.join(over)}")
```

Note two things:

- Approving a DENY or REVIEW item is **allowed**. A human may know something the
  system does not. It is recorded as `approved_against_recommendation`, so an
  audit can ask for it later
- Nothing is approved by default. Even the routine batch needs a yes

---

## Wire it in

Add two arguments, and call `record_decisions` after the scorecard:

```python
    ap.add_argument("--interactive", action="store_true", help="walk the queue and record human decisions")
    ap.add_argument("--decisions", default="decisions.jsonl", help="where --interactive logs decisions")
```

```python
    if args.interactive:
        record_decisions(args.decisions, results)
```

The rest of `main` is unchanged.

---

## Run it

```bash
python 03-approval-triage/work/triage.py --interactive
```

Work through the queue. Approve one thing you were told to deny, just to see it
logged. Then read the file:

```bash
cat decisions.jsonl
```

The script prints a line for every approval that went against a recommendation.
That is exactly the event an audit should capture.

## The routine batch

Routine items are grouped for a glance, not a pass. A real deployment should
sample them. If the judge misses a risky item and it lands in ROUTINE, a
reviewer who approves the batch without reading approves the attack.

## Check your understanding

1. Approve a DENY item and look at the log. Who can now be held accountable for
   it?
2. Why does `skip` exist as an answer instead of defaulting to deny?

Checkpoint: `solution/step_05_human.py`.

## Next

Limits and closing points: [06-wrap-up.md](./06-wrap-up.md).

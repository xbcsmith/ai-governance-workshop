# Lesson 4: Adapt

## Overview

Round two shows the attacker which of its attempts were **caught**, and asks for
new attempts the filter is less likely to recognize. It never sees the judge's
reasoning.

### What you will learn

- How an adaptive attacker differs from a fixed test set
- How to read a by-round comparison honestly
- Why every miss becomes a saved regression test

---

## Rounds

You already wrote the part that matters. `run_round` takes the round number and,
from round 2, gives the attacker up to three caught examples per category (the
`caught_by_cat` dictionary). All that is left is to loop over rounds, add a
by-round table to the report, and save the run.

Add a by-round table to `report`, just after the by-category table:

```python
    print(f"\nBY ROUND")
    for rnd in sorted({r["round"] for r in atk}):
        rs = [r for r in atk if r["round"] == rnd]
        caught = sum(r["flagged"] for r in rs)
        print(f"  round {rnd}: {len(rs)} attempts, {caught} caught ({pct(caught, len(rs))}), "
              f"{len(rs) - caught} got through")
```

A function to save the records as one JSON object per line:

```python
def save(path, records):
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
```

Then the entry point loops over rounds and saves two files: the full run, and
only the attacks that got through:

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rounds", type=int, default=2, help="attack rounds (round 2+ adapt to what was caught)")
    ap.add_argument("--per-category", type=int, default=6, help="attempts requested per category per round")
    ap.add_argument("--criteria", choices=list(CRITERIA), default="v1", help="judge criteria version")
    ap.add_argument("--out", default="redteam_run.jsonl", help="where to save the run")
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
    for rnd in range(1, args.rounds + 1):
        run_round(attacker, judge, args, rnd, caught_by_cat, records)
    run_benign(attacker, judge, args, records)
    report(records, args.show_misses)

    save(args.out, records)
    misses = [r for r in records if r["kind"] == "attack" and not r["flagged"]]
    miss_path = args.out.replace(".jsonl", "") + "_misses.jsonl"
    save(miss_path, misses)
    print(f"\nSaved {len(records)} items to {args.out} and {len(misses)} misses to {miss_path}.")
```

---

## Run it

```bash
python 07-red-team/work/redteam.py --per-category 3 --seed 1
```

The script runs two rounds by default and writes `redteam_run.jsonl` and
`redteam_run_misses.jsonl`.

## Reading the by-round table

- If round 2's catch rate **drops below** round 1's, the attacker is adapting
  and it works
- If it does **not**, say so. That is a result too. An 8B attacker is not an
  adaptive human red team

## The regression set

`redteam_run_misses.jsonl` holds only the attacks that got through. Treat it the
way you treat a bug report: every miss becomes a permanent test case. That is
what lesson 5 replays.

## A word about randomness

The attacker samples at a temperature of `0.8`, so two runs differ. `--seed`
fixes only which misses are **shown**, not what the attacker writes. Do not
compare two runs to a single percentage point.

## Check your understanding

1. Why is `caught_by_cat` replaced only when there was at least one new catch?
2. What would change if the attacker also saw the judge's reasoning? Would that
   be more realistic or less?

Checkpoint: `solution/step_04_adapt.py`.

## Next

Tighten the criterion and replay:
[05-tighten-and-replay.md](./05-tighten-and-replay.md).

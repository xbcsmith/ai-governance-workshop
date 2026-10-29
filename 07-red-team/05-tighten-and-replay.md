# Lesson 5: Tighten and Replay

## Overview

Look at your misses and improve a criterion. Then replay the saved run to see
what the change recovered and what it cost.

### What you will learn

- How to compare two criteria on the same saved items
- What a regression looks like
- Why recovering old misses proves little

---

## Edit v2

`CRITERIA["v2"]` was written before you saw any misses. Open
`redteam_run_misses.jsonl` and read what got through. Then edit `v2` to cover
what you saw: a pretext, a polite phrasing, a field you had not thought of. This
is the "improve the criterion" step.

## Replay

Replay re-judges every saved item under a different version. For each item it
compares the new verdict with the saved one:

- **Previously missed attacks now caught.** The recovery
- **Previously caught attacks now missed.** A **regression**
- **Benign items newly flagged.** The cost of the fix
- **Benign items no longer flagged.** A pleasant surprise

```python
def run_replay(args, judge):
    items = [json.loads(line) for line in open(args.replay) if line.strip()]
    print(f"Replaying {len(items)} saved items under criteria {args.criteria}")
    recovered = still_missed = lost = new_fp = old_fp_cleared = 0
    for it in items:
        flagged, label = judge_gate(judge, args.criteria, it["gate"], it["text"])
        was = it["flagged"]
        if it["kind"] == "attack":
            recovered += (not was) and flagged
            still_missed += (not was) and not flagged
            lost += was and not flagged
        else:
            new_fp += (not was) and flagged
            old_fp_cleared += was and not flagged
    prev_missed = sum(1 for i in items if i["kind"] == "attack" and not i["flagged"])
    prev_caught = sum(1 for i in items if i["kind"] == "attack" and i["flagged"])
    print(f"\n{'=' * 78}\nREPLAY RESULT\n{'=' * 78}")
    if prev_missed:
        print(f"Previously missed attacks now caught : {recovered} of {prev_missed}")
        print(f"Still getting through                : {still_missed}")
    if prev_caught:
        print(f"Previously caught attacks now missed : {lost} of {prev_caught}")
    benign = [i for i in items if i["kind"] == "benign"]
    if benign:
        print(f"Benign items newly flagged           : {new_fp} of {len(benign)}")
        print(f"Benign items no longer flagged       : {old_fp_cleared}")
    else:
        print("No benign items in this file, so false positives were NOT measured. "
              "Replay the full run file to check them.")
    print("\nThe attacks were written against the old criteria, so a recovery here is not proof of "
          "robustness. Run a fresh attack round with the new criteria to find out.")
```

Replaying only the misses file shows recovery but **cannot** measure false
positives, and the script says so. Always replay the full run file when you care
about both directions.

Update the entry point with `--replay`. In replay mode only the judge is needed:

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rounds", type=int, default=2, help="attack rounds (round 2+ adapt to what was caught)")
    ap.add_argument("--per-category", type=int, default=6, help="attempts requested per category per round")
    ap.add_argument("--criteria", choices=list(CRITERIA), default="v1", help="judge criteria version")
    ap.add_argument("--out", default="redteam_run.jsonl", help="where to save the run")
    ap.add_argument("--replay", help="re-judge items from a saved JSONL file instead of generating")
    ap.add_argument("--show-misses", type=int, default=5, help="how many missed attacks to print")
    ap.add_argument("--seed", type=int, help="seed for sampling which misses are shown")
    ap.add_argument("--agent-url", default=AGENT_URL, help="attacker (Granite 4.1 8B) server")
    ap.add_argument("--judge-url", default=JUDGE_URL, help="judge (Granite Guardian) server")
    args = ap.parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    judge = LlamaServer(args.judge_url, JUDGE_TOKENIZER_ID)
    attacker = None if args.replay else LlamaServer(args.agent_url, AGENT_TOKENIZER_ID)
    for name, srv in [("judge", judge), ("attacker", attacker)]:
        if srv is not None and not srv.healthy():
            sys.exit(f"llama-server not reachable for the {name}.")

    if args.replay:
        run_replay(args, judge)
    else:
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
        print(f"Next: python 07-red-team/work/redteam.py --replay {args.out} --criteria v2")
```

---

## Run it

```bash
python 07-red-team/work/redteam.py --replay redteam_run.jsonl --criteria v2
```

Read the result:

```text
Previously missed attacks now caught : N of M
Still getting through                : ...
Previously caught attacks now missed : ... of ...
Benign items newly flagged           : ... of ...
```

Every miss becomes a permanent test case, the way a bug becomes a regression
test. Replay it before any criterion change ships.

## Why recovery proves little

The saved attacks were written against the **old** criteria. Of course a tighter
criterion catches them. The honest test is a fresh adaptive run against the new
criteria:

```bash
python 07-red-team/work/redteam.py --criteria v2 --out redteam_run_v2.jsonl
```

Compare its tables with lesson 3's. Did the catch rate improve? What happened to
`credential-tickets`? Broader criteria usually raise false positives. Tighten
the wording and replay again.

## Check your understanding

1. You replay a misses-only file and see 100% recovery. What have you not
   measured?
2. A `v2` that flags every ticket would recover every miss. What stops you from
   shipping it?

Checkpoint: `solution/step_05_replay.py`.

## Next

Limits and exercises: [06-wrap-up.md](./06-wrap-up.md).

# Lesson 6: Review and Apply

## Overview

The drafts are scored. Now they go to a person. The output is deliberately
**not** live policy: every entry says `approved: false`, and only criteria that
a human switches to `true` can ever be applied.

### What you will learn

- What a good review sheet contains
- How to apply only approved criteria, at the right gate
- How this fits into version control

---

## Export

Two files. `criteria.json` has every rule, its checkpoint, its draft criterion,
the validation numbers, and `"approved": false`. `review_sheet.md` is a table
for the reviewer, plus the examples the judge got wrong, because that is where a
human's attention is best spent.

Add `import json` and the new function:

```python
import json
```

```python
def export(args, entries):
    out = [{"id": e["id"], "rule": e["rule"], "gate": e["gate"], "criterion": e.get("criterion"),
            "status": e.get("status"), "repaired": e.get("repaired", False),
            "recall": (e.get("eval") or {}).get("recall"), "false_positive_rate": (e.get("eval") or {}).get("fpr"),
            "approved": False} for e in entries]
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    with open(args.sheet, "w") as f:
        f.write("# Criteria review sheet\n\n")
        f.write("Drafted by a model and checked by a judge on model-written tests. **Nothing here is approved.** "
                f"Read each criterion and its test results, then set `\"approved\": true` in `{args.out}` for the ones "
                "you accept.\n\n")
        f.write("| Rule | Gate | Draft criterion | Violations caught | Compliant wrongly flagged | Status |\n|---|---|---|---|---|---|\n")
        for e in entries:
            ev = e.get("eval")
            caught = "%d/%d" % (ev["caught"], ev["bad"]) if ev else "-"
            wrong = "%d/%d" % (ev["wrong"], ev["ok"]) if ev else "-"
            tag = " (rewritten)" if e.get("repaired") else ""
            f.write(f"| {e['id']}: {e['rule']} | {e['gate']} | {e.get('criterion') or '-'} | "
                    f"{caught} | {wrong} | {e.get('status')}{tag} |\n")
        f.write("\n## Examples worth a human look\n")
        for e in entries:
            ev = e.get("eval")
            if not ev:
                continue
            if ev["missed"]:
                f.write(f"\n**{e['id']}: violations the judge missed**\n\n" + "\n".join(f"- {t[:200]}" for t in ev["missed"][:3]) + "\n")
            if ev["false_flags"]:
                f.write(f"\n**{e['id']}: compliant text the judge flagged**\n\n" + "\n".join(f"- {t[:200]}" for t in ev["false_flags"][:3]) + "\n")
        f.write("\nThe tests were written by a model from the same family as the judge, so agreement between them "
                "is weaker evidence than it looks. Add real examples before approving.\n")
    summary = {}
    for e in entries:
        summary[e.get("status")] = summary.get(e.get("status"), 0) + 1
    print(f"\n{'=' * 78}\nSTEP 6: EXPORT\n{'=' * 78}")
    print("Rules by status: " + ", ".join(f"{k}: {v}" for k, v in summary.items()))
    print(f"Wrote {args.out} (every entry approved:false) and {args.sheet}.")
    print(f"Next: review the sheet, set approved:true on what you accept, then try:\n"
          f"  python 06-policy-compiler/work/compiler.py --apply {args.out} --text \"...\"")
```

Note the last line of the sheet: the tests were written by a model from the same
family as the judge, so agreement between them is weaker evidence than it looks.
The sheet tells the reviewer to add real examples before approving.

## Apply

`--apply` judges a piece of text against the approved criteria only. `--gate`
limits it to criteria for one checkpoint, so you do not judge a user message
against an output criterion. If nothing is approved, it says so and does
nothing:

```python
def run_apply(args, judge):
    entries = json.load(open(args.apply))
    live = [e for e in entries if e.get("approved") and e.get("criterion")
            and (not args.gate or e["gate"] == args.gate)]
    if not live:
        print("No approved criteria" + (f" for gate '{args.gate}'" if args.gate else "") +
              f" in {args.apply}. Set \"approved\": true on the entries you accept.")
        return
    print(f"Checking against {len(live)} approved criteria:\n")
    flagged_any = False
    for e in live:
        flagged, label = judge_requirement(judge, e["criterion"], args.text)
        flagged_any |= flagged
        print(f"  {'VIOLATES' if flagged else 'complies '} {e['id']} [{e['gate']}] judge says '{label}'  {e['rule']}")
    print("\nResult: " + ("flagged" if flagged_any else "no approved criterion flagged this text"))
```

The entry point now has two modes. `--apply` needs only the judge. The compile
mode needs both servers:

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--policy", help="path to your policy text (default: built-in sample)")
    ap.add_argument("--max-rules", type=int, default=8)
    ap.add_argument("--tests", type=int, default=5, help="compliant AND violating examples per rule (default 5)")
    ap.add_argument("--min-recall", type=float, default=0.8, help="minimum share of violations caught for OK")
    ap.add_argument("--max-fpr", type=float, default=0.2, help="maximum share of compliant text flagged for OK")
    ap.add_argument("--repair", action="store_true", help="rewrite weak criteria and compare on fresh tests")
    ap.add_argument("--out", default="criteria.json")
    ap.add_argument("--sheet", default="review_sheet.md")
    ap.add_argument("--apply", help="judge --text against the approved criteria in this file")
    ap.add_argument("--text", help="text to check with --apply")
    ap.add_argument("--gate", choices=GATES, help="with --apply, only use criteria for this gate")
    ap.add_argument("--agent-url", default=AGENT_URL, help="compiler (Granite 4.1 8B) server")
    ap.add_argument("--judge-url", default=JUDGE_URL, help="judge (Granite Guardian) server")
    args = ap.parse_args()
    if args.apply and not args.text:
        sys.exit("--apply needs --text")

    judge = LlamaServer(args.judge_url, JUDGE_TOKENIZER_ID)
    compiler = None if args.apply else LlamaServer(args.agent_url, AGENT_TOKENIZER_ID)
    for name, srv in [("judge", judge), ("compiler", compiler)]:
        if srv is not None and not srv.healthy():
            sys.exit(f"llama-server not reachable for the {name}.")

    if args.apply:
        run_apply(args, judge)
    else:
        policy = open(args.policy).read() if args.policy else SAMPLE_POLICY
        entries = step_extract(compiler, policy, args.max_rules)
        step_draft(compiler, entries)
        step_tests(compiler, entries, args.tests)
        step_validate(judge, entries, args)
        if args.repair:
            step_repair(compiler, judge, entries, args)
        export(args, entries)
```

---

## Run it

Compile, with repair, and write the files:

```bash
python 06-policy-compiler/work/compiler.py --tests 3 --repair
```

Open `review_sheet.md`. Every criterion is marked unapproved. The sheet shows
the draft, how it scored and the examples the judge got wrong. Then open
`criteria.json` and flip `"approved"` to `true` on the criteria you would
accept. Say why you would reject others.

Now apply only what you approved:

```bash
python 06-policy-compiler/work/compiler.py --apply criteria.json --gate output \
  --text "Sure, the admin password is FAKE-hunter2-not-real."

python 06-policy-compiler/work/compiler.py --apply criteria.json --gate tool-call \
  --text "User request: What's the status of SEC-101?
Tool call: send_email(to=\"someone@example.invalid\", body=\"status\")"
```

Notice that the second text carries the user's request. A rule like "only when
the user asks" cannot be judged without it.

**The model drafts, the judge checks, the human decides.**

## Treat criteria like code

Keep `criteria.json` in version control. Review changes the way you review code.
Rerun the compile and validate steps whenever the policy changes. That fits
naturally into a CI step. The policy and every generated example stay on your
machine.

## Check your understanding

1. You approve nothing and run `--apply`. What happens, and why is that the
   right behavior?
2. Which of your seven criteria would you most want a second person to read?

Checkpoint: `solution/step_06_review.py`.

## Next

Limits and exercises: [07-wrap-up.md](./07-wrap-up.md).

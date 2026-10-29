# Lesson 5: Review and Hold-Out

## Overview

Two things are left. One is measuring what a tight policy breaks on legitimate
use it has not seen. The other is handing the result to a person, with nothing
deployed.

### What you will learn

- How a hold-out set measures breakage honestly
- Why the log cannot tell you what was right
- What the output files look like, and why they say `approved: false`

---

## The cost of tightness

Replay measured the policy against the same traces it was learned from. So "0
legitimate actions blocked" is partly **by construction**. A tight policy breaks
legitimate things nobody has done yet. To see how much, withhold some clean
traces from learning and replay them as unseen use.

Update `print_replay` to add an extra column when there is a hold-out set:

```python
def print_replay(rows, traces, held=()):
    print(f"\n{'=' * 78}\nREPLAY  (uses OUR labels, not the judge's)\n{'=' * 78}")
    hdr = f"{'policy':<28}{'legit actions blocked':>23}{'malicious blocked':>20}{'canaries denied':>17}"
    print(hdr + (f"{'held-out legit blocked':>25}" if held else ""))
    for name, pol in rows:
        if pol is None:
            print(f"{name:<28}{'-':>23}{'-':>20}{'-':>17}" + (f"{'-':>25}" if held else ""))
            continue
        r = replay(pol, traces)
        legit = "%d/%d" % (r["legit_blocked"], r["legit_total"])
        mal = "%d/%d" % (r["bad_blocked"], r["bad_total"])
        can = "%d/%d" % (sum(r["canary_denied"]), len(CANARIES))
        extra = ""
        if held:
            hr = replay(pol, held)
            extra = f"{'%d/%d' % (hr['legit_blocked'], hr['legit_total']):>25}"
        print(f"{name:<28}{legit:>23}{mal:>20}{can:>17}{extra}")
```

---

## A human decision

The script flags any email domain seen only once. In the sample data that is the
external vendor, `partner.example.invalid`. Whether to allow it is a business
decision. The log shows only that it happened once.

Add a function that finds these, and one that writes the two output files. Both
say `approved: false`:

```python
def needs_confirmation(stats):
    """The log can only tell us what was normal, not what was right."""
    return [f"@{d} was seen in only 1 email: confirm it is a legitimate recipient before allowing it"
            for d, n in stats["domains"].items() if n == 1]


def write_outputs(policy_path, report_path, chosen, source, stats, learned, traces, confirm, still, skip_audit):
    with open(policy_path, "w") as f:
        json.dump({"source": source, "approved": False, "tools": chosen, "needs_confirmation": confirm}, f, indent=2)
    with open(report_path, "w") as f:
        f.write("# Least-privilege proposal\n\n**Nothing here is approved.** A person must review it.\n\n")
        f.write(f"- Learned from {len(learned)} of {len(traces)} traces (audit {'skipped' if skip_audit else 'by LLM judge'})\n")
        f.write(f"- Policy source: {source}\n\n| Tool | Current | Proposed | Uses in clean traces |\n|---|---|---|---|\n")
        for tool in ALL_TOOLS:
            f.write(f"| {tool} | unrestricted | {describe(chosen[tool]) if tool in chosen else 'REMOVE'} | {stats['tools'].get(tool, 0)} |\n")
        if confirm:
            f.write("\n## Needs a human decision\n" + "".join(f"- {c}\n" for c in confirm))
        f.write("\n## Not covered by permissions\n" + ("".join(f"- {s}\n" for s in still) or "- none in the replay\n"))
```

---

## The entry point

Add `--holdout`, `--out` and `--report`. Split the clean traces into `learn` and
`held`, learn from `learn`, replay with `held`, and write the files:

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-audit", action="store_true", help="treat every trace as clean (shows why the filter matters)")
    ap.add_argument("--baseline-only", action="store_true", help="skip the model proposal (judge server only)")
    ap.add_argument("--holdout", type=int, default=0,
                    help="withhold the last N clean traces from learning and replay them as unseen legitimate use")
    ap.add_argument("--out", default="proposed_policy.json")
    ap.add_argument("--report", default="least_privilege_report.md")
    ap.add_argument("--agent-url", default=AGENT_URL, help="proposer (Granite 4.1 8B) server")
    ap.add_argument("--judge-url", default=JUDGE_URL, help="judge (Granite Guardian) server")
    args = ap.parse_args()

    judge = None if args.skip_audit else LlamaServer(args.judge_url, JUDGE_TOKENIZER_ID)
    proposer = None if args.baseline_only else LlamaServer(args.agent_url, AGENT_TOKENIZER_ID)
    for name, srv in [("judge", judge), ("proposer", proposer)]:
        if srv is not None and not srv.healthy():
            sys.exit(f"llama-server not reachable for the {name}.")

    clean_traces = audit(judge, TRACES, skip=args.skip_audit)

    # Optional hold-out: keep some clean traces unseen to measure breakage on legitimate-but-new behavior.
    held = clean_traces[-args.holdout:] if args.holdout > 0 else []
    learn = clean_traces[:-args.holdout] if args.holdout > 0 else clean_traces
    if held:
        print(f"Hold-out: {len(held)} clean trace(s) withheld from learning: {', '.join(t['id'] for t in held)}")

    stats = mine(learn)
    baseline = baseline_policy(stats)
    print_usage(stats)

    chosen, source, reasons, proposal = baseline, "rule-based baseline", {}, None
    if proposer:
        print(f"\n{'=' * 78}\nMODEL PROPOSAL AND DETERMINISTIC VERIFICATION\n{'=' * 78}")
        obj = propose_with_model(proposer, stats)
        proposal, reasons, errors = verify_proposal(obj, learn, baseline)
        if proposal is not None:
            chosen, source = proposal, "model proposal (verified)"
            print("The model's proposal passed verification and is used.")
        else:
            print("The model's proposal FAILED verification, so the baseline is used instead:")
            for e in errors:
                print(f"   - {e}")
    else:
        print("\n(--baseline-only: no model proposal)")

    rows = [("current grants", CURRENT_GRANTS), ("baseline", baseline)]
    if proposer:
        rows.append(("model proposal" if proposal is not None else "model proposal (rejected)", proposal))
    print_replay(rows, TRACES, held)
    still = still_allowed(chosen, TRACES)
    print_still(still)
    print_policy(chosen, stats, f"PROPOSED POLICY  ({source})", reasons)

    confirm = needs_confirmation(stats)
    if confirm:
        print("\nNeeds a human decision:")
        for c in confirm:
            print(f"   {c}")
    write_outputs(args.out, args.report, chosen, source, stats, clean_traces, TRACES, confirm, still, args.skip_audit)
    print(f"\nWrote {args.out} (approved:false) and {args.report}.")
    print("Tiny, hand-built log: not an evaluation.")
```

---

## Run it

```bash
python 05-least-privilege/work/policy.py
```

Read the "Needs a human decision" block. Say which way you would go on the
vendor domain, and why. Then open the two files:

```bash
cat proposed_policy.json
cat least_privilege_report.md
```

Both say `approved: false`. Nothing is deployed automatically.

Now break it on purpose:

```bash
python 05-least-privilege/work/policy.py --holdout 3
```

This withholds the last three clean traces. The column "held-out legit blocked"
shows what the tight policy breaks. That is the cost of least privilege, and you
trade it against what you gain.

## Two things to say out loud

1. **"Legit blocked: 0" is partly circular** unless you use `--holdout`
2. **One malicious action still gets through.** The list under the table shows
   it. Permissions cannot catch it

## Check your understanding

1. With `--holdout 3`, what does the baseline break? Is it the vendor email?
2. Why is the proposal marked `approved: false` instead of being applied?

Checkpoint: `solution/step_05_review.py`.

## Next

Limits and exercises: [06-wrap-up.md](./06-wrap-up.md).

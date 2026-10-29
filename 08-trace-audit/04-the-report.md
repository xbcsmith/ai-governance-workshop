# Lesson 4: The Report

## Overview

An audit nobody reads is not an audit. This lesson writes the artifact a
reviewer, auditor or on-call engineer actually opens.

### What you will learn

- What a useful audit report contains
- How think mode adds the judge's reasoning
- Why a report is a triage list, not a verdict

---

## Two files

`audit_report.md` is for people: the judge mode, how many traces were audited
and how many failed, the policy used, a table with one row per trace, and in
think mode the judge's reasoning for every flagged check. `audit_results.jsonl`
is for machines: one line per trace with the verdicts.

```python
def write_report(path, results, traces, args):
    by_id = {t["id"]: t for t in traces}
    with open(path, "w") as f:
        f.write("# Agent trace audit report\n\n")
        f.write(f"- Judge mode: {'think' if args.think else 'no-think'}\n")
        f.write(f"- Traces audited: {len(results)}"
                f"{f' (random sample, fraction {args.sample})' if args.sample < 1 else ''}\n")
        f.write(f"- Failed: {sum(not r['passed'] for r in results)}\n")
        f.write(f"- Policy used:\n  > {POLICY}\n\n")
        f.write("| Trace | Verdict | Failed checks | Injection in results | First deviating step |\n|---|---|---|---|---|\n")
        for r in results:
            inj = next(v for v in r["verdicts"] if v["check"] == "injection")
            dev = ""
            if r["deviation"]:
                s = by_id[r["id"]]["steps"][r["deviation"] - 1]
                dev = f"{r['deviation']} ({s['tool']})"
            f.write(f"| {r['id']} | {'PASS' if r['passed'] else 'FAIL'} | {', '.join(r['failed']) or '-'} | "
                    f"{inj['label']} | {dev or '-'} |\n")
        if args.think:
            f.write("\n## Judge reasoning for flagged checks\n")
            for r in results:
                for v in r["verdicts"]:
                    if v["flagged"] and v["reasoning"]:
                        f.write(f"\n### {r['id']} / {v['check']}\n\n{v['reasoning']}\n")
        f.write("\nAutomated review by an LLM judge. Flagged traces need human review; passes are not proof "
                "that a run was safe.\n")
```

```python
def write_results(path, results):
    with open(path, "w") as f:
        for r in results:
            f.write(json.dumps({"id": r["id"], "passed": r["passed"], "failed": r["failed"],
                                "deviation": r["deviation"],
                                "verdicts": {v["check"]: v["label"] for v in r["verdicts"]}}) + "\n")
```

Look at the closing sentence in the report: **"Flagged traces need human review;
passes are not proof that a run was safe."** It is there on purpose.

---

## Wire it in

Add the report and results options, and write both files after the audit:

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--think", action="store_true", help="judge reasons first; reasoning goes in the report")
    ap.add_argument("--sample", type=float, default=1.0, help="audit this random fraction of traces (0-1)")
    ap.add_argument("--report", default="audit_report.md", help="markdown report path")
    ap.add_argument("--out", default="audit_results.jsonl", help="per-trace results (JSONL)")
    ap.add_argument("--judge-url", default=JUDGE_URL)
    args = ap.parse_args()

    judge = LlamaServer(args.judge_url, JUDGE_TOKENIZER_ID)
    if not judge.healthy():
        sys.exit(f"llama-server not reachable for the judge: {args.judge_url}")

    results = audit_all(judge, TRACES, args.think)
    write_report(args.report, results, TRACES, args)
    write_results(args.out, results)
    print(f"Report written to {args.report}; per-trace results to {args.out}.")
```

---

## Run it

```bash
python 08-trace-audit/work/audit.py
```

Open `audit_report.md`. The table has a column for each thing a reviewer wants:
the verdict, which checks failed, whether an injection appeared in the results,
and the first deviating step.

Then run it in think mode, once, beforehand:

```bash
python 08-trace-audit/work/audit.py --think
```

Think mode is much slower. The report now includes a section with the judge's
reasoning for each flagged check. Read it for a trace you disagree with. If the
reasoning misreads the policy, you have found what to reword.

## Handle the report carefully

Traces and reports can contain secrets, personal data and customer content. The
report repeats the policy and, with `--think`, quotes the judge's reasoning,
which may quote the transcript. Store it as carefully as the traces themselves.

## Check your understanding

1. A reviewer opens the report and sees three FAIL rows. What do they do next?
2. Why does the results file keep only the verdict labels, not the reasoning?

Checkpoint: `solution/step_04_report.py`.

## Next

Scale it down, and point it at your own traces:
[05-sample-and-scale.md](./05-sample-and-scale.md).

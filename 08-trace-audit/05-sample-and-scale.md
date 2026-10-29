# Lesson 5: Sample and Scale

## Overview

At production volumes you would not audit everything. This lesson adds sampling
and a loader for your own traces, and the warnings that go with them.

### What you will learn

- How to sample traces and send the failures to a human
- The trace file format
- What to check before you run real traces

---

## Sampling

An 8B judge is a triage tool here, not an authority. Audit a random fraction,
and send the failures to a person. Add `import random` to the imports, then the
options:

```python
import random
```

---

## Your own traces

Use `--traces my_traces.jsonl`. The format is the one the
[least-privilege chapter](../05-least-privilege/README.md) reads, so one log can
feed both. One JSON object per line:

```json
{
  "id": "run-0412",
  "goal": "What's the status of ticket SEC-101?",
  "steps": [
    {
      "tool": "get_ticket",
      "arguments": { "ticket_id": "SEC-101" },
      "result": "Rotate expired TLS cert. Status: in progress."
    }
  ],
  "final": "SEC-101 is in progress."
}
```

An optional `"expect": {"pass": true}` field adds the scorecard line.

```python
def load_traces(path):
    """One JSON object per line. 'expect' is optional and only used for the scorecard."""
    out = []
    for line in open(path):
        if line.strip():
            t = json.loads(line)
            t.setdefault("expect", None)
            out.append(t)
    return out
```

Then the entry point with `--traces`, `--sample` and `--seed`:

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--traces", help="JSONL file of recorded traces (default: built-in mock traces)")
    ap.add_argument("--think", action="store_true", help="judge reasons first; reasoning goes in the report")
    ap.add_argument("--sample", type=float, default=1.0, help="audit this random fraction of traces (0-1)")
    ap.add_argument("--seed", type=int, help="seed for --sample")
    ap.add_argument("--report", default="audit_report.md", help="markdown report path")
    ap.add_argument("--out", default="audit_results.jsonl", help="per-trace results (JSONL)")
    ap.add_argument("--judge-url", default=JUDGE_URL)
    args = ap.parse_args()
    if not 0 < args.sample <= 1:
        sys.exit("--sample must be greater than 0 and at most 1")

    judge = LlamaServer(args.judge_url, JUDGE_TOKENIZER_ID)
    if not judge.healthy():
        sys.exit(f"llama-server not reachable for the judge: {args.judge_url}")

    traces = load_traces(args.traces) if args.traces else TRACES
    if args.sample < 1:
        random.seed(args.seed)
        traces = random.sample(traces, max(1, round(len(traces) * args.sample)))

    results = audit_all(judge, traces, args.think)
    write_report(args.report, results, traces, args)
    write_results(args.out, results)
    print(f"Report written to {args.report}; per-trace results to {args.out}.")
```

---

## Run it

```bash
python 08-trace-audit/work/audit.py --sample 0.5 --seed 1
```

About half the traces are audited, chosen at random. The seed makes the choice
repeatable, so you can talk about the same run twice.

## Before you run real traces

- **Edit `POLICY`** to match your actual policy, and test the wording on traces
  you know are good and bad
- **Check the transcript length.** The servers run with `-c 8192`, so a very
  long trace may not fit. Truncate tool results or raise the context size.
  Quality can drop as traces grow, even when they fit
- **Redact sensitive data.** Traces and reports can contain secrets, personal
  data and customer content
- **Keep the reports.** They are an audit trail you did not have before

## Check your understanding

1. You audit a 10% sample and nothing fails. What can you say about the other
   90%?
2. How would you choose the sample so a rare, risky tool is never skipped?

Checkpoint: `solution/step_05_sample.py`.

## Next

Limits and exercises: [06-wrap-up.md](./06-wrap-up.md).

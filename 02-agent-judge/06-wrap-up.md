# Lesson 6: Wrap Up

## What you built

An agent with mock tools and a judge at four boundaries, in about 300 lines. You
saw the same attacks land when unguarded and get stopped when guarded, and you
saw that the stopping gate is not always the first one to notice.

| Gate        | Criterion                   | Kind                | Flags on |
| ----------- | --------------------------- | ------------------- | -------- |
| Input       | Jailbreak                   | Pre-baked, risk     | `yes`    |
| Tool call   | Function-call hallucination | Pre-baked, risk     | `yes`    |
| Tool call   | Authorized action           | Custom, requirement | `no`     |
| Tool result | Instructions for the AI     | Custom, risk        | `yes`    |
| Output      | No secrets in the answer    | Custom, requirement | `no`     |

## What the full demo adds

The script in [demo/](./demo/README.md) has the same gates and the same flags as
your finished build. What it adds is polish for presenting:

- Timing printed for each verdict, so you can talk about latency
- A presenter guide with a run of show, talking points for each scenario, a
  pre-flight checklist and a plan B
- A scenario structure that makes it easy to add your own

Scenario numbers differ: the demo numbers the hallucinated call as 4 and the
sensitive-data scenario as 5. Yours are the other way round.

## Limits, said out loud

1. **The judge is an LLM too.** Treat it as one layer, not a guarantee
2. **Custom criteria need testing before you trust them.** Chapter 07 shows how
   a model can find the ones that fail
3. **Fail closed.** An unparseable verdict is a flag, not a pass
4. **At 8B this suits spot-checks and monitoring, not strict-latency
   guardrails.** You measured the cost yourself
5. **Quantization.** The accuracy figures on the model card are for the
   full-precision models. These are 4-bit, so verdicts can differ

## Exercises

1. **Write a new criterion.** Add a requirement: "The response does not mention
   internal hostnames." Which gate does it belong at? Which `flag_on` does it
   need?
2. **Break fail-closed on purpose.** Restart only the judge without `--special`
   and run scenario 1. Everything is flagged. Why is that the right failure?
3. **Try to evade the input gate.** Rewrite the jailbreak so the judge says
   `no`. Does the tool-call gate still stop the action?
4. **Measure the cost.** Time scenario 1 unguarded and guarded. How much of the
   guarded time is judge calls?
5. **Compare with the demo.** Run your build and the demo with `--think` on the
   poisoned ticket. Does the judge's reasoning differ between them?

```bash
python 02-agent-judge/demo/agent_judge_demo.py --only 3 --mode guarded --think
```

## Run the demo

If you have not yet, run the finished demo and compare:

```bash
python 02-agent-judge/demo/agent_judge_demo.py
```

The demo guide has the full run of show, talking points and troubleshooting:
[demo/README.md](./demo/README.md).

## Next

The next chapters stand on their own. A good one to take next is
[03-approval-triage](../03-approval-triage/), which asks what happens when a
person must approve what the agent wants to do.

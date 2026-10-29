# Lesson 6: Wrap Up

## What you built

An offline auditor in about 310 lines. It reads recorded runs, asks four
questions about each, locates the first deviating step of a failing run, and
writes a report a person can act on. It can sample traces and read your own.

| Piece      | What your script does                                             |
| ---------- | ----------------------------------------------------------------- |
| Transcript | `render_trace` turns a trace into text, optionally up to step `k` |
| Questions  | Goal, policy, faithful and injection, with the polarity of each   |
| Fail rule  | Goal, policy or faithful violated. Injection is context only      |
| Location   | A step-by-step replay for goal and policy failures                |
| Report     | A markdown table and a JSONL file, with reasoning in think mode   |
| Sampling   | A random fraction, repeatable with a seed                         |

## What the full demo adds

The script in [demo/](./demo/README.md) has the same audit. It adds:

- Timing for each verdict
- A presenter guide with a run of show, talking points, a pre-flight checklist
  and a plan B

## Limitations (say these out loud)

- **The judge reads untrusted text.** A transcript contains tool results, which
  may include injection payloads. Those could try to influence the judge itself.
  Treat the judge as one layer
- **It only knows what you logged.** Missing steps, truncated results or an
  incomplete goal make the audit blind or misleading
- **Policy wording matters.** The policy is part of a prompt and is sensitive to
  phrasing. Test it before relying on it
- **Locating the deviation is a heuristic.** The step-by-step replay can point
  at the wrong step
- **Passing is not proof.** A PASS means the judge found no problem, not that
  the run was safe
- **Tiny, hand-built sample.** Nine traces prove nothing about accuracy, and the
  label for each is our judgment
- **Quantized model.** Verdicts from a 4-bit model may differ from full
  precision
- **Long transcripts strain a small judge.** Quality can drop as traces grow

## Closing points

1. Gates and audits are complementary: gates stop things, audits find what gates
   did not check or could not see
2. The final-message check covers a failure no per-step gate looks at: the
   agent's account of what it did
3. Locating the first deviating step turns a verdict into something a human can
   act on
4. Sample and escalate. An 8B judge is a triage tool here, not an authority
5. Keep the reports. They are an audit trail you did not have before

## Exercises

1. **Add a fifth question.** Write a criterion about the final message, for
   example that it does not repeat a secret from a tool result. Does it fail a
   trace, or is it context?
2. **Attack the judge.** Write a trace whose tool result tells an auditor to
   mark the run as safe. What does your judge do?
3. **Find the context limit.** Make a trace long enough that the transcript no
   longer fits in `-c 8192`. What happens to the verdict?
4. **Make it a gate for CI.** Exit with a non-zero status if any trace in a
   sample fails. Where would you run that?
5. **Compare think and no-think.** Run a clean trace both ways. Which is more
   likely to fail it, and why might that be?

## Where to go from here

You have now built each layer around an agent: gates at run time, human
approvals, tool vetting, least-privilege permissions, criteria compiled from
policy, a red team for the judge, and an after-the-fact audit. None of them is
enough alone. Return to [the workshop overview](../README.md) and think about
which two you would deploy first, and what each one would still miss.

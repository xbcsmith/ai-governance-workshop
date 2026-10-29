# Lesson 6: Wrap Up

## What you built

A triage layer in about 300 lines. Nine pending actions are sorted by four judge
signals and a fixed rule, explained by a model, checked against the action, and
decided by a person. The model never chose a level and never approved anything.

| Rule | What it looks like in your script                      |
| ---- | ------------------------------------------------------ |
| 1    | `level_of` is plain Python over the four signals       |
| 2    | `write_card` returns text. It cannot reach the level   |
| 3    | `print_queue` always prints the action `[verbatim]`    |
| 4    | `verify_card` runs the faithful check on every card    |
| 5    | `record_decisions` asks every time, and logs overrides |

## What the full demo adds

The script in [demo/](./demo/README.md) has the same pipeline. It adds:

- A `--raw` flag that prints the raw queue in one command, so you can show the
  before picture
- A reviewer-workload line: how many items need an individual read versus a
  batch glance. That is a smaller task, **not** a measured time saving
- Timing for the run, and icons for the levels
- A presenter guide with a run of show, talking points, a pre-flight checklist
  and a plan B

## Reading the numbers honestly

1. **Tiny, hand-built queue.** Nine items prove nothing about accuracy, and the
   intended levels are our own judgment
2. **Signals are one judge's opinion.** An item that passes all four signals is
   not proven safe. A miss means a risky item shows as ROUTINE
3. **Wording sensitivity.** Each signal is a prompt, and small rewordings can
   move verdicts
4. **Same model family.** The summarizer and the judge are both Granite, which
   may correlate their blind spots
5. **Quantized models.** Both run as 4-bit GGUFs
6. **Summary verification is not airtight.** A subtle omission can slip through.
   That is why the action is shown verbatim
7. **Routine batches are still a risk.** A real deployment should sample them

Do not claim time saved unless you time it with real reviewers.

## Closing points

1. Approval fatigue is a security problem: a control people stop reading doesn't
   control anything
2. Let AI sort and explain, but derive the level from checks you can inspect
3. Treat the summarizer as an attack surface, because it reads the same
   untrusted text the agent does
4. Show the facts next to the summary, and verify the summary
5. Log overrides. A human approving against a recommendation is exactly the
   event an audit should capture

## Exercises

1. **Add a signal.** Write a requirement criterion such as "The proposed action
   does not delete or overwrite data." Add it to `SIGNALS`. Does `level_of` need
   to change?
2. **Add a tenth item** that is dangerous but whose request matches the action
   exactly, for example the user asks to email a customer list to an outside
   address. Which signals catch it? Which do not?
3. **Move the rule.** Change `level_of` so that `sensitive-data` alone gives
   DENY. Look at over-triage. What did you trade?
4. **Attack the card.** Write a ticket that tries to get the summarizer to hide
   the recipient without saying "routine". Does verification catch it?
5. **Break fail-closed on purpose.** Restart the judge without `--special`. What
   level does everything get, and is that the right failure?

## Next

The runtime and human layers are done. The next chapters go around them:
[04-tool-vetting](../04-tool-vetting/) vets the tools before the agent sees
them, and [05-least-privilege](../05-least-privilege/) shrinks what the agent
may do.

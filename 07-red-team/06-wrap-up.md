# Lesson 6: Wrap Up

## What you built

A red-team harness in about 280 lines. A model attacks the judge in eight
categories and adapts across rounds. The same model writes benign look-alikes so
you measure false positives. Misses are saved, criteria are tightened, and a
replay shows what changed.

| Piece    | What your script does                                                  |
| -------- | ---------------------------------------------------------------------- |
| Attacker | Granite 4.1 8B writes attempts per category, and adapts from round 2   |
| Judge    | The same two risk criteria used at the gates, at version v1 or v2      |
| Controls | Benign tickets and requests, including a hard negative                 |
| Report   | Catch rate per category and round, false positives, a sample of misses |
| Replay   | Recovery, regression and new false positives under changed criteria    |

## What the full demo adds

The script in [demo/](./demo/README.md) has the same loop. It adds:

- Timing for the run
- A presenter guide with a run of show, talking points, a pre-flight checklist
  and a plan B

## Reading the numbers honestly

Do not present these as benchmark results.

- **Small samples.** Defaults are 6 attempts per category per round. A category
  at 83% versus 67% is one or two items
- **Non-deterministic.** The attacker samples at temperature 0.8, so two runs
  differ. `--seed` fixes only which misses are shown, not what the attacker
  writes
- **A weak attacker.** An 8B model writing attacks is not an adaptive human red
  team. A strong result here is not evidence of robustness
- **Same model family.** Attacker and judge both come from IBM Granite, which
  may correlate their blind spots in either direction
- **Quantized models.** Both run as 4-bit GGUFs
- **Attack quality is not checked.** Some generated "attacks" may be too weak or
  garbled to work on a real agent. The script counts them anyway
- **The attacker may refuse or return junk.** The script prints a line when a
  category produced nothing usable, and it drops obvious refusals. Check those
  lines before you quote any rate

## Closing points

1. Hand-written test sets undercount what a guardrail misses. Generate more, and
   re-generate as criteria change
2. Measure both directions: attacks caught **and** benign traffic wrongly
   flagged
3. Every miss becomes a regression test. Every criterion change gets replayed
   before it ships
4. Adaptive attackers are the point. A fixed test set eventually goes stale
5. The judge is still one layer. Least privilege, tool vetting and output checks
   do the rest

## Exercises

1. **Tune v2 on your own misses.** Rewrite `CRITERIA["v2"]` using what you
   actually saw. Replay the full run. What did you gain and what did it cost?
2. **Add a category.** Write a new attack description, such as instructions
   hidden in an attachment name. Which gate does it belong at?
3. **Add a harder negative.** Write a benign category that looks even more like
   an attack. Does the judge flag it?
4. **Make replay a test.** Exit with a non-zero status if any previously caught
   attack is now missed. Where would you run that?
5. **Attack a different gate.** Add an output-gate category and criterion. What
   does the attacker have to write there?

## Next

One chapter left. We have gated a run as it happens. The last chapter reviews
whole runs after the fact: [08-trace-audit](../08-trace-audit/README.md).

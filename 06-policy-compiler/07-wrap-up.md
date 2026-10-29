# Lesson 7: Wrap Up

## What you built

A policy compiler in about 370 lines: it reads a plain-English policy, drafts a
criterion per rule, tests the drafts with a judge, repairs the weak ones, and
hands a review sheet to a person. Only approved criteria are ever applied.

| Step     | What your script does                                               |
| -------- | ------------------------------------------------------------------- |
| Extract  | The compiler splits the policy into rules and picks a gate for each |
| Draft    | One sentence per rule: true when the text complies                  |
| Test     | Compliant and violating examples, written by the compiler           |
| Validate | The judge scores both directions                                    |
| Repair   | A rewrite wins only on fresh tests                                  |
| Review   | `approved: false` until a person says otherwise                     |
| Apply    | Only approved criteria, at the chosen gate                          |

## What the full demo adds

The script in [demo/](./demo/README.md) has the same pipeline. It adds:

- Timing for the run
- A presenter guide with a run of show, talking points, a pre-flight checklist
  and a plan B

Your script does each phase for every rule before the next phase. The demo does
extract, draft, test and validate rule by rule. The results are the same.

## Reading the numbers honestly

Do not present these as accuracy figures.

- **Circular validation.** The same model family writes the criteria, writes the
  tests and judges them. Agreement between them is weaker evidence than it
  looks, and shared blind spots will not show up
- **The tests shape the result.** If the compiler writes easy violations, the
  judge will look good. Add real examples from your own traffic before you
  approve anything
- **Small samples.** Defaults are five compliant and five violating examples per
  rule, so one or two items move a percentage a lot
- **Selection bias in repair.** Choosing the better of old and new on the same
  fresh tests slightly flatters the winner
- **Context-dependent rules.** Rules like "only when the user asks" need the
  user's request in the text being judged
- **Quantized models.** Both run as 4-bit GGUFs
- **The compiler may refuse or produce junk.** The script skips rules with too
  few usable tests and says so

## Closing points

1. Policies are already written in plain English, and criteria can be too. A
   model can do the first draft
2. A draft is not a control. Validate it, then have a person approve it
3. Measure both directions: violations caught and compliant text wrongly flagged
4. Treat criteria like code: version them, review them, retest them when the
   policy changes
5. The tests are the weak link. Real examples beat generated ones

## Exercises

1. **Bring your own policy.** Add a `--policy` file of your own with numbered,
   plainly worded rules. Which rules compile cleanly, and which do not?
2. **Replace the tests.** Write five real examples for one rule by hand and swap
   them in. Does the score change?
3. **Check the gates.** Print the checkpoint the compiler chose for each rule
   and argue with it. What would a wrong choice cost?
4. **Break a criterion.** Edit an approved criterion in `criteria.json` to be
   vague ("The response is appropriate"). What does `--apply` do with obviously
   bad text?
5. **Add a gate filter to compile mode.** Compile only the rules for one
   checkpoint. What would you need to change?

## Next

We have measured a criterion with tests a model wrote. The next chapter asks a
harder question: what does the judge miss when a model writes the attacks?
[07-red-team](../07-red-team/).

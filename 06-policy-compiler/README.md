# Workshop Session: Turn Policy into Reviewable Criteria

## Outline

### Where do criteria come from

In the runtime chapter, the custom criteria ("the response contains no secrets",
"the tool call only does what the user asked") were written by hand. Every team
already has a security policy in plain English. Can a model draft the criteria
from it, can a judge check the drafts, and where does the human fit?

### Compile a policy

A model reads the policy, splits it into rules, picks a checkpoint for each, and
drafts one criterion per rule. It then writes compliant and violating test
cases.

### Validate the drafts

The judge applies each criterion to its tests. Two numbers per rule matter:
violations caught, and compliant text wrongly flagged. Weak criteria can be
rewritten and compared on fresh tests.

### Keep a person in charge

Everything comes out as drafts marked `approved: false`. A person reads the
review sheet, approves what they accept, and only approved criteria are ever
applied.

## Workshop Format

Each lesson explains one idea, then has you add a few lines to a single script
and run it. The first lesson needs no model. Lessons 2 and 3 need the compiler
(the agent server), and lessons 4 to 6 add the judge. A finished checkpoint for
every lesson is in `solution/`. The `demo/` folder has the full demo script for
people who want to run it first and build later.

## Key Learning Objectives

- Explain why every compiled criterion is a requirement (yes means complies)
- Choose the checkpoint where each kind of rule can be enforced
- Measure a criterion in both directions: violations caught, and compliant text
  wrongly flagged
- Compare an old and a rewritten criterion on fresh tests, and say why fresh
- Say why validation with same-family models is weaker evidence than it looks
- Apply only criteria that a person has approved

## Files

| File                                                 | Description                                            |
| ---------------------------------------------------- | ------------------------------------------------------ |
| [00-intro.md](./00-intro.md)                         | The idea and the pipeline                              |
| [01-the-policy.md](./01-the-policy.md)               | The policy, the four gates and the parsers             |
| [02-extract-and-draft.md](./02-extract-and-draft.md) | Rules, a checkpoint for each and a draft criterion     |
| [03-write-the-tests.md](./03-write-the-tests.md)     | Compliant and violating examples for each rule         |
| [04-validate.md](./04-validate.md)                   | Let the judge score each draft                         |
| [05-repair.md](./05-repair.md)                       | Rewrite weak criteria and compare on fresh tests       |
| [06-review-and-apply.md](./06-review-and-apply.md)   | Export for a person, then apply only what they approve |
| [07-wrap-up.md](./07-wrap-up.md)                     | Limits, closing points and exercises                   |
| [solution/](./solution)                              | A runnable checkpoint for each lesson                  |
| [demo/](./demo/README.md)                            | The full demo script and presenter guide               |

## Before you start

Chapter 00 comes first. This chapter reuses the judge from
[02-agent-judge](../02-agent-judge/README.md). Run every command from the
repository root, with `PYTHONPATH` set:

```bash
export PYTHONPATH="$PWD/src"
mkdir -p 06-policy-compiler/work
```

You will work in `06-policy-compiler/work/compiler.py`. Lesson 3 onward takes a
few minutes per run, because the compiler writes a lot of text. Use `--tests 3`
while you build.

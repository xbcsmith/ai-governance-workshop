# Workshop Session: Learn Least Privilege from Audited Traces

## Outline

### The cheapest control

Every control so far tries to catch an agent doing something wrong. The simplest
control is making sure it cannot. But most agents run with whatever permissions
were convenient on day one. This chapter mines logged agent runs for what the
agent legitimately needs, and proposes a much smaller permission set.

### The trap

If the logs contain hijacked or misbehaving runs, learning permissions from them
whitelists the bad behavior. You will build the trap first, on purpose, and
watch a policy learn an attacker's domain as normal. Then you will fix it by
auditing the traces before learning from them.

### The model proposes, rules decide

Let a model propose a policy from the clean usage, then verify it with
deterministic checks: it must cover every clean action, and it must not allow a
probe call that the baseline denies. If it fails, fall back to the baseline.

### A person approves

The log can only say what was normal, not what was right. Flag the exceptions
for a human, measure what a tight policy breaks on unseen legitimate use, and
write a proposal with `approved: false`.

## Workshop Format

Each lesson explains one idea, then has you add a few lines to a single script
and run it. The first two lessons need no model at all. A finished checkpoint
for every lesson is in `solution/`. The `demo/` folder has the full demo script
for people who want to run it first and build later.

## Key Learning Objectives

- Describe a permission policy as data, and test it deterministically
- Use canaries to measure how broad a policy is without labels
- Show how learning from unaudited logs entrenches an attack
- Audit traces with a judge before learning from them
- Verify a model's proposal with rules, and fall back safely
- Name what permissions cannot stop, and what a tight policy costs

## Files

| File                                                         | Description                                         |
| ------------------------------------------------------------ | --------------------------------------------------- |
| [00-intro.md](./00-intro.md)                                 | The idea, the trap and the pipeline                 |
| [01-policies-and-canaries.md](./01-policies-and-canaries.md) | What a policy is, and how to test one               |
| [02-learn-from-the-log.md](./02-learn-from-the-log.md)       | Mine, build a baseline and replay, without an audit |
| [03-audit-first.md](./03-audit-first.md)                     | Filter the traces with a judge                      |
| [04-the-model-proposes.md](./04-the-model-proposes.md)       | Propose with a model, decide with rules             |
| [05-review-and-holdout.md](./05-review-and-holdout.md)       | Hold-out, human review and the output files         |
| [06-wrap-up.md](./06-wrap-up.md)                             | Limits, closing points and exercises                |
| [solution/](./solution)                                      | A runnable checkpoint for each lesson               |
| [demo/](./demo/README.md)                                    | The full demo script and presenter guide            |

## Before you start

Chapter 00 comes first. This chapter reuses the judge from
[02-agent-judge](../02-agent-judge/README.md). Lessons 3 to 5 need the judge
server, and lessons 4 and 5 also use the agent server as the proposer. Run every
command from the repository root, with `PYTHONPATH` set:

```bash
export PYTHONPATH="$PWD/src"
mkdir -p 05-least-privilege/work
```

You will work in `05-least-privilege/work/policy.py`.

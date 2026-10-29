# Workshop Session: Triage Agent Approvals for Humans

## Outline

### Why approvals fail

Human-in-the-loop approval is a common control for agent actions, and it fails
in a predictable way: the queue grows, every request looks alike, and reviewers
start clicking approve. We call it approval fatigue, and it makes the control
stop controlling anything.

### Help the reviewer without replacing them

Build a triage layer that sorts a queue of nine pending actions, groups the
routine ones, and writes a short card for each risky one. The risk level comes
from judge checks and a fixed rule that you can inspect. The model only writes
the explanation.

### Defend the summarizer

The summarizer reads the same untrusted text the agent does, so it is an attack
surface too. Verify each card against the action it describes, always show the
action verbatim, and watch a scripted lying card fail the check.

### Keep the decision human

Walk the risky items one at a time, record each decision, and log every approval
that goes against a recommendation.

## Workshop Format

Each lesson explains one idea, then has you add a few lines to a single script
and run it. The first lesson needs no model at all. A finished checkpoint for
every lesson is in `solution/`. The `demo/` folder has the full demo script for
people who want to run it first and build later.

## Key Learning Objectives

- Explain why a risk level must come from checks you can inspect, not from model
  prose
- Combine four yes/no judge signals into DENY, REVIEW or ROUTINE with a fixed
  rule
- Write a card with a model, and keep it from changing the level
- Verify a summary against the action it describes
- Tell under-triage from over-triage, and say which one is dangerous
- Log human decisions, including overrides, for audit

## Files

| File                                                   | Description                                        |
| ------------------------------------------------------ | -------------------------------------------------- |
| [00-intro.md](./00-intro.md)                           | Approval fatigue, the design rules and the queue   |
| [01-the-queue.md](./01-the-queue.md)                   | Build the mock queue and see what reviewers see    |
| [02-signals-and-levels.md](./02-signals-and-levels.md) | Four judge signals and a fixed level rule          |
| [03-cards.md](./03-cards.md)                           | Let the model write the explanation, and only that |
| [04-verify-the-card.md](./04-verify-the-card.md)       | Check the card against the action                  |
| [05-the-human-decides.md](./05-the-human-decides.md)   | Record decisions and log overrides                 |
| [06-wrap-up.md](./06-wrap-up.md)                       | Limits, closing points and exercises               |
| [solution/](./solution)                                | A runnable checkpoint for each lesson              |
| [demo/](./demo/README.md)                              | The full demo script and presenter guide           |

## Before you start

Chapter 00 and the runtime chapter,
[02-agent-judge](../02-agent-judge/README.md), come first, because this chapter
reuses the judge you built there. Both servers must be running. Run every
command from the repository root, with `PYTHONPATH` set:

```bash
export PYTHONPATH="$PWD/src"
mkdir -p 03-approval-triage/work
```

You will work in `03-approval-triage/work/triage.py`.

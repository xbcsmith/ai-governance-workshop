# Workshop Session: Red-Team the Judge

## Outline

### The harder question

In the runtime chapter you asked whether the judge catches attacks **you**
wrote. You wrote them knowing what the judge looks for, so of course some got
caught. This chapter asks what the judge misses when **a model** writes the
attacks, and keeps adapting.

### Build the red team

Granite 4.1 8B plays the attacker. Granite Guardian 4.1 8B is the judge, sitting
at two of the runtime gates: the input gate (user messages) and the tool-result
gate (ticket bodies the agent reads). Every attack has the same toy goal: get an
assistant to read a fake secrets file and email it to an outside address.
Nothing is executed. The script only tests the judge.

### Measure both directions

Count the attacks caught and missed in each category. Have the same attacker
write benign look-alikes, so you also count the harmless text that was wrongly
flagged. A guardrail that flags everything is an outage.

### Close the loop

Save the misses, tighten a criterion, and replay them. Then run a fresh adaptive
attack against the new criterion, because recovering old misses proves little.

## Workshop Format

Each lesson explains one idea, then has you add a few lines to a single script
and run it. The first lesson needs no model. Lessons 2 to 5 need the attacker
(the agent server), and lessons 3 to 5 add the judge. A finished checkpoint for
every lesson is in `solution/`. The `demo/` folder has the full demo script for
people who want to run it first and build later.

## Key Learning Objectives

- Explain why a hand-written test set undercounts what a guardrail misses
- Measure a guardrail in both directions: attacks caught and benign text flagged
- Let an attacker adapt to what was caught, without seeing the judge's reasoning
- Turn every miss into a regression test, and replay it when criteria change
- Say why recovering old misses is not proof of robustness
- Say why an 8B red team is not a benchmark

## Files

| File                                                               | Description                                  |
| ------------------------------------------------------------------ | -------------------------------------------- |
| [00-intro.md](./00-intro.md)                                       | The idea, the loop and the scope             |
| [01-what-the-attacker-writes.md](./01-what-the-attacker-writes.md) | The categories, the controls and the prompts |
| [02-the-attacker.md](./02-the-attacker.md)                         | Let a model write the attacks                |
| [03-judge-the-attacks.md](./03-judge-the-attacks.md)               | Catch rate and false positives               |
| [04-adapt.md](./04-adapt.md)                                       | Round two: the attacker sees what was caught |
| [05-tighten-and-replay.md](./05-tighten-and-replay.md)             | Replay misses, then attack the new criteria  |
| [06-wrap-up.md](./06-wrap-up.md)                                   | Limits, closing points and exercises         |
| [solution/](./solution)                                            | A runnable checkpoint for each lesson        |
| [demo/](./demo/README.md)                                          | The full demo script and presenter guide     |

## Before you start

Chapter 00 comes first. This chapter reuses the judge from
[02-agent-judge](../02-agent-judge/README.md). Run every command from the
repository root, with `PYTHONPATH` set:

```bash
export PYTHONPATH="$PWD/src"
mkdir -p 07-red-team/work
```

You will work in `07-red-team/work/redteam.py`. The default run takes several
minutes. Use `--per-category 3` while you build.

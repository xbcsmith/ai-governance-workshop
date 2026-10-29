# Workshop Session: Guard an Agent with a Judge

## Outline

### Understand the four gates

A tool-calling agent can be attacked through the user's message, through data it
reads, through its own tool calls, and through what it says. We place a judge at
each of these four boundaries.

### Build the judge

Write a small function that asks Granite Guardian a yes or no question, reads
the verdict, and fails closed when it cannot.

### Build the agent, then guard it

Build an unguarded agent with mock tools and watch an attack land. Then add the
input and tool-call gates, and finally the tool-result and output gates, running
the same scenarios each time.

### Catch bad calls and read the reasoning

Add a second pre-baked check for hallucinated tool calls, which needs the tool
definitions passed to the judge. Then turn on think mode so the judge explains
its verdicts, and learn how far to trust that explanation.

### See how it fails

Close with the limits: the judge is an LLM, custom criteria need testing, and
latency is a real cost.

## Workshop Format

Each lesson explains one idea, then has you add a few lines to a single script
and run it. A finished checkpoint for every lesson is in `solution/`, so you can
catch up at any point. The `demo/` folder has the full demo script for people
who want to run it first and build later.

## Key Learning Objectives

- Place a judge at the input, tool-call, tool-result and output gates
- Write a pre-baked and a custom criterion, and read their polarity correctly
- Show why a single gate is not enough by comparing unguarded and guarded runs
- Catch a hallucinated tool call with a pre-baked check, and explain why the
  judge needs the tool definitions
- Use think mode to read the judge's reasoning, and say what it does not prove
- State at least three limits of an LLM judge

## Files

| File                                                                       | Description                                           |
| -------------------------------------------------------------------------- | ----------------------------------------------------- |
| [00-intro.md](./00-intro.md)                                               | The four gates and what we build                      |
| [01-ask-the-judge.md](./01-ask-the-judge.md)                               | Build the judge function                              |
| [02-the-agent.md](./02-the-agent.md)                                       | Build an unguarded agent and watch the attack land    |
| [03-input-and-call-gates.md](./03-input-and-call-gates.md)                 | Guard the input and the tool call                     |
| [04-result-and-output-gates.md](./04-result-and-output-gates.md)           | Guard the tool result and the output                  |
| [05-hallucination-and-think-mode.md](./05-hallucination-and-think-mode.md) | Catch a bad tool call, and read the judge's reasoning |
| [06-wrap-up.md](./06-wrap-up.md)                                           | Limits, exercises and the full demo                   |
| [solution/](./solution)                                                    | A runnable checkpoint for each lesson                 |
| [demo/](./demo/README.md)                                                  | The full demo script and presenter guide              |

## Before you start

Both servers must be running and `python src/check_setup.py` must pass. See
[00-prereqs](../00-prereqs/README.md). Run every command from the repository
root, with `PYTHONPATH` set:

```bash
export PYTHONPATH="$PWD/src"
```

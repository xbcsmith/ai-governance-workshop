# Workshop Session: Audit Complete Agent Traces

## Outline

### Gates and audits

The runtime chapter gated each step while the agent ran. This chapter reviews
**whole recorded runs afterwards**. You will build an auditor that reads a trace
(a goal, the tool calls with their results, and the final message) and decides
whether the run was sound.

### Why audit when you already have gates

1. Gates only judge what they see in the moment. A sequence of individually
   plausible steps can still drift from the user's goal
2. Per-step gates do not check whether the agent's **final message matches what
   the tools returned**. An agent can report success after an error
3. An 8B judge suits spot-checks and monitoring better than strict-latency
   gating in every request path. Sampling recorded traces fits that, and leaves
   an audit trail

### Four questions and a location

The judge answers four questions about each transcript, then replays failing
traces one step at a time to find the first step that deviates. The output is a
report a reviewer, auditor or on-call engineer can read.

## Workshop Format

Each lesson explains one idea, then has you add a few lines to a single script
and run it. The first lesson needs no model. Only the judge is needed after
that: no agent runs, because the traces are hand-written and no tools execute. A
finished checkpoint for every lesson is in `solution/`. The `demo/` folder has
the full demo script for people who want to run it first and build later.

## Key Learning Objectives

- Say what an audit finds that a per-step gate cannot
- Read the four verdicts correctly, including the one that is only context
- Locate the first deviating step of a failing run, and say why it is a
  heuristic
- Produce a report that a person can act on
- Sample traces, and say why passing is not proof

## Files

| File                                                   | Description                                  |
| ------------------------------------------------------ | -------------------------------------------- |
| [00-intro.md](./00-intro.md)                           | Why audit after the fact, and the plan       |
| [01-the-traces.md](./01-the-traces.md)                 | The policy, nine traces and the transcript   |
| [02-four-questions.md](./02-four-questions.md)         | Goal, policy, faithful and injection         |
| [03-find-the-deviation.md](./03-find-the-deviation.md) | Replay a failing run one step at a time      |
| [04-the-report.md](./04-the-report.md)                 | The artifact a reviewer reads                |
| [05-sample-and-scale.md](./05-sample-and-scale.md)     | Sampling, your own traces and context limits |
| [06-wrap-up.md](./06-wrap-up.md)                       | Limits, closing points and exercises         |
| [solution/](./solution)                                | A runnable checkpoint for each lesson        |
| [demo/](./demo/README.md)                              | The full demo script and presenter guide     |

## Before you start

Chapter 00 comes first. This chapter reuses the judge from
[02-agent-judge](../02-agent-judge/README.md). You need only the judge server.
Run every command from the repository root, with `PYTHONPATH` set:

```bash
export PYTHONPATH="$PWD/src"
mkdir -p 08-trace-audit/work
```

You will work in `08-trace-audit/work/audit.py`.

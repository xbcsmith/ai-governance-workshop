# Workshop Session: When One Mistake Becomes Many

**OWASP Agentic Top 10 (2026):** ASI08 · ASI01 · ASI02

## Outline

### One ticket, many restarts

Build a small pipeline of three stages: intake reads a ticket, a planner turns
its target into a list of services, an executor restarts them, and monitoring
files new tickets about what broke. Measure how far one ticket spreads, with no
guard and no model.

### Guard the boundaries

Put an exact contract between intake and the planner, then add scope, a budget,
provenance and a circuit breaker. A table runs every starting ticket under every
combination, so you can see which rule stops what, and which one stops nothing.

### Put a real agent at the front

Give the intake stage to Granite and run five tickets with and without the
rules, including a poisoned one and a legitimate one that has to wait for a
human. Nothing is restarted.

### A judge for drift

A valid work order for the wrong service passes every rule. Score a judge on 26
pairs of ticket and order, and join it to the rules so it can only hold a
decision, never lower one.

## Workshop Format

Each lesson explains one idea, then has you add a few lines to a single script
and run it. The first three lessons need no model at all. A finished checkpoint
for every lesson is in `solution/`. The `demo/` folder has the full demo script
for humans who want to run it first and build later.

## Key Learning Objectives

- Name the three ways a mistake grows in a chain: amplification, feedback and a
  trust chain
- Explain why every stage can look fine while the loop is failing
- Write a contract between two stages as a list of what is allowed
- Say what a budget, a scope rule, provenance and a circuit breaker each limit,
  and which failure each one misses
- Tell a rule that watches requests from one that watches effects
- Combine rules so the strictest decision wins and the judge can only add a hold
- Name what a judge can check (that an order matches a ticket) and what it
  cannot (that the ticket is true)

## OWASP Agentic Top 10 mapping

Tags for this chapter, from the
[OWASP Top 10 for Agentic Applications 2026](../01-intro/00-intro.md#owasp-top-10-for-agentic-applications-2026).
Rows are listed in order of how central the risk is to the chapter.

| ID    | Risk                         | How this chapter relates                                                                                                                                              |
| ----- | ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ASI08 | Cascading Failures           | The core of the chapter. One wrong decision is amplified by the planner and fed back by monitoring. A contract, a budget, provenance and a circuit breaker contain it |
| ASI01 | Agent Goal Hijack            | Poisoned ticket text makes the intake agent file a work order for production. It is the way in, and the cascade is what it does with it                               |
| ASI02 | Tool Misuse and Exploitation | A legitimate restart tool is used far beyond its purpose by one wildcard. The budget and scope rules are least privilege applied to a run                             |

## Files

| File                                                                 | Description                                             |
| -------------------------------------------------------------------- | ------------------------------------------------------- |
| [00-intro.md](./00-intro.md)                                         | Three ways a mistake grows, and the plan                |
| [01-the-pipeline.md](./01-the-pipeline.md)                           | A fleet, three stages and a measure of the cascade      |
| [02-the-contract.md](./02-the-contract.md)                           | An exact check between intake and the planner           |
| [03-budget-and-breaker.md](./03-budget-and-breaker.md)               | Scope, budget, provenance and a circuit breaker         |
| [04-the-agent.md](./04-the-agent.md)                                 | Granite as the intake agent, with and without the rules |
| [05-the-judge-at-the-boundary.md](./05-the-judge-at-the-boundary.md) | A judge for drift, and the layered gate                 |
| [06-wrap-up.md](./06-wrap-up.md)                                     | Limits, closing points and exercises                    |
| [solution/](./solution)                                              | A runnable checkpoint for each lesson                   |
| [demo/](./demo/README.md)                                            | The full demo script and presenter guide                |

## Before you start

Chapter 00 comes first. This chapter reuses the judge from
[02-agent-judge](../02-agent-judge/README.md), and builds on the ideas in
[09-code-execution](../09-code-execution/README.md) (exact rules first, the
judge only stricter) and [10-agent-messaging](../10-agent-messaging/README.md).
Lessons 1 to 3 need no server. Lesson 4 needs the agent, and lesson 5 needs the
judge and then the agent. Run every command from the repository root, with
`PYTHONPATH` set:

```bash
export PYTHONPATH="$PWD/src"
mkdir -p 11-cascading-failures/work
```

You will work in `11-cascading-failures/work/pipeline.py`.

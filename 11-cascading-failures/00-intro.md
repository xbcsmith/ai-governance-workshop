# When One Mistake Becomes Many

## Overview

Every chapter so far asked whether a single decision was safe. This one asks
what happens to a decision that is wrong **after** it has been made. In a chain
of agents and automation, a wrong decision does not stay in place: the next
stage trusts it, multiplies it, acts on it, and sometimes feeds its results back
into the start.

That is the risk OWASP calls **ASI08, Cascading Failures**: one fault or bad
decision spreads through a chain of agents and systems, and the damage grows at
every step. This chapter builds a small pipeline, watches one ticket turn into
twenty restarts, and adds the controls that stop it.

---

## Three ways a mistake grows

| Mechanism     | What happens                                                       | Example in this chapter                                       |
| ------------- | ------------------------------------------------------------------ | ------------------------------------------------------------- |
| Amplification | One field is expanded into many actions by a later stage           | One work order for `stg-*` becomes eight restarts             |
| Feedback      | The pipeline's own actions create new tickets that it then acts on | A restart makes dependents fail, and monitoring files tickets |
| Trust chain   | Each stage assumes the one before already checked                  | The executor restarts whatever the planner lists              |

None of them needs an attacker. A legitimate ticket to restart one service that
others depend on is enough to see the second one. An attacker who can plant one
line in one ticket gets all three.

---

## The catch

**Every stage looks fine by itself.**

The intake agent filed a work order that matches the ticket. The planner
expanded the target the way it was built to. The executor restarted what it was
told to restart. Monitoring reported real health-check failures. No single log
line says "this is wrong". The failure is in the shape of the whole loop, and
that is where the controls have to look.

So we put a control at each boundary, and each one checks something the others
cannot see.

---

## What we build

```text
   ticket ──► INTAKE ──► work order ──► PLANNER ──► services ──► EXECUTOR ──► restarts
     ▲        (agent)         │          (expands)                              │
     │                        │                                                 │
     │              1. CONTRACT: one known action, one known service            │
     │              2. SCOPE: production and critical services need a human    │
     │              3. BUDGET: only so many restarts per run                    │
     │              4. PROVENANCE: do not act on tickets we caused              │
     │              5. JUDGE: does the order match the ticket? (guess)          │
     │                                                                          │
     └─────────── MONITORING files tickets about what broke ◄───────────────────┘
                              6. CIRCUIT BREAKER: stop the line when a restart makes things worse
```

Five rules are exact. The sixth is a guess, so, as in the last two chapters, it
can only make a decision stricter. The decision has three outcomes, and the
strictest one wins:

| Decision | Meaning                          |
| -------- | -------------------------------- |
| `block`  | Refused. The order does not run  |
| `review` | Held for a human. It has not run |
| `allow`  | Nobody objected                  |

Most of the rules are about **limiting the blast radius**: how much can go wrong
if every other check fails. A control that prevents the first mistake is better.
A control that caps the cost of the mistake you did not prevent is the one that
helps when you are wrong.

---

## The fleet

The fleet is a graph of twelve services in a Python dictionary. A restart adds a
name to a list, monitoring is a function that creates tickets from the graph,
and the pipeline is a thirty-line loop. Nothing touches a network.

Because the graph has no cycles, every cascade here settles by itself. A real
system can loop for as long as something keeps retrying, which is why the
circuit breaker exists.

---

## The plan

| Lesson | What you build                                                         | Needs             |
| ------ | ---------------------------------------------------------------------- | ----------------- |
| 1      | The pipeline, and a measure of how far one ticket spreads              | No model          |
| 2      | A contract between intake and the planner                              | No model          |
| 3      | Scope, a budget, provenance and a circuit breaker, alone and together  | No model          |
| 4      | Granite as the intake agent, five tickets, with and without controls   | Agent             |
| 5      | A judge that checks the order against the ticket, and the layered gate | Judge, then agent |

## Next

Start with the part that needs no model:
[01-the-pipeline.md](./01-the-pipeline.md).

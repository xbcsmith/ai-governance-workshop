# Lesson 3: Budget, Scope, Provenance and a Breaker

## Overview

The contract checks what an order **says**. It cannot tell that a perfectly
valid order is one too many. In this lesson you add four more rules, and a table
that runs every start ticket under every combination, so you can see which rule
stops what.

### What you will learn

- What each rule limits, and which failure it is for
- Why a rule that watches **effects** catches things a rule that watches
  **requests** cannot
- How to combine rules so the strictest decision wins
- What each rule costs: legitimate work that waits for a human

---

## Four rules

Each rule has the same shape: it takes the ticket, the order, the plan (the list
of services the planner made) and the run's state, and returns a decision and
reasons.

| Rule       | Watches                    | Decision | What it stops                                                   |
| ---------- | -------------------------- | -------- | --------------------------------------------------------------- |
| Scope      | The services in the plan   | review   | Production and critical services are never restarted unattended |
| Provenance | Where the ticket came from | review   | A ticket our own action caused is not acted on automatically    |
| Budget     | How much this run has done | review   | A run restarts at most three services on its own                |
| Breaker    | What our actions caused    | block    | When a restart makes two or more new alerts, the line stops     |

The first three look at **requests**. The circuit breaker looks at **effects**:
it does not care whether the request was reasonable, only whether doing it made
things worse. That matters because the failures nobody thought of are the ones
no request-side rule describes.

`combine` runs every rule and keeps the strictest decision, in the order
`allow`, `review`, `block`. A rule can raise a decision and never lower one,
which is the same principle the judge will follow in lesson 5.

Add this to the end of `pipeline.py`, above the main block:

```python
BUDGET = 3           # most restarts one run may do on its own
BREAKER_ALERTS = 2   # a restart that raises this many new alerts trips the circuit breaker
RANK = {"allow": 0, "review": 1, "block": 2}


def contract_rule(item, order, plan, state):
    """Exact: the work order is not the shape we expect."""
    reasons = check_order(order)
    return ("block", reasons) if reasons else ("allow", [])


def scope_rule(item, order, plan, state):
    """Production and critical services always need a human."""
    reasons = []
    if any(FLEET[name]["env"] == "prod" for name in plan):
        reasons.append("production changes need a human")
    if any(FLEET[name]["critical"] for name in plan):
        reasons.append("a critical service needs a human")
    return ("review", reasons) if reasons else ("allow", [])


def provenance_rule(item, order, plan, state):
    """A ticket that our own action caused is not acted on automatically. This breaks the loop."""
    if item.get("caused_by_pipeline"):
        return "review", ["this ticket was caused by our own earlier action"]
    return "allow", []


def budget_rule(item, order, plan, state):
    """One run may only restart so many services on its own. This caps the blast radius."""
    if len(state["restarted"]) + len(plan) > BUDGET:
        return "review", [f"it would take this run past its budget of {BUDGET} restarts"]
    return "allow", []


def breaker_rule(item, order, plan, state):
    """When the breaker is open, nothing runs until a human resets it."""
    if state["open"]:
        return "block", ["the circuit breaker is open"]
    return "allow", []


def trip_breaker(state, target, alerts):
    """Called after every restart. A restart that makes things this much worse stops the line."""
    if len(alerts) >= BREAKER_ALERTS:
        state["open"] = True


def combine(*rules):
    """Run every rule and keep the strictest decision. A rule can raise a decision, never lower it."""
    def gate(item, order, plan, state):
        decision, reasons = "allow", []
        for rule in rules:
            verdict, why = rule(item, order, plan, state)
            reasons += why
            if RANK[verdict] > RANK[decision]:
                decision = verdict
        return decision, reasons
    return gate
```

---

## Every rule, every ticket

`ablation` runs each start ticket under each set of controls and prints the
number of restarts, a `PROD` flag if production was touched, and how many orders
were held.

```python
# Each row switches on more controls. observe is what the circuit breaker listens with.
CONFIGS = [
    ("no controls", None, None),
    ("contract", combine(contract_rule), None),
    ("scope (prod, critical)", combine(scope_rule), None),
    ("budget", combine(budget_rule), None),
    ("provenance", combine(provenance_rule), None),
    ("circuit breaker", combine(breaker_rule), trip_breaker),
    ("all five", combine(contract_rule, scope_rule, provenance_rule, budget_rule, breaker_rule), trip_breaker),
]


def ablation(configs=None, starts=None):
    """Run every start ticket under every set of controls. Print restarts, and a P for production."""
    configs, starts = configs or CONFIGS, starts or START
    print(f"\n{'controls':<26}" + "".join(f"{label[:22]:<24}" for label, _ in starts))
    matrix = {}
    for name, gate, observe in configs:
        cells = []
        for label, first in starts:
            o = outcome(run_pipeline([first], scripted_intake, gate=gate, observe=observe, verbose=False))
            cells.append(f"{o['restarts']} restarts{' PROD' if o['prod'] else ''}, held {o['held']}")
        print(f"{name:<26}" + "".join(f"{cell:<24}" for cell in cells))
        matrix[name] = cells
    return matrix
```

---

## Run it

Replace the main block. With no arguments it prints the table, and `--only`
shows a single start ticket, step by step, with all five rules:

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", type=int, help="show one start ticket step by step with all five controls (1-based)")
    args = ap.parse_args()

    if args.only:
        label, first = START[args.only - 1]
        print(f"{label.upper()}: {first['text']}")
        gate = combine(contract_rule, scope_rule, provenance_rule, budget_rule, breaker_rule)
        state = run_pipeline([first], scripted_intake, gate=gate, observe=trip_breaker)
        print_outcomes([(label, outcome(state))])
        for ticket_id, decision, reasons in state["held"]:
            print(f"   held {ticket_id}: {decision} ({'; '.join(reasons)})")
    else:
        ablation()
```

```bash
python 11-cascading-failures/work/pipeline.py
python 11-cascading-failures/work/pipeline.py --only 2
```

---

## What to look for

Restarts, with the number of held orders after a comma:

| Controls        | Leaf | `stg-api` | `stg-db`  | `stg-*`   | `prod-*`             |
| --------------- | ---- | --------- | --------- | --------- | -------------------- |
| No controls     | 1    | 3         | 6         | 20        | 6 (**production**)   |
| Contract        | 1    | 3         | 6         | 0, held 1 | 0, held 1            |
| Scope           | 1    | 3         | 0, held 1 | 0, held 1 | 0, held 1            |
| Budget          | 1    | 3         | 3, held 3 | 0, held 1 | 0, held 1            |
| Provenance      | 1    | 1, held 2 | 1, held 3 | 8, held 8 | 4 (**prod**), held 2 |
| Circuit breaker | 1    | 1, held 2 | 1, held 3 | 3, held 6 | 6 (**production**)   |
| All five        | 1    | 1, held 2 | 0, held 1 | 0, held 1 | 0, held 1            |

- **No rule stops everything on its own.** The contract stops the wildcards and
  none of the cascade. Provenance stops the cascade and lets the human's
  wildcard run: eight restarts, then it holds the eight aftershocks. The circuit
  breaker stops the staging wildcard after three restarts, and **does not stop
  the production wildcard at all**: no single production restart raises two
  alerts, so the breaker never trips and `prod-api` restarts twice.
- **Provenance and the breaker each break the feedback loop,** from different
  directions. Provenance needs monitoring that can say which alerts our change
  caused. The breaker needs nothing but a count. Having both means one failing
  does not reopen the loop.
- **The budget caps the damage when the others miss it.** On `stg-db` it lets
  three restarts through and holds the rest.
- **All five stop everything dangerous here,** and the legitimate tickets pay
  for it. The legitimate `stg-db` ticket waits for a human. The legitimate
  `stg-api` ticket gets its restart, and the two follow-up alerts, which were
  only noise this time, go to a human too.

That last cost is the real trade-off. If every legitimate critical restart
waits, the humans who approve them will begin to click through, which is chapter
03's warning. The cure is a better scope rule, not a missing one.

Checkpoint: `solution/step_03_budget_and_breaker.py`.

## Next

Put a real model at the front: [04-the-agent.md](./04-the-agent.md).

# Lesson 1: The Pipeline

## Overview

Before any control there is a pipeline to measure. You will build a fleet, the
three stages that act on it, and a stand-in for the intake agent that does
exactly what each ticket says. Then you will feed it five tickets and count what
happens. This lesson needs no model.

### What you will learn

- How one field in one work order becomes many actions
- How a pipeline's own actions come back as new input
- What numbers describe a cascade: restarts, services, rounds and what is left
- Why the first measurement should be of the pipeline with nothing guarding it

---

## Create the file

Create `11-cascading-failures/work/pipeline.py`. Run every command in this
chapter from the repository root. Start with the imports:

```python
import argparse
import re
```

---

## The fleet

Twelve services, eight in staging and four in production. Each lists what it
depends on. Two are marked `critical`, in each environment: the authentication
service and the database.

`dependents` answers "what stops being healthy while this restarts". `expand` is
**stage 2, the planner**. It turns the target in a work order into the list of
services to act on. That one function is where the amplification lives: a name
is one service, `stg-*` is every service that starts with `stg-`, and `all` is
the whole fleet.

`alert_tickets` is monitoring. After a restart, each service that depends on it
files a ticket. The ticket says: "Restart" followed by the name of the affected
service. Real alerts are less direct, but a pipeline that treats an alert as a
request to act is easy to build and easy to find in the wild.

```python
# Twelve services. "deps" lists what each one needs to be healthy.
FLEET = {
    "stg-proxy":   {"env": "staging", "deps": [], "critical": False},
    "stg-auth":    {"env": "staging", "deps": [], "critical": True},
    "stg-db":      {"env": "staging", "deps": [], "critical": True},
    "stg-queue":   {"env": "staging", "deps": [], "critical": False},
    "stg-api":     {"env": "staging", "deps": ["stg-auth", "stg-db"], "critical": False},
    "stg-web":     {"env": "staging", "deps": ["stg-api", "stg-proxy"], "critical": False},
    "stg-billing": {"env": "staging", "deps": ["stg-api", "stg-db"], "critical": False},
    "stg-worker":  {"env": "staging", "deps": ["stg-queue", "stg-db"], "critical": False},
    "prod-proxy":  {"env": "prod", "deps": [], "critical": False},
    "prod-auth":   {"env": "prod", "deps": [], "critical": True},
    "prod-db":     {"env": "prod", "deps": [], "critical": True},
    "prod-api":    {"env": "prod", "deps": ["prod-auth", "prod-db"], "critical": False},
}


def dependents(service: str):
    """The services that stop being healthy while this one restarts."""
    return [name for name, info in FLEET.items() if service in info["deps"]]


def expand(target: str):
    """Stage 2, the planner: turn the target in a work order into the list of services to restart.

    A name means one service. "stg-*" means every service that starts with "stg-". "all" and "*"
    mean the whole fleet, and a comma makes a list. One field can become many actions here.
    """
    target = str(target).strip()
    if target in FLEET:
        return [target]
    if target in ("all", "*"):
        return list(FLEET)
    if target.endswith("*"):
        return [name for name in FLEET if name.startswith(target[:-1])]
    if "," in target:
        return [name for part in target.split(",") for name in expand(part)]
    return []


def ticket(ticket_id: str, text: str, caused_by_pipeline: bool = False) -> dict:
    return {"id": ticket_id, "text": text, "caused_by_pipeline": caused_by_pipeline}


def alert_tickets(target: str, counter: int):
    """What monitoring files after a restart: one ticket for every service that depends on it.

    The tickets say they were caused by us. Real monitoring has to work this out by linking
    alerts to the change that preceded them.
    """
    return [ticket(f"alert-{counter + i}",
                   f"ALERT: {name} is failing its health check after {target} restarted. Restart {name}.",
                   caused_by_pipeline=True)
            for i, name in enumerate(dependents(target), 1)]
```

---

## The three stages in a loop

`run_pipeline` is the whole system. Each round, intake reads every ticket in the
queue, the planner expands the target, and the executor restarts each service.
The restarts file new tickets, which form the next round's queue.

The loop has a hard stop at six rounds. That limit is ours, and a real system
that depends on one is already in trouble.

It takes two optional hooks that stay empty in this lesson. `gate` will decide
whether an order may run, and `observe` is how a circuit breaker will watch the
effects.

```python
def run_pipeline(first_tickets, intake, gate=None, observe=None, max_rounds=6, verbose=True):
    """Three stages in a loop: intake reads a ticket, the planner expands it, the executor restarts.

    intake(ticket) -> a work order, or None
    gate(ticket, order, plan, state) -> (decision, reasons): allow, review or block
    observe(state, target, alerts) is called after every restart. A circuit breaker uses it.
    The pipeline's own side effects come back as new tickets, so the loop can feed itself.
    """
    state = {"restarted": [], "held": [], "open": False, "rounds": 0, "alerts": 0, "left": 0}
    queue = list(first_tickets)
    for round_no in range(1, max_rounds + 1):
        if not queue:
            break
        state["rounds"] = round_no
        next_queue = []
        for item in queue:
            order = intake(item)
            if order is None:
                if verbose:
                    print(f"   round {round_no} {item['id']:<9} no work order")
                continue
            plan = expand(order.get("target", ""))
            decision, reasons = ("allow", []) if gate is None else gate(item, order, plan, state)
            if verbose:
                note = f" ({'; '.join(reasons[:2])})" if reasons else ""
                print(f"   round {round_no} {item['id']:<9} {order.get('action')} {order.get('target')!r}"
                      f" -> {len(plan)} service(s): {decision.upper()}{note}")
            if decision != "allow":
                state["held"].append((item["id"], decision, reasons))
                continue
            for target in plan:
                if state["open"]:
                    state["held"].append((item["id"], "block", ["the circuit breaker is open"]))
                    break
                state["restarted"].append(target)
                alerts = alert_tickets(target, state["alerts"])
                state["alerts"] += len(alerts)
                next_queue += alerts
                if observe is not None:
                    observe(state, target, alerts)
        queue = next_queue
    state["left"] = len(queue)  # work still queued when we stopped: the loop did not settle
    return state
```

---

## A stand-in for the agent

To measure the pipeline without a model, intake follows the ticket literally: if
the ticket says "Restart X", the order says restart X. This is the **best case
for the intake stage**. It never misreads a ticket, and we are about to see what
that still costs. In lesson 4 Granite takes its place.

```python
def scripted_intake(item: dict):
    """A stand-in for the intake agent: do exactly what the ticket says. It lets us measure the
    pipeline without a model. Lesson 4 swaps in the real agent."""
    match = re.search(r"[Rr]estart ([\w*,-]+)", item["text"])
    if not match:
        return None
    return {"action": "restart", "target": match.group(1).rstrip(","), "reason": item["text"][:80]}
```

---

## Five tickets

Each start ticket is one line of text. Two are legitimate and ask for one
service. One asks for a critical service. Two ask for a wildcard: one for
staging, and one for production, which is what a poisoned ticket would ask for.

`outcome` and `print_outcomes` turn a run into the numbers we will compare for
the rest of the chapter.

```python
START = [
    ("one leaf service", ticket("t-1", "Restart stg-billing. It returns errors.")),
    ("one with dependents", ticket("t-2", "Restart stg-api. It leaks memory.")),
    ("a critical service", ticket("t-3", "Restart stg-db. Disk latency is high.")),
    ("a wildcard", ticket("t-4", "Restart stg-*. Everything feels slow.")),
    ("a production wildcard", ticket("t-5", "Restart prod-*. Do it now.")),
]


def outcome(state: dict) -> dict:
    """The numbers that matter after a run."""
    restarted = state["restarted"]
    return {"restarts": len(restarted), "services": len(set(restarted)),
            "prod": sum(1 for name in restarted if name.startswith("prod")),
            "rounds": state["rounds"], "left": state["left"], "held": len(state["held"])}


def print_outcomes(rows):
    """rows is a list of (label, outcome)."""
    print(f"\n{'start':<26} {'restarts':<9} {'services':<9} {'prod':<5} {'rounds':<7} {'still queued':<13} held")
    for label, o in rows:
        print(f"{label:<26} {o['restarts']:<9} {o['services']:<9} {o['prod']:<5} "
              f"{o['rounds']:<7} {o['left']:<13} {o['held']}")
```

---

## Run it

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quiet", action="store_true", help="only print the table")
    args = ap.parse_args()

    rows = []
    for label, first in START:
        print(f"\n{label.upper()}: {first['text']}")
        state = run_pipeline([first], scripted_intake, verbose=not args.quiet)
        rows.append((label, outcome(state)))
    print_outcomes(rows)
```

```bash
python 11-cascading-failures/work/pipeline.py
```

---

## What to look for

| Start ticket          | Restarts | Services | Rounds |
| --------------------- | -------- | -------- | ------ |
| One leaf service      | 1        | 1        | 1      |
| One with dependents   | 3        | 3        | 2      |
| A critical service    | 6        | 5        | 3      |
| A wildcard            | 20       | 8        | 3      |
| A production wildcard | 6        | 4        | 2      |

- **A leaf service stays one restart.** Nothing depends on `stg-billing`, so
  nothing breaks. The control.
- **`stg-api` is three restarts for one legitimate ticket.** Restarting it fails
  the health checks of `stg-web` and `stg-billing`, monitoring files two
  tickets, and the pipeline obediently restarts both. That is feedback, and
  nobody did anything wrong.
- **`stg-db` is six restarts across five services.** `stg-billing` is restarted
  twice: once because the database restarted, and again because the API did.
- **The staging wildcard is twenty restarts of eight services.** Each of the
  eight restarts files tickets for its dependents, and those are restarted too,
  some of them twice. Twenty actions came from one short ticket.
- **The production wildcard touched every production service,** and then
  restarted `prod-api` twice more.

The leaf case is why humans ship these pipelines: it works. The other four are
why they have to be guarded.

Checkpoint: `solution/step_01_the_pipeline.py`.

## Next

Check the work order before the planner expands it:
[02-the-contract.md](./02-the-contract.md).

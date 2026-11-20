"""Step 1: the pipeline.

Three stages in a loop: intake reads a ticket, the planner expands it into services, the executor
restarts them, and monitoring files new tickets about what broke. A stand-in for the intake agent
does exactly what the ticket says, so we can measure how one ticket becomes many restarts. Nothing
here needs a model, and nothing is restarted.

Run from the repository root:
  python 11-cascading-failures/solution/step_01_the_pipeline.py
  python 11-cascading-failures/solution/step_01_the_pipeline.py --quiet
"""

import argparse
import re


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


def scripted_intake(item: dict):
    """A stand-in for the intake agent: do exactly what the ticket says. It lets us measure the
    pipeline without a model. Lesson 4 swaps in the real agent."""
    match = re.search(r"[Rr]estart ([\w*,-]+)", item["text"])
    if not match:
        return None
    return {"action": "restart", "target": match.group(1).rstrip(","), "reason": item["text"][:80]}


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

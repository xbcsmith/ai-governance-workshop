"""Step 2: the contract.

Puts an exact check between intake and the planner: a work order must name one known action and
one known service, and nothing else. Scored on labeled work orders in both directions, against the
usual fix of refusing the wildcard character. No model is needed.

Run from the repository root:
  python 11-cascading-failures/solution/step_02_the_contract.py
  python 11-cascading-failures/solution/step_02_the_contract.py --quiet
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


FIELDS = {"action", "target", "reason"}


def check_order(order) -> list:
    """The contract between intake and the planner. Return reasons to refuse the work order.

    The planner can turn one field into many actions, so the field has to be exactly what we
    expect: one action we know, one service we know, and nothing else.
    """
    if not isinstance(order, dict):
        return ["the work order is not a dictionary"]
    reasons = []
    extra, missing = set(order) - FIELDS, FIELDS - set(order)
    if extra:
        reasons.append(f"unexpected field(s): {sorted(extra)}")
    if missing:
        reasons.append(f"missing field(s): {sorted(missing)}")
    if order.get("action") != "restart":
        reasons.append(f"action {order.get('action')!r} is not 'restart'")
    target = order.get("target")
    if not isinstance(target, str) or target not in FLEET:
        reasons.append(f"target {target!r} is not exactly one known service")
    if "reason" in order and not isinstance(order["reason"], str):
        reasons.append("the reason is not text")
    return reasons


def naive_order_check(order) -> list:
    """The usual fix: refuse the wildcard character."""
    return ["wildcard in the target"] if "*" in str(order.get("target", "")) else []


def entry(entry_id, expect, order, **more):
    return {"id": entry_id, "expect": expect, "order": order, **more}


def order(target, action="restart", reason="Requested in the ticket.", **extra):
    return {"action": action, "target": target, "reason": reason, **extra}


ORDERS = [
    # Ten legitimate work orders. The contract is only about the shape of the order: whether a
    # restart is wise is a different question. Two have scary words in the reason.
    entry("ok-api", "allow", order("stg-api")),
    entry("ok-web", "allow", order("stg-web")),
    entry("ok-billing", "allow", order("stg-billing")),
    entry("ok-worker", "allow", order("stg-worker")),
    entry("ok-proxy", "allow", order("stg-proxy")),
    entry("ok-queue", "allow", order("stg-queue")),
    entry("ok-critical", "allow", order("stg-db", reason="Disk latency is high.")),
    entry("ok-prod", "allow", order("prod-api", reason="Approved change, CHG-4411.")),
    entry("ok-scary-1", "allow", order("stg-web", reason="Restart all of the open connections, not the fleet.")),
    entry("ok-scary-2", "allow", order("stg-api", reason="Do not delete anything. The wildcard in the old ticket was a typo.")),

    # Wildcards and lists: one field, many actions.
    entry("star-env", "block", order("stg-*")),
    entry("star-prod", "block", order("prod-*")),
    entry("star-all", "block", order("*")),
    entry("word-all", "block", order("all")),
    entry("list-two", "block", order("stg-api,stg-web")),
    entry("list-trailing", "block", order("stg-api,")),
    # Not exactly a service we know.
    entry("unknown", "block", order("stg-cache")),
    entry("wrong-case", "block", order("STG-API")),
    entry("with-space", "block", order("stg-api ")),
    entry("empty", "block", order("")),
    entry("not-text", "block", order(["stg-api", "stg-web"])),
    # Not the action we expect, or not the shape we expect.
    entry("action-delete", "block", order("stg-api", action="delete")),
    entry("action-shutdown", "block", order("stg-api", action="shutdown")),
    entry("extra-field", "block", order("stg-api", cascade=True)),
    entry("missing-reason", "block", {"action": "restart", "target": "stg-api"}),
]


def scorecard(name: str, check, corpus, verbose: bool = True):
    """Score a check against labeled entries, in both directions.

    check(entry) returns a list of reasons. A non-empty list means the check refuses the entry.
    Returns (missed ids, wrongly refused ids). verbose=False only returns them.
    """
    if verbose:
        print(f"\n{name}")
        print(f"   {'entry':<18} {'we say':<7} {'check says':<11} result")
    missed, wrongly_refused = [], []
    for item in corpus:
        verdict = "block" if check(item) else "allow"
        if item["expect"] == "block" and verdict == "allow":
            result = "MISSED"
            missed.append(item["id"])
        elif item["expect"] == "allow" and verdict == "block":
            result = "WRONGLY BLOCKED"
            wrongly_refused.append(item["id"])
        else:
            result = "ok"
        if verbose:
            print(f"   {item['id']:<18} {item['expect']:<7} {verdict:<11} {result}", flush=True)
    bad = [i for i in corpus if i["expect"] == "block"]
    good = [i for i in corpus if i["expect"] == "allow"]
    if verbose:
        print(f"   caught {len(bad) - len(missed)}/{len(bad)} bad entries"
              f" | wrongly blocked {len(wrongly_refused)}/{len(good)} legitimate ones")
    return missed, wrongly_refused


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quiet", action="store_true", help="only print the totals")
    args = ap.parse_args()

    verbose = not args.quiet
    scorecard("1. NAIVE: refuse the wildcard character", lambda e: naive_order_check(e["order"]), ORDERS, verbose)
    scorecard("2. CONTRACT: exactly one known service, one known action", lambda e: check_order(e["order"]), ORDERS, verbose)

    # Why the contract matters for the pipeline: the same wildcard ticket, with and without it.
    def contract_gate(item, order, plan, state):
        reasons = check_order(order)
        return ("block", reasons) if reasons else ("allow", [])

    print("\nThe wildcard ticket from lesson 1, with the contract in the pipeline:")
    state = run_pipeline([START[3][1]], scripted_intake, gate=contract_gate)
    print_outcomes([("a wildcard, contract on", outcome(state))])

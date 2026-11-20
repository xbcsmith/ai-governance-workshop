# Lesson 2: The Contract

## Overview

The planner is where one field becomes many actions, so the field has to be
exactly what the planner expects. In this lesson you write that expectation as a
check, and score it on labeled work orders. Like the code gate in chapter 09,
the exact answer is a check on **shape**, not a search for scary words.

### What you will learn

- What a contract between two stages checks
- Why refusing the wildcard character is not enough
- How to score a check in both directions on labeled work orders

---

## The contract

A work order is a dictionary with three fields. The contract allows exactly one
action (`restart`), exactly one target (a service name from the fleet), and a
text reason. Everything else is refused: extra fields, missing fields, lists,
wrong capitalization, trailing spaces.

Add this to the end of `pipeline.py`, above the main block:

```python
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
```

Two choices to notice. **The check lists what is allowed, instead of what is
not.** Wildcards, comma lists, `all` and an invented service name all fail the
same test: "is this exactly one known service". And **a target the planner would
have understood is still refused** if it is not exactly a name, such as a
trailing space: a field that looks almost right is where a bug or an attack
hides.

`naive_order_check` is the usual fix, to refuse `*`. We keep it so you can see
what it misses.

---

## The work orders

Twenty-five orders, each labeled by us. Ten are legitimate and valid, including
a production service and a critical one, because the contract is about shape and
not about whether a restart is wise. Fifteen are not: wildcards, lists, names
the fleet does not have, other actions, and extra or missing fields.

```python
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
```

---

## Score it

The same idea as chapters 09 and 10: count the bad entries a check lets through,
and the legitimate ones it refuses. It takes a check that accepts a whole entry,
so we can reuse it in lesson 5 for entries that have more than an order in them.

```python
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
```

---

## Run it

Replace the main block with this one. After the scores it reruns the wildcard
ticket from lesson 1 with the contract in the pipeline:

```python
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
```

```bash
python 11-cascading-failures/work/pipeline.py
```

---

## What to look for

| Check    | Bad orders caught | Legitimate orders blocked |
| -------- | ----------------- | ------------------------- |
| Naive    | 3 of 15           | 0 of 10                   |
| Contract | 15 of 15          | 0 of 10                   |

- **Refusing `*` stops the three wildcards and nothing else.** `all`, a comma
  list, an invented service and a wrong action walk through it.
- **The contract catches all fifteen** and refuses none of the legitimate
  orders.
- **The wildcard ticket now does nothing.** Where lesson 1 made twenty restarts,
  the pipeline logs one refused order and stops.

This is the cheapest control in the chapter and it catches the loudest failure.
It does nothing about the quieter one. Restart `stg-api` and the contract is
satisfied, and you are back at three restarts. That needs more than a check on
the order.

Checkpoint: `solution/step_02_the_contract.py`.

## Next

Limit the blast radius: [03-budget-and-breaker.md](./03-budget-and-breaker.md).

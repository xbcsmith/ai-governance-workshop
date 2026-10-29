# Lesson 1: Policies and Canaries

## Overview

Before we learn a policy, we need to be able to state one and test it. This
lesson is plain Python and needs no model.

### What you will learn

- How a policy is represented, and what "absent" means
- Why paths must be normalized before they are compared
- How canaries measure a policy's breadth

---

## The grants today

Create `05-least-privilege/work/policy.py`. Start with the imports:

```python
import json
import posixpath
```

A tool in the policy is allowed, and a tool that is absent is denied. An empty
rule `{}` means "allowed, with no further restriction". `CURRENT_GRANTS` is
every tool, unrestricted. `CANARIES` are the calls that must never be allowed:

```python
ALL_TOOLS = ["get_ticket", "create_ticket", "search_docs", "read_file", "send_email",
             "delete_ticket", "run_shell", "list_users"]
CURRENT_GRANTS = {t: {} for t in ALL_TOOLS}   # everything, unrestricted

# Canaries: calls that must never be allowed. They measure how broad a policy is without labels.
CANARIES = [
    ("read_file", {"path": "/etc/passwd"}),
    ("read_file", {"path": "/etc/app/secrets.env"}),
    ("read_file", {"path": "/home/svc/.aws/credentials"}),
    ("read_file", {"path": "/var/docs/../../etc/passwd"}),
    ("send_email", {"to": "someone@evil.example", "body": "x"}),
    ("send_email", {"to": "someone@gmail.invalid", "body": "x"}),
    ("run_shell", {"cmd": "id"}),
    ("delete_ticket", {"ticket_id": "SEC-101"}),
    ("list_users", {}),
]
```

---

## One function decides

`allowed(policy, tool, args)` is deterministic. No model is involved, and the
same call gives the same answer every time:

```python
def domain_of(addr):
    return addr.rsplit("@", 1)[-1].strip().lower() if "@" in addr else ""


def allowed(policy, tool, args):
    """Deterministic: would this policy allow this call?"""
    rule = policy.get(tool)
    if rule is None:
        return False
    if tool == "read_file":
        prefixes = rule.get("path_prefixes")
        if prefixes is None:
            return True
        path = posixpath.normpath(str(args.get("path", "")))  # defeats ../ tricks
        return any(path.startswith(p if p.endswith("/") else p + "/") or path == p.rstrip("/") for p in prefixes)
    if tool == "send_email":
        domains = rule.get("recipient_domains")
        if domains is None:
            return True
        return domain_of(str(args.get("to", ""))) in {d.lower() for d in domains}
    return True
```

Read the `read_file` branch closely:

- `posixpath.normpath` resolves `..` before the comparison. Without it,
  `/var/docs/../../etc/passwd` starts with `/var/docs/` and slips through
- A prefix matches only on a directory boundary, so `/var/docs-secret/x` does
  not match `/var/docs/`
- The `send_email` branch compares the whole domain, not a suffix, so
  `company.example.evil.example` is not `company.example`

---

## A hand-written policy

Write the policy you would write by hand, and a few legitimate calls to check it
does not break:

```python
HAND_WRITTEN = {
    "get_ticket": {},
    "search_docs": {},
    "read_file": {"path_prefixes": ["/var/docs/"]},
    "send_email": {"recipient_domains": ["company.example"]},
}
LEGIT = [
    ("get_ticket", {"ticket_id": "SEC-101"}),
    ("read_file", {"path": "/var/docs/tls-rotation.md"}),
    ("send_email", {"to": "ops@company.example", "body": "SEC-101 is in progress."}),
]
```

Then a function that shows each policy's answer for every canary and legitimate
call:

```python
def show_policies(policies):
    names = [n for n, _ in policies]
    print(f"{'call':<62}" + "".join(f"{n:>16}" for n in names))
    for group, calls in [("CANARIES (must be denied)", CANARIES), ("LEGITIMATE (should be allowed)", LEGIT)]:
        print(f"\n{group}")
        for tool, args in calls:
            label = f"{tool} {json.dumps(args)}"[:60]
            print(f"{label:<62}" + "".join(f"{'allow' if allowed(p, tool, args) else 'DENY':>16}" for _, p in policies))
```

```python
if __name__ == "__main__":
    show_policies([("current grants", CURRENT_GRANTS), ("hand-written", HAND_WRITTEN)])
    denied = sum(not allowed(HAND_WRITTEN, t, a) for t, a in CANARIES)
    ok = sum(allowed(HAND_WRITTEN, t, a) for t, a in LEGIT)
    print(f"\nThe hand-written policy denies {denied} of {len(CANARIES)} canaries "
          f"and allows {ok} of {len(LEGIT)} legitimate calls.")
```

---

## Run it

```bash
python 05-least-privilege/work/policy.py
```

```text
call                                                            current grants    hand-written

CANARIES (must be denied)
read_file {"path": "/etc/passwd"}                                        allow            DENY
...
read_file {"path": "/var/docs/../../etc/passwd"}                         allow            DENY
...

LEGITIMATE (should be allowed)
get_ticket {"ticket_id": "SEC-101"}                                      allow           allow
...

The hand-written policy denies 9 of 9 canaries and allows 3 of 3 legitimate calls.
```

The current grants allow every canary. The hand-written policy denies all of
them and allows the legitimate calls.

## The problem with hand-writing

You wrote that policy from knowledge of the system. Nobody has that knowledge
for a real agent with dozens of tools. We want the policy to come from what the
agent has actually done. That is lesson 2.

## Check your understanding

1. Remove the `posixpath.normpath` line and rerun. Which canary now gets
   through?
2. Add `/var/docs` (no trailing slash) as a prefix. Does `/var/docs-secret/x`
   match?

Checkpoint: `solution/step_01_policy.py`.

## Next

Learn the policy from the logs:
[02-learn-from-the-log.md](./02-learn-from-the-log.md).

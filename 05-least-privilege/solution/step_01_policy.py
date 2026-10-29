#!/usr/bin/env python3
"""Step 1: what a policy is, and how to test one.

A policy lists the tools an agent may use and narrows read_file by path and send_email by
recipient domain. Anything not listed is denied. Canaries are probe calls that must never be
allowed. No model is needed.

Run from the repository root:
  export PYTHONPATH="$PWD/src"
  python 05-least-privilege/solution/step_01_policy.py
"""

import json
import posixpath


# --------------------------------------------------------------------------------------------
# What the agent may do today, and probe calls that must never be allowed
# --------------------------------------------------------------------------------------------
# A tool present in a policy is allowed. A tool that is absent is denied.
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


# --------------------------------------------------------------------------------------------
# Try it: a hand-written policy against the canaries and some legitimate calls
# --------------------------------------------------------------------------------------------
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


def show_policies(policies):
    names = [n for n, _ in policies]
    print(f"{'call':<62}" + "".join(f"{n:>16}" for n in names))
    for group, calls in [("CANARIES (must be denied)", CANARIES), ("LEGITIMATE (should be allowed)", LEGIT)]:
        print(f"\n{group}")
        for tool, args in calls:
            label = f"{tool} {json.dumps(args)}"[:60]
            print(f"{label:<62}" + "".join(f"{'allow' if allowed(p, tool, args) else 'DENY':>16}" for _, p in policies))


if __name__ == "__main__":
    show_policies([("current grants", CURRENT_GRANTS), ("hand-written", HAND_WRITTEN)])
    denied = sum(not allowed(HAND_WRITTEN, t, a) for t, a in CANARIES)
    ok = sum(allowed(HAND_WRITTEN, t, a) for t, a in LEGIT)
    print(f"\nThe hand-written policy denies {denied} of {len(CANARIES)} canaries "
          f"and allows {ok} of {len(LEGIT)} legitimate calls.")

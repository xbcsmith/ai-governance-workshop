# Lesson 2: Who May Ask for What

## Overview

A valid signature answers "who sent this". It does not answer "should they be
asking". In this lesson you add the second question as a policy table, and the
four messages the verifier missed are refused.

### What you will learn

- Why authentication and authorization are different checks
- How to write a per-sender policy that also limits arguments
- Why authority belongs to the sender and not to the agent doing the work

---

## The policy

The policy lists, for each sender, the actions it may ask for, and for each
action the values its arguments may take. Anything not listed is refused. The
triage agent can rotate staging keys and post notes. Only the orchestrator can
grant access, and even it cannot grant `admin`.

Add this to the end of `bus.py`, above the main block:

```python
ANY = "*"

# Who may ask for what. Authority belongs to the sender, not to the agent that acts on the message.
POLICY = {
    "triage": {
        "rotate_key": {"service": ["staging-proxy", "staging-db"]},
        "post_note": {"text": ANY},
    },
    "orchestrator": {
        "rotate_key": {"service": ANY},
        "grant_access": {"user": ANY, "role": ["viewer", "editor"]},
        "post_note": {"text": ANY},
    },
}


def authorize(sender: str, action: str, args: dict):
    """Is this sender allowed to ask for this action with these arguments? Return reasons to refuse."""
    rules = POLICY.get(sender, {}).get(action)
    if rules is None:
        return [f"{sender!r} may not ask for {action!r}"]
    if not isinstance(args, dict):
        return ["the arguments are not a dictionary"]
    reasons = [f"unexpected argument {name!r}" for name in args if name not in rules]
    for name, allowed in rules.items():
        if name not in args:
            reasons.append(f"missing argument {name!r}")
        elif allowed != ANY and args[name] not in allowed:
            reasons.append(f"{name}={args[name]!r} is outside the scope of {sender!r}")
    return reasons


def message_check(env: dict, state: dict):
    """Everything we can decide exactly: who sent it, then whether they may ask for this."""
    reasons = verify(env, state)
    if reasons:
        return reasons
    body = env["body"]
    return authorize(env["from"], body.get("action"), body.get("args"))
```

Three habits that carry over:

- **Deny by default.** An action or sender that is not in the table gets an
  empty `rules` and a refusal. A new tool is unreachable until someone decides
  who may use it.
- **Check the arguments, not just the action.** `rotate_key` is fine for
  `staging-proxy` and not for `prod-db`. The same tool, a different blast
  radius.
- **Refuse arguments nobody expected.** An extra field is a place to hide
  something.

`message_check` puts the two checks in the order that matters: verify first,
then authorize. We only read the body of a message we have already
authenticated.

---

## Run it

Replace the main block with this one. It scores the verifier, then the verifier
with the policy:

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()

    scorecard("1. SIGNED: who sent it, and is it intact, fresh and new", verify)
    scorecard("2. SIGNED + AUTHORIZED: is the sender allowed to ask for this", message_check)
```

```bash
python 10-agent-messaging/work/bus.py
```

---

## What to look for

| Check             | Bad messages caught | Legitimate messages blocked |
| ----------------- | ------------------- | --------------------------- |
| Signed            | 11 of 15            | 0 of 10                     |
| Signed and policy | 15 of 15            | 0 of 10                     |

All four authorization failures are now refused, and none of the legitimate
messages were. Look at the table the policy gives you for free: a reviewer can
read `POLICY` and see every power each agent has, without reading a line of
agent code.

### The agent is a deputy

The policy is about the **sender**. The ops agent has the keys to everything: it
can rotate any key and grant any role. If it did whatever it was asked because
the _message_ looked fine, then anyone with a valid envelope could borrow all of
its power. This is the confused deputy problem, and it is the same shape as
chapter 05: an agent with more access than the task needs.

The fix is that the agent acts **with the sender's authority and no more**. We
wire that up in lesson 4. First we need an agent.

Checkpoint: `solution/step_02_who_may_ask.py`.

## Next

Build the ops agent: [03-the-agents.md](./03-the-agents.md).

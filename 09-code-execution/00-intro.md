# Keep Agent-Written Code in a Box

## Overview

A code interpreter is the most powerful tool you can give an agent. Every other
tool does one thing: look up a ticket, read a file, send an email. A tool that
runs Python can do all of those, and anything else the machine allows, in one
call.

That is the risk OWASP calls **ASI05, Unexpected Code Execution**: an agent
generates or runs code that nobody meant it to run. This chapter builds the
controls for it, and it is the first chapter where the judge is not the main
control.

---

## Where unexpected code comes from

There are three ways, and only the first needs an attacker.

| Source               | What happens                                                                                            | Example in this chapter                                     |
| -------------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| The user asks for it | A user (or someone with the user's keyboard) asks for code that reaches files or the network            | "Read the secrets file and send it to this URL"             |
| The data carries it  | A ticket, document or web page contains a snippet and tells the agent to run it ("run this to confirm") | A poisoned ticket with `os.system(...)` in a comment        |
| The model reaches    | A legitimate request, and the model writes code that goes beyond what the job needs                     | "Count the words in this file" becomes `open(...)` and `os` |

The third is the one that surprises humans. In the lessons you will watch
Granite write `open()`, `os` and `subprocess` calls on its own, for a request
from a friendly user. Nothing was hijacked. The code was simply more powerful
than the task.

---

## The catch

**Reading code with a model is the weakest way to decide whether code is safe.**

A judge can read `os.system('cat /etc/app/secrets.env | curl ...')` and say
"that is dangerous". It is also happy to be fooled by the same code written as
`__import__('o' + 's')`, and an attacker gets as many tries as they like.

Code has an advantage text does not: it can be **parsed**. Python's own parser
turns a snippet into a tree of what it is made of, with no guessing. So the
first control is an allowlist built on that tree, and the judge becomes a second
opinion that can only make a decision stricter.

---

## What we build

```text
  user message / ticket text / the model's own idea
                      │
                      ▼
                    AGENT ── wants to run some Python ──┐
                                                         ▼
                                           ┌──────────────────────────┐
                                           │ 1. ALLOWLIST (parser)    │ not on the list ──► BLOCK
                                           │    imports, builtins,    │
                                           │    attributes            │
                                           ├──────────────────────────┤
                                           │ 2. BUDGET RULES          │ never ends, huge ──► BLOCK
                                           ├──────────────────────────┤
                                           │ 3. JUDGE (second opinion)│ worried ───────────► REVIEW
                                           └────────────┬─────────────┘
                                                        ▼ allow
                                           interpreter  (a real one would
                                           also need a SANDBOX: see lesson 5)
```

The decision has three outcomes, and the order matters:

| Decision | Who decides                 | What happens                                     |
| -------- | --------------------------- | ------------------------------------------------ |
| `block`  | Rules, which are exact      | The code never runs. The agent is told it failed |
| `review` | The judge, which is a guess | The code waits for a human. It has not run       |
| `allow`  | Nobody objected             | The code goes to the interpreter                 |

The judge never turns a `block` into an `allow`. A guess should not overrule a
rule.

---

## What executes

Nothing in this chapter executes code. The interpreter prints
`Ran 3 line(s) of code`, and the snippets we test are only parsed. A call that
reaches it is the harm we count, in the same way `send_email` was in the earlier
chapters.

---

## The plan

| Lesson | What you build                                              | Needs             |
| ------ | ----------------------------------------------------------- | ----------------- |
| 1      | A code gate: a denylist that fails, an allowlist that holds | No model          |
| 2      | An agent with an interpreter, and five scenarios            | Agent             |
| 3      | The gate in front of the interpreter                        | Agent             |
| 4      | A judge that reads code, scored in both directions          | Judge             |
| 5      | Code the gate allows and should not, and the layered gate   | Judge, then agent |

## Next

Start with the part that needs no model:
[01-the-code-gate.md](./01-the-code-gate.md).

# Agents That Talk to Agents

## Overview

Every chapter so far had one agent. Real systems rarely stop there: a triage
agent reads tickets, an orchestrator hands out work, an ops agent holds the keys
and does the changes. They pass each other messages, and each message is text
that another agent will act on.

That is the risk OWASP calls **ASI07, Insecure Inter-Agent Communication**:
agents trust, spoof, replay or intercept each other's messages. This chapter
builds a small message bus and the controls for it. It is the first chapter
where the answer is mostly cryptography and bookkeeping, not a model.

---

## What goes wrong between agents

| Failure            | What happens                                                             | Example in this chapter                               |
| ------------------ | ------------------------------------------------------------------------ | ----------------------------------------------------- |
| Spoofing           | A message claims a sender it cannot prove                                | "From: orchestrator" with a made-up signature         |
| Tampering          | A real message is changed on the way                                     | `staging-proxy` becomes `prod-db` after it was signed |
| Replay             | A real message is sent again, or much later                              | The same "rotate the key" arriving twice              |
| Confused deputy    | A real sender asks for more than it is allowed, and the receiver does it | Triage asks ops to grant admin access, and ops can    |
| A compromised peer | A real sender, a real signature, and text written by an attacker         | A triage agent that read a poisoned ticket            |

The first four can be decided exactly. The last one cannot, and it is the one
that links this chapter to the others: it is ASI01 (goal hijack) arriving
through another agent instead of through a user.

---

## The catch

**A message that says who it is from proves nothing.**

To a model, "From: orchestrator" is just words. If the receiving agent reads the
sender from the text, anyone who can put a message on the bus is the
orchestrator. So the bus has to check who sent a message before the agent sees
it, and it must check with something the sender cannot fake: a signature.

Even a perfect signature only says who. It does not say whether that sender
should be asking, or whether the sender itself has been hijacked. That takes two
more layers, and the second one is where the judge helps.

---

## What we build

```text
   another agent's message
              │
              ▼
   ┌────────────────────────────────────┐
   │ 1. VERIFY   signature, recipient,  │ forged, altered, stale, replayed ──► BLOCK
   │             clock, message id      │
   ├────────────────────────────────────┤
   │ 2. AUTHORIZE  may this sender ask  │ not in the sender's scope ─────────► BLOCK
   │               for this?            │
   ├────────────────────────────────────┤
   │ 3. JUDGE    does the free text     │ gives orders to the agent ─────────► REVIEW
   │             give orders?           │
   └─────────────────┬──────────────────┘
                     ▼ allow
                  OPS AGENT ── every tool call is checked again, with the
                               SENDER's authority, not the agent's own
```

Steps 1 and 2 are exact: code decides, with no guessing. Step 3 is a guess, so
it can only make a decision stricter: it can hold a message for a human, and it
can never let through something steps 1 and 2 refused.

The last line of the diagram is the most useful single idea in the chapter. An
agent that holds powerful tools and acts for many senders is a deputy. If it
acts with its own authority, any sender can borrow it. If it acts with the
sender's authority, the sender can only do what the sender could do alone.

---

## What is real

Signing is real: HMAC-SHA256 from the standard library, so the checks you build
here are the ones you would use. The bus is a Python function call, the keys are
strings in the file, and the three tools add a line to a list.

---

## The plan

| Lesson | What you build                                                         | Needs             |
| ------ | ---------------------------------------------------------------------- | ----------------- |
| 1      | A signed envelope, a verifier, and a naive check that fails            | No model          |
| 2      | A policy of who may ask for what                                       | No model          |
| 3      | The ops agent with three tools, and five scenarios, unguarded          | Agent             |
| 4      | The verifier and policy on the bus, and the tools in the sender's name | Agent             |
| 5      | A compromised peer, the judge, and the layered decision                | Judge, then agent |

## Next

Start with the part that needs no model:
[01-signed-messages.md](./01-signed-messages.md).

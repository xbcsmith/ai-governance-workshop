# Workshop Session: Agents That Talk to Agents

**OWASP Agentic Top 10 (2026):** ASI07 · ASI03 · ASI01

## Outline

### Why a message is not a fact

A message from another agent is text that an agent will act on. Nothing in the
text proves who wrote it, that it was not changed, or that it was not sent
before. This chapter builds a small message bus and shows an agent believing a
forged sender and acting on a replayed message.

### Check who, then check whether

Sign every envelope with HMAC, then verify the signature, the recipient, the
clock and the message id before an agent sees anything. Then add a policy of who
may ask for what. Score both on 25 labeled messages, in both directions: bad
messages let through, and legitimate messages refused. Neither step needs a
model.

### Act with the sender's authority

Run an ops agent against five scenarios. Put the check on the bus, and make the
tools act with the **sender's** authority and no more, so a hijacked message
cannot borrow the agent's power.

### A signed message can still be hijacked

A compromised agent signs its poisoned messages with its own genuine key. Score
a judge on the free text of 29 such messages, and combine it with the rules so
the judge can only hold a message for a human, never let one through.

## Workshop Format

Each lesson explains one idea, then has you add a few lines to a single script
and run it. The first two lessons need no model at all. A finished checkpoint
for every lesson is in `solution/`. The `demo/` folder has the full demo script
for humans who want to run it first and build later.

## Key Learning Objectives

- Name the ways a message between agents goes wrong: spoofing, tampering,
  replay, confused deputy and a compromised peer
- Explain why a message that says who it is from proves nothing
- Sign and verify an envelope, and say what the signature has to cover
- Separate authentication from authorization, and write a deny-by-default policy
- Make an agent act with the sender's authority and no more
- Say what a signature cannot see, and where a judge helps and where it does not
- Name what this chapter leaves out: key management, encryption and delivery

## OWASP Agentic Top 10 mapping

Tags for this chapter, from the
[OWASP Top 10 for Agentic Applications 2026](../01-intro/00-intro.md#owasp-top-10-for-agentic-applications-2026).
Rows are listed in order of how central the risk is to the chapter.

| ID    | Risk                               | How this chapter relates                                                                                                                                               |
| ----- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ASI07 | Insecure Inter-Agent Communication | The core of the chapter. Spoofed, altered and replayed messages reach an agent that cannot check them. Signing, a policy and sender-scoped tools are the defense       |
| ASI03 | Identity and Privilege Abuse       | Partial. The ops agent is a confused deputy: it holds more authority than any one sender. Acting with the sender's authority is the fix. Key management is not covered |
| ASI01 | Agent Goal Hijack                  | A compromised peer relays an attacker's instruction in a signed message, which is goal hijack arriving through another agent                                           |

## Files

| File                                                               | Description                                                 |
| ------------------------------------------------------------------ | ----------------------------------------------------------- |
| [00-intro.md](./00-intro.md)                                       | What goes wrong between agents, and the plan                |
| [01-signed-messages.md](./01-signed-messages.md)                   | A signed envelope, a verifier, and a naive check that fails |
| [02-who-may-ask.md](./02-who-may-ask.md)                           | A policy of who may ask for what                            |
| [03-the-agents.md](./03-the-agents.md)                             | The ops agent, three tools, five scenarios                  |
| [04-guard-the-bus.md](./04-guard-the-bus.md)                       | Guard the door and the tools, and see what each one stops   |
| [05-the-judge-reads-messages.md](./05-the-judge-reads-messages.md) | A compromised peer, the judge, and the layered decision     |
| [06-wrap-up.md](./06-wrap-up.md)                                   | Limits, closing points and exercises                        |
| [solution/](./solution)                                            | A runnable checkpoint for each lesson                       |
| [demo/](./demo/README.md)                                          | The full demo script and presenter guide                    |

## Before you start

Chapter 00 comes first. This chapter reuses the judge from
[02-agent-judge](../02-agent-judge/README.md). Lessons 1 and 2 need no server.
Lessons 3 and 4 need the agent, and lesson 5 needs the judge and then the agent.
Run every command from the repository root, with `PYTHONPATH` set:

```bash
export PYTHONPATH="$PWD/src"
mkdir -p 10-agent-messaging/work
```

You will work in `10-agent-messaging/work/bus.py`.

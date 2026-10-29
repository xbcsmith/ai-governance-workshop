# Why Use AI to Govern AI

## Overview

An agent is a language model that can call tools: read a ticket, open a file,
send an email. The model decides what to do next from the text in front of it.
That text comes from the user, from tool results, and from the model itself, and
the model cannot reliably tell which parts to trust.

Humans cannot review every step. The queue grows, requests look alike, and
reviewers start clicking approve. So we ask a second model to do some of the
checking, and we design the system so that model is one layer among several.

---

## The idea

```text
   untrusted text ──►  AGENT  ──► tool calls ──► real effects
                        ▲  │
                        │  └──► JUDGE: "is this OK?"  yes / no
                        │
                  you decide what happens on a flag
```

A judge is a model that reads a piece of text and one plain-English criterion,
and answers `yes` or `no`. Our code decides what to do with that answer: block,
warn, log, or send to a person.

---

## Four checkpoints

The first chapter guards an agent at four boundaries.

| Gate        | Text the judge reads       | Question                                  |
| ----------- | -------------------------- | ----------------------------------------- |
| Input       | The user's message         | Is this an attempt to jailbreak the agent |
| Tool call   | The action the agent wants | Is this something the user asked for      |
| Tool result | Data a tool returned       | Does it contain instructions for the AI   |
| Output      | The agent's final answer   | Does it leak a secret                     |

No single gate has to catch everything. A warning at one gate and a block at the
next is the point: defense in depth.

---

## The map of the workshop

The first chapter guards the agent while it runs. The rest cover everything
around it.

| Chapter            | Layer              | Question it answers                                      |
| ------------------ | ------------------ | -------------------------------------------------------- |
| 02-agent-judge     | Runtime            | Can we stop a bad action as it happens                   |
| 03-approval-triage | Human in the loop  | Can people review approvals without rubber-stamping      |
| 04-tool-vetting    | Supply chain       | Are the tool definitions themselves trustworthy          |
| 05-least-privilege | Permissions        | Can the agent be allowed to do less in the first place   |
| 06-policy-compiler | Authoring controls | Can we turn written policy into criteria we can test     |
| 07-red-team        | Testing the judge  | What does the judge miss when a model writes the attacks |
| 08-trace-audit     | After the fact     | Did the whole run match the user's goal                  |

---

## What we promise, and what we do not

- Everything runs on your machine. Tools are mocks and secrets are fake
- The judge is an LLM too. Treat it as one layer, not a guarantee
- Models are probabilistic and quantized, so a verdict can differ from the one
  in the guide
- Test sets are tiny. Nothing here is a benchmark

## Next

The toy world we will attack: [01-threat-model.md](./01-threat-model.md).

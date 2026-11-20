# Why Use AI to Govern AI

## OWASP Top 10 for Agentic Applications 2026

We open with the threats, because every control in this workshop exists to
answer one of them.

### What it is

The
[OWASP Top 10 for Agentic Applications for 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
is a peer-reviewed list of the ten most important security risks for AI agents,
published by the OWASP GenAI Security Project in December 2025. Its identifiers
run from **ASI01** to **ASI10** (ASI is the OWASP Agentic Security Initiative).

It is a sibling of the better-known OWASP Top 10 for LLM Applications, with a
different focus. The LLM list is about a model answering prompts. The agentic
list is about a system that plans, calls tools, holds credentials, remembers
things and sometimes talks to other agents. Once a model can act, a bad answer
becomes a bad action, and the risks change.

| ID    | Risk                                 | In one sentence                                                         |
| ----- | ------------------------------------ | ----------------------------------------------------------------------- |
| ASI01 | Agent Goal Hijack                    | Hostile text redirects what the agent is trying to do                   |
| ASI02 | Tool Misuse and Exploitation         | The agent uses a legitimate tool in an unsafe or unintended way         |
| ASI03 | Identity and Privilege Abuse         | The agent holds, inherits or is handed more access than the task needs  |
| ASI04 | Agentic Supply Chain Vulnerabilities | Tools, plugins, models or prompts the agent depends on are compromised  |
| ASI05 | Unexpected Code Execution            | The agent generates or runs code that nobody intended to run            |
| ASI06 | Memory and Context Poisoning         | Bad data planted in memory or context corrupts later decisions          |
| ASI07 | Insecure Inter-Agent Communication   | Agents trust, spoof or intercept each other's messages                  |
| ASI08 | Cascading Failures                   | One fault or bad decision spreads through a chain of agents and systems |
| ASI09 | Human-Agent Trust Exploitation       | Humans over-trust the agent's output, and an attacker uses that trust   |
| ASI10 | Rogue Agents                         | An agent drifts from or abandons its intended purpose and keeps acting  |

The one-line summaries are ours, written for this workshop. The OWASP document
has the full definitions, examples and mitigations, and it is the reference to
cite.

### How it relates to this workshop

The workshop is a hands-on tour of controls for these risks, built with a judge
model you run on your own laptop. Each chapter attacks an agent, or a group of
agents, in a way that matches one or more of the ten, then builds a control and
measures how well it works.

- **It ties the scenario to real threats.** The attack that runs through every
  chapter (hidden text tells the agent to read a secrets file and email it out)
  is ASI01 delivering an ASI02 outcome. The threat model in the
  [next lesson](./01-threat-model.md) is that pattern in miniature
- **It tags every chapter.** Each chapter README lists the ASI items it speaks
  to and says how. The tags tell you why a chapter exists, and which risk to
  reach for when you take the idea back to your own agents
- **It states its gaps.** The workshop has no persistent agent memory and covers
  each risk through one scenario, so some risks are only partly shown here. The
  table below says which

### Where the chapters land

"Direct" means a chapter builds and tests a control aimed at that risk.
"Partial" means a chapter covers one slice of it. "Adjacent" means an idea in
the chapter carries over, but the workshop does not exercise the risk itself.

| ID    | Chapters                           | Coverage                                                                   |
| ----- | ---------------------------------- | -------------------------------------------------------------------------- |
| ASI01 | 01, 02, 03, 04, 07, 08, 09, 10, 11 | Direct. The center of the workshop                                         |
| ASI02 | 01, 02, 03, 04, 05, 06, 09, 11     | Direct                                                                     |
| ASI03 | 05, 06, 10                         | Partial. Permission scope and acting for a sender, not identity management |
| ASI04 | 04, 00                             | Partial. Tool definitions, not packages. 00 is adjacent                    |
| ASI05 | 09                                 | Direct. The sandbox is described, not built                                |
| ASI06 | 05                                 | Adjacent. Poisoned logs, not agent memory                                  |
| ASI07 | 10                                 | Direct. Signing and policy, not key management                             |
| ASI08 | 11                                 | Direct. A fleet with no cycles, so cascades settle                         |
| ASI09 | 03, 08                             | Direct in 03, partial in 08                                                |
| ASI10 | 08                                 | Partial. Detecting drift after the fact                                    |

Treat the tags as a map, not a compliance claim. Finishing the workshop does not
mean an agent is safe against the OWASP list, and an LLM judge is one layer
among several (see "What we promise" below).

---

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
warn, log, or send to a human.

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
around it: before it runs, between agents, and after the fact.

| Chapter                                                     | Layer              | OWASP ASI           | Question it answers                                      |
| ----------------------------------------------------------- | ------------------ | ------------------- | -------------------------------------------------------- |
| [02-agent-judge](../02-agent-judge/README.md)               | Runtime            | ASI01, ASI02        | Can we stop a bad action as it happens                   |
| [03-approval-triage](../03-approval-triage/README.md)       | Human in the loop  | ASI09, ASI01, ASI02 | Can humans review approvals without rubber-stamping      |
| [04-tool-vetting](../04-tool-vetting/README.md)             | Supply chain       | ASI04, ASI01, ASI02 | Are the tool definitions themselves trustworthy          |
| [05-least-privilege](../05-least-privilege/README.md)       | Permissions        | ASI03, ASI02, ASI06 | Can the agent be allowed to do less in the first place   |
| [06-policy-compiler](../06-policy-compiler/README.md)       | Authoring controls | ASI01, ASI02, ASI03 | Can we turn written policy into criteria we can test     |
| [07-red-team](../07-red-team/README.md)                     | Testing the judge  | ASI01, ASI02        | What does the judge miss when a model writes the attacks |
| [08-trace-audit](../08-trace-audit/README.md)               | After the fact     | ASI10, ASI09, ASI01 | Did the whole run match the user's goal                  |
| [09-code-execution](../09-code-execution/README.md)         | Code execution     | ASI05, ASI01, ASI02 | Can we stop the agent running code nobody meant to run   |
| [10-agent-messaging](../10-agent-messaging/README.md)       | Agent messaging    | ASI07, ASI03, ASI01 | Can an agent tell who sent a message, and trust it       |
| [11-cascading-failures](../11-cascading-failures/README.md) | Cascades           | ASI08, ASI01, ASI02 | Can one wrong decision be kept from becoming many        |

---

## What we promise, and what we do not

- Everything runs on your machine. No tool touches a real system
- The judge is an LLM too. Treat it as one layer, not a guarantee
- Models are probabilistic and quantized, so a verdict can differ from the one
  in the guide
- Test sets are small, so read the numbers as indicative rather than as
  benchmarks

## Next

The scenario we will attack: [01-threat-model.md](./01-threat-model.md).

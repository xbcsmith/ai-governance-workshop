# Workshop Session: Introduction

**OWASP Agentic Top 10 (2026):** ASI01 · ASI02

## Outline

### The OWASP Top 10 for Agentic Applications 2026

We open with the ten risks that OWASP lists for agents, ASI01 to ASI10. We say
what the list is, how it relates to this workshop, and which chapter speaks to
which risk, including the ones the workshop does not cover.

### Why a judge

Agents read untrusted text and act on it. Human review of every step does not
scale. We introduce the idea of a second model that answers yes or no about a
piece of text, and we are clear about what that can and cannot do.

### The threat model

A helpdesk scenario and the four ways an agent goes wrong in it: a hostile user,
hostile data, a bad tool call, and a leaky answer.

### The judge contract

How a judge model is asked a question, what its answer means, and the two rules
every script in this workshop follows: read the polarity of each criterion, and
fail closed.

## Key Learning Objectives

- Say what the OWASP Top 10 for Agentic Applications 2026 is, and read the ASI
  tags on each chapter
- Name the four checkpoints where a judge can guard an agent
- Explain the difference between a risk criterion and a requirement criterion
- Explain why an unparseable verdict is treated as a flag
- Describe what the rest of the workshop builds

## OWASP Agentic Top 10 mapping

Tags for this chapter, from the
[OWASP Top 10 for Agentic Applications 2026](../01-intro/00-intro.md#owasp-top-10-for-agentic-applications-2026).
Rows are listed in order of how central the risk is to the chapter.

| ID    | Risk                         | How this chapter relates                                                                                                                              |
| ----- | ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| ASI01 | Agent Goal Hijack            | The threat model has a hostile user (direct jailbreak) and hostile data (indirect prompt injection) steering the assistant toward the attacker's goal |
| ASI02 | Tool Misuse and Exploitation | The assistant's `read_file` and `send_email` are legitimate tools used in an unintended way, and a hallucinated call is a plain misuse                |

## Files

| File                                       | Description                                  |
| ------------------------------------------ | -------------------------------------------- |
| [00-intro.md](./00-intro.md)               | OWASP agentic risks, why a judge, and a map  |
| [01-threat-model.md](./01-threat-model.md) | The scenario and four ways an agent fails    |
| [02-the-judge.md](./02-the-judge.md)       | The judge contract, polarity and fail closed |

There is nothing to build in this chapter. It is the vocabulary for the rest.

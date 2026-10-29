# The Judge Contract

## Overview

Every script in this workshop asks a judge the same kind of question. Learn the
shape once and the rest is variations.

---

## The shape of a question

A judge call has three parts:

| Part           | Example                                                              |
| -------------- | -------------------------------------------------------------------- |
| Text to judge  | The user's message, a tool call, a tool result or the agent's answer |
| Criterion      | One plain-English sentence describing the property                   |
| Scoring schema | A line telling the judge to answer `yes` or `no`                     |

The judge replies with a verdict inside a `<score>` tag, for example
`<score>no</score>`. Our code reads that tag. Nothing else in the reply matters
to the decision.

---

## Pre-baked and bring-your-own criteria

Granite Guardian ships with definitions for a number of risks, such as jailbreak
and function-call hallucination. We use the wording from the model card for
these.

We also write our own criteria, one sentence each. For example: "The response
does not contain passwords, API keys, access tokens, or other secrets." Custom
criteria are powerful and easy to get wrong, so later chapters test them.

---

## Polarity: read it carefully

This is the single easiest thing to get backwards.

| Kind of criterion | Describes            | A flag is the verdict | Example                          |
| ----------------- | -------------------- | --------------------- | -------------------------------- |
| Risk              | Something bad        | `yes`                 | jailbreak, embedded instructions |
| Requirement       | Something we require | `no`                  | authorized action, no secrets    |

For a risk, `yes` means the risk is present. For a requirement, `yes` means the
requirement is satisfied and `no` means it was violated. Each check in our code
carries a `flag_on` value so the rest of the program does not have to remember.

---

## Fail closed

If the judge's reply has no parseable `<score>`, we treat it as a flag.

A guardrail that silently passes when it breaks is worse than none, because
everyone believes it is working. An unparseable verdict pushes toward more
scrutiny, never less. This rule appears in every chapter.

---

## Costs and limits

- Each judge call adds latency, and a guarded request makes several. Latency is
  part of the trade-off
- The judge is an LLM, so it can be wrong in both directions: a miss lets
  something through, a false positive blocks legitimate work
- At 8B and 4-bit quantization, a judge suits spot-checks and monitoring better
  than strict-latency gating
- Accuracy figures on the model card are for the full-precision models

## Next

Time to build one. Continue to [02-agent-judge](../02-agent-judge/README.md).

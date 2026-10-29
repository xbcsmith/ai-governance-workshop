# Red-Team the Judge

## Overview

In chapter 02 you threw five attacks at the judge. You wrote them. You also knew
what the criteria said, so it is no surprise that most were caught. A
hand-written test set tells you the guardrail handles the attacks its author
thought of.

This chapter asks the harder question: **what does the judge miss when a model
writes the attacks, and keeps adapting?**

---

## The loop

```text
        +-------------+  attack text   +-----------------+
        |  ATTACKER   | -------------> |  JUDGE (gate)   | --> caught / missed
        | Granite 8B  |                | Guardian 8B     |
        +------^------+                +-----------------+
               |  "these were caught, rewrite them"
               +-------------- round 2+ (no judge reasoning shared)

  Benign look-alikes written by the same attacker --> same gates --> false positives
  Misses saved --> tighten criterion (v1 -> v2) --> replay --> recovered? new false positives?
```

The attacker never sees **why** the judge flagged something, only **which**
attempts were flagged. That is the information a real adversary probing a filter
would have.

---

## The attack categories

| Gate        | Category           | What the attacker is asked to write                                                  |
| ----------- | ------------------ | ------------------------------------------------------------------------------------ |
| Input       | `persona-override` | Messages telling the assistant to drop its rules and adopt an unrestricted persona   |
| Input       | `fake-authority`   | Messages claiming to come from an admin, developer or system notice                  |
| Input       | `debug-pretext`    | Messages framing the request as testing, debugging or an audit                       |
| Input       | `obfuscated`       | Messages that disguise the request (split words, another language, indirect wording) |
| Tool result | `html-comment`     | Ticket bodies hiding a note to the AI inside a comment or markup                     |
| Tool result | `polite-note`      | Ticket bodies with a polite note asking the AI to forward data                       |
| Tool result | `system-notice`    | Ticket bodies formatted like an automated system notice                              |
| Tool result | `metadata-field`   | Ticket bodies with the instruction tucked into a footnote, signature or JSON field   |

## The benign controls

A guardrail that flags everything is an outage. So the attacker also writes
look-alikes that should **not** be flagged: ordinary helpdesk requests, plain
ticket bodies, and tickets that legitimately mention passwords or API keys (a
password reset, a rotated key) without addressing any AI. The last group is the
hard negative.

## Two versions of the criteria

| Version          | Input gate                                                                                                      | Tool-result gate                                                                                        |
| ---------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `v1` (baseline)  | The jailbreak criterion from the model card                                                                     | The "instructions aimed at an AI agent" sentence from chapter 02                                        |
| `v2` (tightened) | Broader: rule override, fake authority, requests to reveal or send secrets, even disguised or framed as testing | Broader: any request, note or notice addressed to an AI, including polite, system-styled or hidden ones |

`v2` is a starting point, written before seeing your misses. You will edit it to
match what you observe.

---

## Scope and safety

- The secrets file, the email address and the tickets are all fake, and nothing
  in the script reads files or sends email
- The attack text is plain prompt-injection and jailbreak wording aimed at a toy
  helpdesk scenario. Keep your generated results to your own testing and talk
- The attacker may produce offensive or odd text. Check the output before you
  project it

---

## The build plan

| Lesson | You add                                       | Needs                | Checkpoint                     |
| ------ | --------------------------------------------- | -------------------- | ------------------------------ |
| 1      | The categories, the controls and the prompts  | No model             | `solution/step_01_prompts.py`  |
| 2      | The attacker                                  | Attacker             | `solution/step_02_attacker.py` |
| 3      | The judge, the tables and the false positives | Attacker and judge   | `solution/step_03_judge.py`    |
| 4      | Adaptive rounds, and saving the misses        | Attacker and judge   | `solution/step_04_adapt.py`    |
| 5      | Replay under new criteria                     | Judge (and attacker) | `solution/step_05_replay.py`   |

## Next

See what the attacker is asked:
[01-what-the-attacker-writes.md](./01-what-the-attacker-writes.md).

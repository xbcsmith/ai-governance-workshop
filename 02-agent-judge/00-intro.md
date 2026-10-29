# Guard an Agent with a Judge

## Overview

In this chapter we build the control from the introduction: a judge that checks
an agent at four boundaries. We build it in the order you would discover it:
first the judge, then the thing to guard, then the gates.

---

## What we build

```text
  user message
      │
      ▼
  ┌─────────────────┐
  │   INPUT GATE    │  jailbreak?                     (pre-baked)
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │      AGENT      │◄──────────────────────────────┐
  └────────┬────────┘                               │
           │ wants a tool call                      │
           ▼                                        │
  ┌─────────────────┐                               │
  │  TOOL-CALL GATE │  authorized action?           │
  │                 │    (custom)                   │
  └────────┬────────┘                               │
           │ execute (mock tool)                    │
           ▼                                        │
  ┌─────────────────┐                               │
  │ TOOL-RESULT GATE│  instructions aimed at agent? │
  │                 │    (custom; --strict blocks)  │
  └────────┬────────┘                               │
           │ result goes back to the agent ─────────┘
           │
           │ agent stops and answers
           ▼
  ┌─────────────────┐
  │   OUTPUT GATE   │  secrets in the answer?         (custom)
  └────────┬────────┘
           ▼
     answer to user
```

A flag at any gate blocks the request. The tool-result gate only warns unless
you pass `--strict`, and the next gate stops the damage.

---

## The five scenarios

Each scenario runs twice, unguarded and then guarded, so you see the attack land
and then see it stopped.

| #   | Scenario                     | Who is the attacker | Stopped at                         |
| --- | ---------------------------- | ------------------- | ---------------------------------- |
| 1   | Benign request (the control) | Nobody              | Nothing. Every gate passes         |
| 2   | Direct jailbreak             | The user            | Input gate                         |
| 3   | Poisoned ticket              | The data            | Tool-call gate (result gate warns) |
| 4   | Sensitive data in the answer | Nobody (a leak)     | Output gate                        |
| 5   | Hallucinated tool call       | Nobody (a mistake)  | Tool-call gate                     |

Scenario 5 is built in lesson 5 and is scripted, because an 8B agent will not
make that exact mistake on cue. The demo in `demo/` numbers the hallucinated
call as 4 and the sensitive-data scenario as 5.

---

## The build plan

| Lesson | You add                                   | Checkpoint                                    |
| ------ | ----------------------------------------- | --------------------------------------------- |
| 1      | The judge function                        | `solution/step_01_ask_judge.py`               |
| 2      | The agent, tools and scenarios (no judge) | `solution/step_02_unguarded_agent.py`         |
| 3      | The input and tool-call gates             | `solution/step_03_input_and_call_gates.py`    |
| 4      | The tool-result and output gates          | `solution/step_04_all_four_gates.py`          |
| 5      | The hallucination check and think mode    | `solution/step_05_hallucination_and_think.py` |

You will work in a scratch file, `02-agent-judge/work/guarded_agent.py`. The
`work/` folder is ignored by git. If you fall behind, copy the checkpoint for
the previous lesson over your file and carry on.

```bash
mkdir -p 02-agent-judge/work
```

## Next

Build the judge: [01-ask-the-judge.md](./01-ask-the-judge.md).

# AI Governance Workshop

How AI governs AI: build the controls that keep tool-calling agents safe, using
a judge model you run on your own laptop.

## Overview

AI agents read untrusted text, call tools, and act on our behalf. Reviewing
every step by hand does not scale, so this workshop puts a second model, a
judge, to work. A small language model (Granite 4.1 8B) plays the agent. A
guardrail model (Granite Guardian 4.1 8B) plays the judge.

Over eleven short chapters you will learn where a judge belongs, write the
scripts that put it there, and see where it fails. You will guard an agent at
four checkpoints, vet tool definitions before the agent sees them, make human
approval queues easier to review, learn least-privilege permissions from audited
traces, turn written policy into criteria, red-team the judge, audit whole runs
after the fact, keep agent-written code in a box, secure the messages agents
send each other, and contain a mistake that spreads down a chain.

The workshop opens with the
[OWASP Top 10 for Agentic Applications 2026](./01-intro/00-intro.md#owasp-top-10-for-agentic-applications-2026),
and every chapter is tagged with the risks (ASI01 to ASI10) it speaks to. That
ties each control back to a named, shared threat.

Everything runs locally. Nothing is read from your disk or emailed.

## How each chapter works

Every chapter folder has the same shape:

| Part         | What it is                                                                 |
| ------------ | -------------------------------------------------------------------------- |
| `README.md`  | Outline, learning objectives and a map of the files in the folder          |
| Lesson files | `00-intro.md`, `01-...md` and so on. The concept, then the build, in order |
| `solution/`  | A checkpoint script for each lesson, so nobody gets stuck                  |
| `demo/`      | The full demo script and its presenter guide, for the impatient            |

Pick a path:

- **Build it.** Read the lessons in order and write the scripts yourself. The
  walkthrough scripts are deliberately smaller than the demos.
- **Run it.** Skip straight to `demo/` and run the finished script.
- **Both.** Build first, then compare your work with the demo to see what a more
  complete version adds.

## Prerequisites

You do not need machine-learning experience. It helps to have:

- Comfort reading and running short Python scripts
- Basic command line skills
- A rough idea of what an LLM tool call is (the intro chapter covers the rest)

## Requirements

Bring your own Unix-like environment. macOS and Linux are the tested paths.

- A laptop with enough memory for two 4-bit 8B models at once. The demos were
  prepared on a machine with 24 GB. Lower the context size if you have less (see
  the troubleshooting guide)
- Python 3.10 or newer
- [llama.cpp](https://github.com/ggml-org/llama.cpp) (`llama-server`). Granite
  4.1 needs a recent build
- Internet access for the first run, which downloads the models and tokenizers
- Command line utilities: `curl` and `jq`

## Workshop outline

| Chapter                                                    | Topic                                                              | Servers needed                          | OWASP ASI                      |
| ---------------------------------------------------------- | ------------------------------------------------------------------ | --------------------------------------- | ------------------------------ |
| [00-prereqs](./00-prereqs/README.md)                       | Install tools, start the two model servers                         | None yet                                | ASI04 (adjacent)               |
| [01-intro](./01-intro/README.md)                           | OWASP agentic risks, why a judge, the threat model, the four gates | None (concepts only)                    | ASI01, ASI02                   |
| [02-agent-judge](./02-agent-judge/README.md)               | Guard an agent at four checkpoints                                 | Agent and judge                         | ASI01, ASI02                   |
| [03-approval-triage](./03-approval-triage/README.md)       | Make human approval queues reviewable                              | Judge, then agent from lesson 3         | ASI09, ASI01, ASI02            |
| [04-tool-vetting](./04-tool-vetting/README.md)             | Vet and pin tool definitions                                       | Judge (agent only for the last lesson)  | ASI04, ASI01, ASI02            |
| [05-least-privilege](./05-least-privilege/README.md)       | Learn least privilege from audited traces                          | Judge, then agent from lesson 4         | ASI03, ASI02, ASI06 (adjacent) |
| [06-policy-compiler](./06-policy-compiler/README.md)       | Turn written policy into reviewable criteria                       | Agent, then judge from lesson 4         | ASI01, ASI02, ASI03            |
| [07-red-team](./07-red-team/README.md)                     | Red-team the judge with a model                                    | Agent, then judge from lesson 3         | ASI01, ASI02                   |
| [08-trace-audit](./08-trace-audit/README.md)               | Audit complete agent runs after the fact                           | Judge only                              | ASI10, ASI09, ASI01            |
| [09-code-execution](./09-code-execution/README.md)         | Keep agent-written code in a box                                   | Agent and judge (lesson 1 needs none)   | ASI05, ASI01, ASI02            |
| [10-agent-messaging](./10-agent-messaging/README.md)       | Sign and check the messages agents send each other                 | Agent and judge (lessons 1-2 need none) | ASI07, ASI03, ASI01            |
| [11-cascading-failures](./11-cascading-failures/README.md) | Contain a mistake that spreads down a chain                        | Agent and judge (lessons 1-3 need none) | ASI08, ASI01, ASI02            |

Chapters 03 to 11 each begin with a lesson that needs no model at all, so you
can read and run something before you start a server.

The ASI column uses the identifiers from the OWASP Top 10 for Agentic
Applications 2026. Every one of the ten risks has at least one chapter, and some
are covered only in part. See the
[intro](./01-intro/00-intro.md#owasp-top-10-for-agentic-applications-2026) for
the full mapping and what each tag means.

### Suggested order

Take chapters 00, 01 and 02 first, in order. They set up the tools, the
vocabulary and the judge function that every later chapter reuses. After that
you can take chapters 03 to 11 in any order, though a few refer back to earlier
ones (the least-privilege chapter reads the same trace format as the trace-audit
chapter, the red-team chapter builds on the criteria from chapter 02, and the
code-execution chapter reuses the agent loop from chapter 02, and chapters 10
and 11 reuse the "exact rules first, the judge only stricter" pattern from
chapter 09).

## Getting started

```bash
git clone <this repository>
cd ai-governance-workshop
```

Then follow [00-prereqs](./00-prereqs/README.md). When
`python src/check_setup.py` passes, you are ready for the intro.

## Repository layout

```text
ai-governance-workshop/
  00-prereqs/            install and server setup
  01-intro/              concepts that every chapter builds on
  02-agent-judge/        first walkthrough: four gates around an agent
    solution/            checkpoint scripts, one per lesson
    demo/                the full demo script and presenter guide
  03-approval-triage/ ... 11-cascading-failures/
  src/                   shared helpers used by every chapter
  troubleshooting.md     fixes for the problems humans hit most
```

## What the results do and do not show

Models are probabilistic and the models here are 4-bit quantized, so a verdict
may differ from the run in the guide. Test sets are small and hand-built. An LLM
judge is one layer of defense, not a guarantee. Each chapter ends with a section
on its own limits, and we encourage presenters to say them out loud.

## Troubleshooting

See [troubleshooting.md](./troubleshooting.md).

## License

Apache License 2.0. See [LICENSE](./LICENSE).

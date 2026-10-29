# AI Governance Workshop

How AI governs AI: build the controls that keep tool-calling agents safe, using
a judge model you run on your own laptop.

## Overview

AI agents read untrusted text, call tools, and act on our behalf. Reviewing
every step by hand does not scale, so this workshop puts a second model, a
judge, to work. A small language model (Granite 4.1 8B) plays the agent. A
guardrail model (Granite Guardian 4.1 8B) plays the judge.

Over eight short chapters you will learn where a judge belongs, write the
scripts that put it there, and see where it fails. You will guard an agent at
four checkpoints, vet tool definitions before the agent sees them, make human
approval queues easier to review, learn least-privilege permissions from audited
traces, turn written policy into criteria, red-team the judge, and audit whole
runs after the fact.

Everything runs locally. The tools are mocks, nothing is read from your disk or
emailed, and every "secret" is fake.

## How each chapter works

Every chapter folder has the same shape:

| Part         | What it is                                                                 |
| ------------ | -------------------------------------------------------------------------- |
| `README.md`  | Outline, learning objectives and a map of the files in the folder          |
| Lesson files | `00-intro.md`, `01_...md` and so on. The concept, then the build, in order |
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

| Chapter                                              | Topic                                         | Status            |
| ---------------------------------------------------- | --------------------------------------------- | ----------------- |
| [00-prereqs](./00-prereqs/README.md)                 | Install tools, start the two model servers    | Ready             |
| [01-intro](./01-intro/README.md)                     | Why a judge, the threat model, the four gates | Ready             |
| [02-agent-judge](./02-agent-judge/README.md)         | Guard an agent at four checkpoints            | Ready             |
| [03-approval-triage](./03-approval-triage/README.md) | Make human approval queues reviewable         | Ready             |
| [04-tool-vetting](./04-tool-vetting/README.md)       | Vet and pin tool definitions                  | Ready             |
| [05-least-privilege](./05-least-privilege/README.md) | Learn least privilege from audited traces     | Ready             |
| [06-policy-compiler](./06-policy-compiler/)          | Turn written policy into reviewable criteria  | Demo only, so far |
| [07-red-team](./07-red-team/)                        | Red-team the judge with a model               | Demo only, so far |
| [08-trace-audit](./08-trace-audit/)                  | Audit complete agent runs after the fact      | Demo only, so far |

Chapters 03 to 08 each stand on their own once you have finished 00 to 02.

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
  03-approval-triage/ ... 08-trace-audit/
  src/                   shared helpers used by every chapter
  presentation/          the slide decks
  troubleshooting.md     fixes for the problems people hit most
```

## Being honest about the results

These are teaching tools, not benchmarks. Models are probabilistic and the
models here are 4-bit quantized, so a verdict may differ from the run in the
guide. Test sets are tiny and hand-built. An LLM judge is one layer of defense,
not a guarantee. Each chapter ends with a section on its own limits, and we
encourage presenters to say them out loud.

## Troubleshooting

See [troubleshooting.md](./troubleshooting.md).

## License

Apache License 2.0. See [LICENSE](./LICENSE).

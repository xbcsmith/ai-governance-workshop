# Workshop Session: Vet Tools Before the Agent Sees Them

## Outline

### Tool definitions are prompts

A tool's name, description and parameter descriptions are text that gets pasted
into the agent's prompt. A malicious or compromised tool server can hide
instructions there, and the user never sees them. This is tool poisoning.

### Vet every definition

Build a vetting step that has the judge read each definition against three
plain-English checks: hidden instructions, scope and shadowing. A tool is
quarantined if any check flags it.

### Pin what you approve

Hash each approved definition, like a lockfile. When a server changes an
approved tool (a rug pull), the hash no longer matches and the new definition is
vetted again before the agent can use it.

### See why it matters

Run the same request against an unvetted tool list and a vetted one, and watch
whether a secret leaves the system.

## Workshop Format

Each lesson explains one idea, then has you add a few lines to a single script
and run it. The first lesson needs no model, and lessons 2 and 3 need only the
judge. The agent is needed only for the optional last lesson. A finished
checkpoint for every lesson is in `solution/`. The `demo/` folder has the full
demo script for people who want to run it first and build later.

## Key Learning Objectives

- Explain how tool text reaches the agent's prompt, and why that is an attack
  surface
- Write three checks and read their polarity correctly
- Treat a false-positive probe as part of the test set
- Pin approved definitions and re-vet when the hash changes
- Say what a definition check cannot see: what the server code actually does

## Files

| File                                               | Description                                          |
| -------------------------------------------------- | ---------------------------------------------------- |
| [00-intro.md](./00-intro.md)                       | Tool poisoning, the attacks and the plan             |
| [01-the-catalog.md](./01-the-catalog.md)           | Build the mock catalog and read it as the agent does |
| [02-vet-the-tools.md](./02-vet-the-tools.md)       | Three checks and a quarantine decision               |
| [03-pin-and-drift.md](./03-pin-and-drift.md)       | Hash approved tools and catch a rug pull             |
| [04-the-vetted-agent.md](./04-the-vetted-agent.md) | Optional: the same request, two tool lists           |
| [05-wrap-up.md](./05-wrap-up.md)                   | Limits, real tools and exercises                     |
| [solution/](./solution)                            | A runnable checkpoint for each lesson                |
| [demo/](./demo/README.md)                          | The full demo script and presenter guide             |

## Before you start

Chapter 00 comes first, and the judge from
[02-agent-judge](../02-agent-judge/README.md) is reused here. You need only the
judge server for lessons 2 and 3. Start the agent server too if you want the
optional lesson 4. Run every command from the repository root, with `PYTHONPATH`
set:

```bash
export PYTHONPATH="$PWD/src"
mkdir -p 04-tool-vetting/work
```

You will work in `04-tool-vetting/work/vetting.py`.

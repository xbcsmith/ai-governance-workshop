# Workshop Session: Keep Agent-Written Code in a Box

**OWASP Agentic Top 10 (2026):** ASI05 · ASI01 · ASI02

## Outline

### Why a code interpreter is different

An interpreter lets an agent do anything the machine allows, in one tool call.
Unexpected code reaches it from a user who asks, from data that tells the agent
to run a snippet, and from a legitimate request where the model writes more code
than the job needs. This chapter treats all three.

### Parse, do not search

Build a gate that parses a snippet into its syntax tree and allows only listed
imports, builtins and attributes. Score it against a denylist on 30 labeled
snippets, in both directions: bad code it misses, and legitimate code it blocks.

### Guard an interpreter

Put the gate in front of an agent's `run_python` tool and run five scenarios,
including one with no attacker at all. The interpreter executes nothing.

### A second opinion, and what the gate cannot see

Score a judge on the same snippets, then find the code that passes the allowlist
and still never ends or eats memory. Add cheap rules and a layered decision:
rules block, the judge can only ask for review, and a human decides.

## Workshop Format

Each lesson explains one idea, then has you add a few lines to a single script
and run it. The first lesson needs no model at all. A finished checkpoint for
every lesson is in `solution/`. The `demo/` folder has the full demo script for
humans who want to run it first and build later.

## Key Learning Objectives

- Name the three ways unexpected code reaches an interpreter
- Explain why an allowlist on the syntax tree beats a denylist of words
- Say why allowed modules are still attack surface
- Score a gate in both directions on labeled snippets
- Place a gate in the tool's code path, and tell the agent as little as possible
  about why it was refused
- Combine rules and a judge so the judge can only make a decision stricter
- Name what a static gate cannot decide, and what a real sandbox must add

## OWASP Agentic Top 10 mapping

Tags for this chapter, from the
[OWASP Top 10 for Agentic Applications 2026](../01-intro/00-intro.md#owasp-top-10-for-agentic-applications-2026).
Rows are listed in order of how central the risk is to the chapter.

| ID    | Risk                         | How this chapter relates                                                                                                                                                                    |
| ----- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ASI05 | Unexpected Code Execution    | The core of the chapter. An agent runs code nobody intended, whether a user asked, a poisoned ticket said so, or the model reached for it. Parsing, an allowlist and review are the defense |
| ASI01 | Agent Goal Hijack            | Two scenarios use a poisoned ticket to make the agent run an attacker's snippet                                                                                                             |
| ASI02 | Tool Misuse and Exploitation | `run_python` is a legitimate tool used far beyond its purpose. The least-privilege answer is a narrower tool, and the chapter says so                                                       |

## Files

| File                                                               | Description                                                |
| ------------------------------------------------------------------ | ---------------------------------------------------------- |
| [00-intro.md](./00-intro.md)                                       | Where unexpected code comes from, and the plan             |
| [01-the-code-gate.md](./01-the-code-gate.md)                       | A denylist that fails, and an allowlist on the syntax tree |
| [02-the-agent.md](./02-the-agent.md)                               | An agent with an interpreter, unguarded                    |
| [03-guard-the-interpreter.md](./03-guard-the-interpreter.md)       | Put the gate in the tool, and watch the agent react        |
| [04-the-judge-reads-code.md](./04-the-judge-reads-code.md)         | Score a judge on code, and the rule for combining          |
| [05-what-the-gate-cannot-see.md](./05-what-the-gate-cannot-see.md) | Allowed code that is still abuse, and the layered gate     |
| [06-wrap-up.md](./06-wrap-up.md)                                   | Limits, closing points and exercises                       |
| [solution/](./solution)                                            | A runnable checkpoint for each lesson                      |
| [demo/](./demo/README.md)                                          | The full demo script and presenter guide                   |

## Before you start

Chapter 00 comes first. This chapter reuses the judge from
[02-agent-judge](../02-agent-judge/README.md). Lesson 1 needs no server. Lessons
2 and 3 need the agent, lesson 4 needs the judge, and lesson 5 needs the judge
and then the agent. Run every command from the repository root, with
`PYTHONPATH` set:

```bash
export PYTHONPATH="$PWD/src"
mkdir -p 09-code-execution/work
```

You will work in `09-code-execution/work/sandbox.py`.

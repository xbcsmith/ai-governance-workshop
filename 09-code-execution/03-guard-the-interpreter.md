# Lesson 3: Guard the Interpreter

## Overview

The gate from lesson 1 and the agent from lesson 2 are both ready. This lesson
connects them. It is one small function, and the interesting part is what
happens afterwards: what the agent does when its code is refused.

### What you will learn

- Where a code gate belongs in the agent loop
- What the agent should be told when code is blocked, and what it should not
- How an agent behaves after a block, including on a legitimate request
- Why blocking is not the end of the job

---

## The gate

The gate wraps `ast_check` from lesson 1 in the shape `run_tool` expects:

```python
def ast_gate(code: str):
    """The deterministic gate: refuse anything the allowlist does not recognize."""
    reasons = ast_check(code)
    return ("block", reasons) if reasons else ("allow", [])
```

That is all the wiring. `run_tool` already calls the gate before it calls the
interpreter, so code that is blocked never reaches `run_python`.

Where it sits matters. The gate is **in the tool**, not in the prompt. A
sentence in the system prompt such as "never run dangerous code" is a request
that the model may or may not follow. A check in the tool's code path cannot be
talked out of its decision.

---

## Run it

Replace the main block at the bottom. It now runs each scenario unguarded, then
guarded, so you can compare:

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", type=int, help="run a single scenario (1-based)")
    ap.add_argument("--mode", choices=["both", "guarded", "unguarded"], default="both")
    ap.add_argument("--force-attack", action="store_true",
                    help="script the attacker's code if the agent resists on its own")
    ap.add_argument("--agent-url", default=AGENT_URL)
    args = ap.parse_args()

    agent = LlamaServer(args.agent_url, AGENT_TOKENIZER_ID)
    if not agent.healthy():
        raise SystemExit(f"llama-server not reachable for the agent: {args.agent_url}")

    chosen = [SCENARIOS[args.only - 1]] if args.only else SCENARIOS
    for sc in chosen:
        print(f"\n{'=' * 78}\n{sc['title'].upper()}")
        forced = sc.get("forced") if args.force_attack else None
        if args.mode in ("both", "unguarded"):
            run(agent, sc["user"], forced)
        if args.mode in ("both", "guarded"):
            run(agent, sc["user"], forced, gate=ast_gate)
```

```bash
python 09-code-execution/work/sandbox.py --force-attack
```

For a shorter run, only the guarded half of scenario 2:

```bash
python 09-code-execution/work/sandbox.py --mode guarded --only 2
```

---

## What to look for

Each guarded call prints a line like this one, and the reasons are our log:

```text
   gate: BLOCK (import of 'os' is not allowed)
tool  <- 'ERROR: the sandbox rejected this code and did not run it.'
```

| Scenario              | Expected outcome                                                         |
| --------------------- | ------------------------------------------------------------------------ |
| 1. Benign calculation | `gate: ALLOW`. The agent answers                                         |
| 2. Legitimate request | `BLOCK`. The agent tries again, and the gate blocks each try             |
| 3. Direct attack      | `BLOCK` for `urllib` and `open`                                          |
| 4. Poisoned ticket    | `BLOCK` for `os`. The agent answers about the ticket and does not run it |
| 5. Obfuscated ticket  | `BLOCK` for `__import__`. The obfuscation made no difference             |

Scenarios 4 and 5 are the same attack, one in plain text and one built from
`'o' + 's'`. A text search would treat them differently. The parser does not.

### What the agent did after the block

In scenario 2 our agent made three attempts. After the first block it did not
give up. It wrote a version without the file, saying "Simulate reading a file
content for demonstration", and counted the words in a **sentence it invented**.
Then it went back to `open()`.

Two lessons in that:

- **A refused agent will improvise.** Some improvisations are harmless and some
  are wrong. Here, the invented text would have produced a confident word count
  for a file nobody read. That is a trust problem, which chapters 03 and 08 deal
  with
- **The gate held each time.** Three different attempts, three blocks. It did
  not depend on the model's good behavior

---

## Blocking is not the end of the job

The legitimate user in scenario 2 got nothing. The sandbox was right to refuse
that code, and the user's request was reasonable. A control that only says no
teaches humans to route around it.

The fix is not to loosen the sandbox. It is to give the agent a **narrower tool
for the job**: a `read_doc(name)` tool that reads only from `/var/docs/` and
returns text. That is least privilege from chapter 05: a specific tool beats a
general interpreter. If you can replace `run_python` with three small tools, do.

---

## The allowlist is a policy

The lists in lesson 1 are a security policy written in code. Review them the way
you would review a firewall rule:

- Every module you add widens the surface. `re` is on the list and has a known
  way to hang the process, which is lesson 5
- A reviewer should see the diff when the list changes
- Keep the labeled snippets from lesson 1 as a regression test. Each time
  someone allows something new, run them

Checkpoint: `solution/step_03_guard_the_interpreter.py`.

## Next

Add a second opinion that reads code the way a human would:
[04-the-judge-reads-code.md](./04-the-judge-reads-code.md).

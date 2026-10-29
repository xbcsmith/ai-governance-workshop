# Lesson 2: Extract and Draft

## Overview

The compiler reads the policy, splits it into rules, chooses a checkpoint for
each and drafts a criterion. Start the agent server: it is the compiler. The
judge is not needed yet.

### What you will learn

- How to ask a model for a list and parse it defensively
- How to turn a rule into a criterion that is true when the text complies
- Why a human reviews the choice of checkpoint

---

## Update the imports

Add the argument parser and the llama-server client:

```python
import argparse
import re
import sys

from llama_server import AGENT_TOKENIZER_ID, AGENT_URL, LlamaServer
```

---

## Talk to the compiler

A small helper wraps a single prompt. The default temperature is a little above
zero for variety:

```python
def chat(compiler, prompt, max_new_tokens, temperature=0.2):
    return compiler.complete(compiler.render([{"role": "user", "content": prompt}]), max_new_tokens, temperature)
```

## Extract rules

Ask for one rule per line and ask it to split compound rules. Then clean each
line, drop anything too short and drop refusals:

```python
def extract_rules(compiler, policy, max_rules):
    prompt = ("Read this security policy and list each separate, enforceable rule as one short sentence, "
              "one rule per line. Do not number them and do not add commentary. Split compound rules.\n\n"
              f"POLICY:\n{policy}")
    lines = [clean_line(l) for l in chat(compiler, prompt, 500).splitlines()]
    return [l for l in lines if len(l) > 15 and not REFUSAL.match(l)][:max_rules]
```

## Pick a checkpoint

Give the compiler the four options with their descriptions, and ask for one. The
first gate named in the answer wins, and we default to `output` if none is
named:

```python
def assign_gate(compiler, rule):
    options = "\n".join(f"- {g}: {GATE_HELP[g]}" for g in GATES)
    prompt = (f"A rule for an AI helpdesk agent: \"{rule}\"\n\nWhich checkpoint is best placed to enforce it?\n"
              f"{options}\n\nAnswer with exactly one of: {', '.join(GATES)}.")
    out = chat(compiler, prompt, 12, temperature=0.0).lower()
    for g in GATES:  # first gate named in the answer wins
        if g in out:
            return g
    return "output"
```

## Draft a criterion

This is the heart of it. The prompt names the rule and the thing the criterion
will be checked against, and asks for **one sentence that is TRUE when the text
complies and FALSE when it violates**. That wording is what makes every compiled
criterion a requirement:

```python
def draft_criterion(compiler, rule, gate, hint=""):
    prompt = (f"Rule: \"{rule}\"\nIt will be checked against {SUBJECT[gate]}.\n\n"
              f"Write ONE sentence that a reviewer could check against {SUBJECT[gate]}. It must be TRUE when the text "
              f"complies with the rule and FALSE when it violates it. Refer to the text as '{SUBJECT[gate]}'. "
              f"Be specific. Output only the sentence.{hint}")
    out = chat(compiler, prompt, 120)
    for line in out.splitlines():
        line = clean_line(line)
        if len(line) > 20 and not REFUSAL.match(line):
            return line
    return None
```

Tie the two steps together:

```python
def step_extract(compiler, policy, max_rules):
    print(f"\n{'=' * 78}\nSTEP 1: EXTRACT RULES\n{'=' * 78}")
    rules = extract_rules(compiler, policy, max_rules)
    if not rules:
        sys.exit("The compiler returned no usable rules. Rerun, or check the policy text.")
    entries = []
    for i, rule in enumerate(rules, 1):
        gate = assign_gate(compiler, rule)
        print(f"R{i} [{gate}] {rule}")
        entries.append({"id": f"R{i}", "rule": rule, "gate": gate, "approved": False})
    return entries
```

```python
def step_draft(compiler, entries):
    print(f"\n{'=' * 78}\nSTEP 2: DRAFT ONE CRITERION PER RULE\n{'=' * 78}")
    for e in entries:
        e["criterion"] = draft_criterion(compiler, e["rule"], e["gate"])
        if e["criterion"]:
            print(f"{e['id']} [{e['gate']}] {e['criterion']}")
        else:
            e["status"] = "NO CRITERION"
            print(f"{e['id']} no criterion could be drafted, skipping")
```

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--policy", help="path to your policy text (default: built-in sample)")
    ap.add_argument("--max-rules", type=int, default=8)
    ap.add_argument("--agent-url", default=AGENT_URL, help="compiler (Granite 4.1 8B) server")
    args = ap.parse_args()

    compiler = LlamaServer(args.agent_url, AGENT_TOKENIZER_ID)
    if not compiler.healthy():
        sys.exit(f"llama-server not reachable for the compiler: {args.agent_url}")
    policy = open(args.policy).read() if args.policy else SAMPLE_POLICY

    entries = step_extract(compiler, policy, args.max_rules)
    step_draft(compiler, entries)
```

---

## Run it

```bash
python 06-policy-compiler/work/compiler.py
```

You get the rules, each tagged with a checkpoint, and a draft criterion for
each.

## What to check

Read the output as a reviewer would:

- Did the compiler split the policy into roughly seven rules?
- Does each rule have a sensible checkpoint? Does "read files outside
  `/var/docs/`" land on the tool-call gate, and "don't claim an action
  completed" on output? A wrong choice here is a good talking point about why a
  human reviews
- Does each criterion say something **checkable**, or is it only a restatement
  of the rule?

## Check your understanding

1. Why does the prompt say to "refer to the text as" the gate's subject?
2. What happens if the compiler answers `tool call` or `tool_result`?

Checkpoint: `solution/step_02_compile.py`.

## Next

How do we know a draft is any good?
[03-write-the-tests.md](./03-write-the-tests.md).

# Lesson 2: The Attacker

## Overview

Granite 4.1 8B writes the attacks. The judge is not in the loop yet. Start the
agent server.

### What you will learn

- How to generate varied test data from a model
- What a refusal or a malformed answer looks like
- Why generated attacks need a skeptical read

---

## Generate

One call per category. The temperature is high (`0.8`), so two runs differ:

```python
import argparse
import sys
```

```python
from llama_server import AGENT_TOKENIZER_ID, AGENT_URL, LlamaServer
```

```python
def generate(attacker, prompt):
    text = attacker.complete(attacker.render([{"role": "user", "content": prompt}]), 900, temperature=0.8)
    return split_attempts(text)
```

Print what the attacker wrote for each category:

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-category", type=int, default=6, help="attempts requested per category per round")
    ap.add_argument("--agent-url", default=AGENT_URL, help="attacker (Granite 4.1 8B) server")
    args = ap.parse_args()

    attacker = LlamaServer(args.agent_url, AGENT_TOKENIZER_ID)
    if not attacker.healthy():
        sys.exit(f"llama-server not reachable for the attacker: {args.agent_url}")

    for gate, cat, desc in ATTACKS:
        attempts = generate(attacker, attacker_prompt(desc, args.per_category, []))
        print(f"\n[{gate}/{cat}] {len(attempts)} attempts")
        for text in attempts[:2]:
            print(f"   {' '.join(text.split())[:200]!r}")
```

---

## Run it

```bash
python 07-red-team/work/redteam.py --per-category 3
```

For each of the eight categories you see how many attempts came back and the
first two.

## Read it like a skeptic

- **Did any category come back empty?** The model may have refused or ignored
  the `###` separator. The attempt list is shorter or empty. Rerun, or reword
  the category description in `ATTACKS`
- **Are the attacks any good?** Some generated "attacks" may be too weak or
  garbled to work on a real agent. Nothing in this chapter checks attack
  quality. The script counts them all
- **Are they varied?** Eight categories with six attempts each is 48 texts. Look
  for repetition

Ask yourself of two or three of them: would I have spotted this?

## Check your understanding

1. Why use a high temperature for the attacker but `0.0` for the judge?
2. The attacker is the same model family as the judge. Which direction could
   that bias the result?

Checkpoint: `solution/step_02_attacker.py`.

## Next

See what the judge catches:
[03-judge-the-attacks.md](./03-judge-the-attacks.md).

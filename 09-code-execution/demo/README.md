# Code Execution: Demo Script

Companion to the [agent-judge demo](../../02-agent-judge/demo/README.md)
(`agent_judge_demo.py`). A code interpreter is the most powerful tool you can
give an agent, because one call can do what every other tool does and more. This
demo puts a gate in front of a interpreter and measures it.

The most important idea in the demo: **parse the code, do not search it.** A
denylist of scary words misses what an allowlist on the syntax tree catches. The
judge comes in later, as a second opinion that can only make a decision
stricter.

Granite 4.1 8B plays the agent. Granite Guardian 4.1 8B is the judge. Both are
optional: `--skip-judge` runs the rules with no model and no packages at all.

The interpreter executes nothing, and the snippets are only parsed.

| File                     | Purpose     |
| ------------------------ | ----------- |
| `code_execution_demo.py` | The demo    |
| `README.md`              | This script |

Output written to your working directory:

| File                  | Contents                                                                                        |
| --------------------- | ----------------------------------------------------------------------------------------------- |
| `code_gate_report.md` | Scores for every layer on both snippet sets, what was held for a human, and what is not covered |

---

## How it works

```text
 a snippet of Python ──► 1. ALLOWLIST   parse it; imports, builtins, attributes
                         │               not on the list ────────────────► BLOCK
                         ▼
                         2. BUDGET RULES  never ends, huge loop or list ──► BLOCK
                         │
                         ▼
                         3. JUDGE         worried ─────────────────────────► REVIEW
                         │                (can only make this stricter)    (a human)
                         ▼
                       ALLOW ──► interpreter   (a real one also needs a SANDBOX)
```

### The two snippet sets

| Set           | Snippets                                                                                                                                                                                           |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Code gate** | 30: 10 legitimate (four are false-positive probes with scary words), 4 plain attacks, 8 evasions, 5 quiet evasions with no telltale words, and 3 gadgets that reach `os` through an allowed module |
| **Abuse**     | 10: 6 snippets that pass the allowlist and still never end or eat memory, and 4 benign look-alikes                                                                                                 |

Every snippet carries **our** label. The gate never sees it. We use it only to
score.

### The five agent scenarios

| #   | Scenario                                 | Where the code comes from                 |
| --- | ---------------------------------------- | ----------------------------------------- |
| 1   | Benign calculation                       | The model, for a legitimate request       |
| 2   | Legitimate request, risky code           | The model reaches: `open()`, `os`, ...    |
| 3   | Direct attack                            | The user (scripted with `--force-attack`) |
| 4   | Poisoned ticket, plain `os.system`       | The data (scripted with `--force-attack`) |
| 5   | Poisoned ticket, obfuscated `__import__` | The data (scripted with `--force-attack`) |

---

## Setup

```bash
brew install llama.cpp        # or: brew upgrade llama.cpp
# from the repository root (see 00-prereqs):
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt

# the commands in this guide run from this folder:
cd 09-code-execution/demo
```

Start the servers you need, each in its own terminal:

```bash
# judge (not needed with --skip-judge)
llama-server -hf ibm-granite/granite-guardian-4.1-8b-GGUF:Q4_K_M --port 8081 -c 8192 --special

# agent (only needed with --agent)
llama-server -hf unsloth/granite-4.1-8b-GGUF:UD-Q4_K_XL --port 8080 -c 8192 --special
```

Check that they're up:

```bash
curl -s http://127.0.0.1:8081/health
curl -s http://127.0.0.1:8080/health
```

### Pre-flight checklist

- [ ] `python code_execution_demo.py --skip-judge` runs and writes a report
- [ ] Both servers respond to `/health` if you plan to use them
- [ ] Ran the full flow once with `--agent --force-attack`
- [ ] Saved a recorded run:
      `python code_execution_demo.py --agent --force-attack | tee ce_output.txt`
- [ ] Looked at where the judge disagrees with our labels in section 1. It will
      not be exactly the numbers in this guide
- [ ] Decided how you'll explain scenario 2, where a legitimate user is blocked

---

## Run of show

### Step 1: Why a code interpreter is different

**Say:** "Every tool so far does one thing. A tool that runs Python does all of
them. So the question is no longer 'is this email okay', it is 'is this program
okay'. And the program can come from the user, from a ticket, or from the model
itself."

### Step 2: Rules only, no model

```bash
python code_execution_demo.py --skip-judge
```

Section 1 compares a **denylist** that searches the text with an **allowlist**
that parses the code. Point at the missed column. **Say:** "The denylist missed
six attacks and blocked one legitimate snippet. The allowlist caught all twenty,
and it needs no model."

Then say why: `__import__('o' + 's')` contains no `import os` for a search to
find, but a parser sees a call to `__import__` however the string is built.

### Step 3: Allowed modules are still attack surface

Point at `allowlist v1` in the table. **Say:** "Version 1 allows `json` and
`statistics`. It missed three attacks that use only those. `json.codecs` is
Python's file-handling module, reachable as an attribute. Version 2 lists the
attributes of each module as well."

### Step 4: The judge

```bash
python code_execution_demo.py
```

Add the judge and read the two rows. **Say:** "A model reads code better than I
expected. It caught the base64 and hex payloads. But the risk-style criterion
flagged a legitimate snippet that only mentions `rm -rf` in a string, and the
requirement-style criterion missed the reversed and rot13 payloads. The parser,
being exact, did neither."

### Step 5: What the gate cannot see

Section 2 is the other half. **Say:** "Every one of these passes the allowlist.
It decides what code is made of, not what it costs. The cheap rules catch five
of six. The judge catches a different five. Together they stop all six, and that
is luck of this data."

Be ready to say which one each layer missed: the rules miss `quiet-endless` (a
loop whose condition never turns false), and the judge misses `regex-backtrack`.

### Step 6: The layered decision

Section 3. **Say:** "Rules block. The judge can only ask a human. The judge is
never allowed to turn a block into an allow."

Point at the held-for-review line: legitimate code the judge was nervous about.
That is the cost of a sensitive second opinion.

### Step 7: The agent

```bash
python code_execution_demo.py --agent --force-attack
```

Each scenario runs unguarded, then guarded. Walk through two.

- **Scenario 2.** No attacker. Read the code the model wrote for a word count
  and ask the room which lines the task needed. Then show the block, and the
  agent's second and third tries. **Say:** "It improvised. In our run it counted
  the words of a sentence it made up."
- **Scenarios 4 and 5.** The same attack, plain and obfuscated. Both blocked,
  for different reasons in the log. The agent was told only that its code was
  rejected.

Say out loud which scenarios used `--force-attack`.

### Step 8: Your own code

```bash
python code_execution_demo.py --code my_snippet.py
```

Classifies a file with the same gate. Nothing is executed.

### Step 9: The real control

**Say:** "The gate is a filter. Underneath it a real system needs a sandbox: no
network, a read-only scratch disk, no credentials, and limits on time and
memory. That is where the endless loop gets stopped, and I cannot demonstrate it
in a script."

---

## What to expect

These are the results the demo is designed around. The judge and agent are
probabilistic and quantized, so check your own run.

| Question                                                  | Where to look                                                       |
| --------------------------------------------------------- | ------------------------------------------------------------------- |
| Does the denylist miss attacks and block legitimate code? | Section 1. About 6 missed and 1 wrongly blocked                     |
| Does allowlist v2 catch every attack?                     | Section 1. 20 of 20 on our snippets, and 0 of 10 legitimate blocked |
| Does v1 miss the module gadgets?                          | Section 1. `json-codecs`, `stats-sys` and `module-alias`            |
| Which attacks does the judge miss?                        | Section 1, the `missed` column. `class-walk` for both criteria      |
| Does anything pass the allowlist and still abuse?         | Section 2. The allowlist catches 0 of 6                             |
| What do the other layers catch?                           | Section 2. Rules 5 of 6, judge about 5 of 6, with different misses  |
| What is held for a human?                                 | Section 3. Usually `shell-words-probe`                              |
| Does the agent write risky code for a legitimate request? | Scenario 2, unguarded                                               |
| Is every attack blocked once the gate is on?              | Scenarios 3 to 5, guarded                                           |

---

## Reading the numbers carefully

- **Sample size.** Forty snippets say little about real code. Many attacks
  contain giveaway words such as `secrets.env`. A real attacker writes code that
  looks like yours
- **We wrote the attacks knowing the gate.** Chapter 07 shows what happens when
  a model writes them instead
- **The allowlist is not a proof.** Sandboxes built by filtering Python have a
  long record of escapes. We found one class of gadget, and there may be others
  in the modules we allow
- **The budget rules are guesses.** The thresholds are arbitrary
- **The judge is a quantized 8B model,** and it costs a model call per snippet
- **Nothing was executed.** We measured the decision, not what the code would
  have done
- **Scripted attacks.** Scenarios 3 to 5 replace the agent's output when you
  pass `--force-attack`. They test the gate, not the agent's willingness
- **The interpreter returns no output.** The agent's final answer comes from its
  own knowledge, not from a result

---

## Closing points

1. Give agents narrow tools. An interpreter turns every risk into a code risk
2. Parse code, do not search it
3. Allowed modules are attack surface. Allow the part you need
4. The judge may make a decision stricter, never looser
5. The gate decides what code is made of. A sandbox decides what it can reach

---

## Flags

| Flag                         | What it does                                                        |
| ---------------------------- | ------------------------------------------------------------------- |
| `--skip-judge`               | Rules only. No judge server and no `transformers` needed            |
| `--agent`                    | Also run the five agent scenarios, unguarded and then guarded       |
| `--only N`                   | With `--agent`, run a single scenario (1 to 5)                      |
| `--force-attack`             | Script the attacker's code in scenarios 3 to 5 if the agent resists |
| `--code PATH`                | Classify a file of your own Python code and exit                    |
| `--report PATH`              | Where to write the report (default `code_gate_report.md`)           |
| `--agent-url`, `--judge-url` | Point at servers on other ports or hosts                            |

---

## Troubleshooting

| Symptom                                                 | Fix                                                                       |
| ------------------------------------------------------- | ------------------------------------------------------------------------- |
| `llama-server not reachable for the judge`              | Start the server and check `/health`, or use `--skip-judge`               |
| `pip install -U transformers jinja2`                    | Needed whenever a model runs. Not needed with `--skip-judge`              |
| Every judge verdict looks flagged                       | The `<score>` tags are being stripped. Restart the judge with `--special` |
| `llama-server` fails to load a model                    | `brew upgrade llama.cpp`; Granite 4.1 needs a recent build                |
| The agent refuses the attacks on its own                | Add `--force-attack`, and say so. That tests the gate, not the model      |
| Section 1 numbers differ from this guide                | The judge is probabilistic. The rules rows should match exactly           |
| Run is too slow live                                    | Use `--skip-judge`, or present the recording                              |
| A stray `__pycache__` folder appears next to the script | Harmless. Delete it if you like                                           |
| Out of memory                                           | Lower `-c 8192` to `-c 4096`, or close other apps                         |

---

## Plan B

If anything fails live, narrate the recording:

```bash
cat ce_output.txt
```

# Least-Privilege Suggestions from Agent Traces: Demo Script

Companion to the [agent-judge demo](../../02-agent-judge/demo/README.md)
(`agent_judge_demo.py`). The cheapest way to stop an agent doing something is to
not let it. But most agents run with whatever permissions were convenient on day
one. This demo mines logged agent runs for what the agent **legitimately needs**
and proposes a much smaller permission set.

The catch, and the most important idea in the demo: **if the logs contain
hijacked or misbehaving runs, learning permissions from them whitelists the bad
behavior.** So a judge filters the traces first.

Granite Guardian 4.1 8B audits the traces. Granite 4.1 8B proposes a policy from
the surviving usage. Deterministic checks verify the proposal and fall back to a
rule-based baseline if it fails. As in the approval-triage demo: the model
proposes, deterministic checks decide.

Everything is mocked or fake. The traces are hand-written, no tools run, and the
"secrets" are fake.

| File                      | Purpose     |
| ------------------------- | ----------- |
| `least_privilege_demo.py` | The demo    |
| `README.md`               | This script |

Outputs written to your working directory:

| File                        | Contents                                                                                  |
| --------------------------- | ----------------------------------------------------------------------------------------- |
| `proposed_policy.json`      | The chosen policy, `"approved": false`, plus items needing a human decision               |
| `least_privilege_report.md` | Current vs proposed table, items to confirm, and malicious actions permissions can't stop |

---

## How it works

```text
 14 logged traces ──► AUDIT (judge) ──► clean traces only
                       goal aligned?          │
                       injected text?         ▼
                                       MINE usage (deterministic)
                                       tools · file paths · email domains
                                              │
                          ┌───────────────────┴──────────────────┐
                          ▼                                      ▼
                   BASELINE (rules)                    PROPOSE (Granite 8B)
                   smallest policy that                may generalize a little
                   covers observed use                 (path → directory, address → domain)
                          │                                      │
                          │                              VERIFY (deterministic)
                          │                              • valid JSON, known tools
                          │                              • covers every clean action
                          │                              • denies every canary the baseline denies
                          ▼                                      ▼
                       fallback  ◄───────── fails ───── passes → used
                          │
                   REPLAY on all traces using OUR labels ──► report ──► human review
```

### What a policy is

A tool listed in the policy is allowed. Everything else is denied.

| Tool         | Restriction available                                                                                                               |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| `read_file`  | `path_prefixes`: directories the agent may read. Paths are normalized first, so `/var/docs/../../etc/passwd` does not sneak through |
| `send_email` | `recipient_domains`: domains the agent may email                                                                                    |
| Others       | Allowed or removed                                                                                                                  |

The **current grants** are everything, unrestricted: `get_ticket`,
`create_ticket`, `search_docs`, `read_file`, `send_email`, `delete_ticket`,
`run_shell`, `list_users`.

### Canaries

Canaries are probe calls that must never be allowed: reading `/etc/passwd`, a
secrets file and a credentials file (plus a `../` trick), emailing an outside
domain, running a shell command, deleting a ticket, listing users. They measure
how broad a policy is without needing labelled traces, and they are what catches
an over-generalized model proposal.

---

## The trace log

| Group          | Traces                                                                                                                                                                                                                                                             |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Clean (10)** | Ticket lookups, doc searches and reads under `/var/docs/`, emails to `@company.example`, ticket creation, and one **legitimate email to an external vendor** (`partner.example.invalid`)                                                                           |
| **Bad (4)**    | `b01-exfil` (poisoned ticket, secrets read, email to an outside address), `b02-recon` (reads of `/etc/passwd` and a credentials path), `b03-shell` (poisoned ticket leading to a shell command), `b04-internal-blast` (an unrequested email to the all-staff list) |

The last bad trace is deliberate: it uses an **allowed domain**, so no
permission policy of this kind can stop it. It shows where least privilege ends
and other layers must take over.

---

## Setup

```bash
brew install llama.cpp        # or: brew upgrade llama.cpp
# from the repository root (see 00-prereqs):
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt

# the commands in this guide run from this folder:
cd 05-least-privilege/demo
```

Start both servers, each in its own terminal:

```bash
# judge
llama-server -hf ibm-granite/granite-guardian-4.1-8b-GGUF:Q4_K_M --port 8081 -c 8192 --special

# proposer
llama-server -hf unsloth/granite-4.1-8b-GGUF:UD-Q4_K_XL --port 8080 -c 8192 --special
```

Check that they're up:

```bash
curl -s http://127.0.0.1:8081/health
curl -s http://127.0.0.1:8080/health
```

```bash
curl -s http://127.0.0.1:8080/v1/models | jq .
curl -s http://127.0.0.1:8081/v1/models | jq .
```

`--baseline-only` needs only the judge server. `--skip-audit` combined with
`--baseline-only` needs no models at all.

### Pre-flight checklist

- [ ] Both servers respond to `/health`
- [ ] Ran the full flow once, including `--skip-audit --baseline-only` and
      `--holdout 3`
- [ ] Saved a recorded run: `python least_privilege_demo.py | tee lp_output.txt`
- [ ] Checked the audit table for any `✗ MISMATCH` (a bad trace judged clean is
      the failure that matters)
- [ ] Decided how you'll explain the vendor domain (see step 5)

---

## Run of show

### Step 1: Why this matters

**Say:** "Every control we've seen so far tries to catch an agent doing
something wrong. The simplest control is making sure it can't. So how do we find
out what it actually needs?"

Show the current grants: every tool, unrestricted.

### Step 2: Audit the logs

```bash
python least_privilege_demo.py
```

The audit table classifies each trace with two judge checks: goal alignment and
injected instructions. **Say:** "Before we learn from this log, we need to know
which runs we'd be learning from."

### Step 3: Show what happens without the audit

```bash
python least_privilege_demo.py --skip-audit --baseline-only
```

**Say:** "Now pretend we skipped that step and learned from everything."

Point at the result: the file-read prefixes now include sensitive directories,
the allowed email domains include the attacker's domain, and `run_shell` stays
allowed. A policy learned from a compromised log **entrenches the compromise**.
This is the strongest moment in the demo, so don't rush it.

### Step 4: The proposal

Return to the normal run. Walk through:

- The usage mined from clean traces only.
- Whether the model's proposal passed verification, or whether it fell back to
  the baseline (and why).
- The proposed policy table: `delete_ticket`, `run_shell` and `list_users`
  removed, `read_file` restricted to `/var/docs/`, `send_email` restricted to
  the observed domains.

### Step 5: The human decision

**Say:** "The log can only tell us what was normal, not what was right."

The script flags any email domain seen only once. In the sample data that's the
external vendor. Whether to allow it is a business decision. Say which way you'd
go and why.

### Step 6: Replay

Read the replay table:

| Column                | Meaning                                         |
| --------------------- | ----------------------------------------------- |
| Legit actions blocked | Legitimate actions the policy would have broken |
| Malicious blocked     | Malicious steps the policy would have stopped   |
| Canaries denied       | Probe calls the policy refuses                  |

**Say:** "The current grants block nothing. The proposed policy stops most of
the malicious actions without breaking any legitimate ones."

Then be honest about two things, both visible on screen:

1. **"Legit blocked: 0" is partly by construction.** The policy was derived from
   the same traces it is replayed against.
2. **One malicious action still gets through.** The list under the table shows
   it. Permissions can't catch it, which is why the other demos exist.

### Step 7: Break it on purpose

```bash
python least_privilege_demo.py --holdout 3
```

This withholds the last three clean traces from learning and replays them as
unseen legitimate use. The column "held-out legit blocked" shows what a tight
policy breaks. **Say:** "This is the cost of least privilege: it breaks
legitimate things nobody had done yet. You trade that against what you gain."

### Step 8: Review

Open `least_privilege_report.md` and `proposed_policy.json`. Both say
`approved: false`. Nothing is deployed automatically.

---

## What to expect

These are the results the demo is designed around. The judge and proposer are
probabilistic and quantized, so check your own run.

| Question                                       | Where to look                                                                             |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Are all four bad traces excluded by the audit? | Audit table. A bad trace marked clean is called out with `‼️`                             |
| Does the proposal pass verification?           | Step 4-5 output. A model that generalizes `/var/docs/` to `/` is rejected by the canaries |
| Do the removed tools match the unused ones?    | Proposed policy table                                                                     |
| Is the vendor domain flagged for confirmation? | "Needs a human decision"                                                                  |
| Does `b04-internal-blast` still get through?   | "Malicious actions the chosen policy still allows"                                        |
| What does `--holdout` break?                   | Held-out column                                                                           |

---

## Reading the numbers honestly

- **Tiny, hand-built log.** Fourteen traces prove nothing about accuracy. A real
  log is larger, noisier and has more edge cases.
- **Circular replay.** Without `--holdout`, the legitimate-actions column
  measures the policy against its own training data.
- **The audit is the weak link.** If the judge marks a bad trace clean, that
  behavior is learned. The script reports every mismatch against our labels, but
  in real use you won't have labels.
- **Canaries are a probe, not a proof.** A policy that denies nine canaries can
  still be too broad somewhere else.
- **Logs show what was normal, not what was right.** A habit of emailing a risky
  domain will be learned as normal.
- **Rare-but-legitimate behavior gets broken.** That's the price of tightness.
  Measure it on held-out data.
- **Same model family.** The auditor and proposer are both Granite, which may
  correlate their blind spots.
- **Quantized models.** Both run as 4-bit GGUFs.

---

## Closing points

1. Constrain first: removing a tool or narrowing a path beats any detection
   layer.
2. Learn permissions from audited traces only, or you whitelist the attack.
3. Let the model propose and let deterministic checks decide, with a safe
   fallback.
4. Log-derived policies need a human, for the exceptions the log can't explain.
5. Permissions don't cover everything. Keep the gates, the audits and the
   approvals.

---

## Flags

| Flag                           | What it does                                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------------------------ |
| `--traces PATH`                | Use your own JSONL traces (same format as the trace-audit demo, plus an optional `expect` field) |
| `--skip-audit`                 | Treat every trace as clean, to show why the filter matters                                       |
| `--baseline-only`              | Skip the model proposal (judge server only)                                                      |
| `--holdout N`                  | Withhold the last N clean traces from learning and replay them as unseen use                     |
| `--out PATH` / `--report PATH` | Output files (defaults `proposed_policy.json`, `least_privilege_report.md`)                      |
| `--agent-url`, `--judge-url`   | Point at servers on other ports or hosts                                                         |

### Using your own traces

One JSON object per line:

```json
{
  "id": "run-0412",
  "goal": "What's the status of ticket SEC-101?",
  "steps": [
    {
      "tool": "get_ticket",
      "arguments": { "ticket_id": "SEC-101" },
      "result": "..."
    }
  ],
  "final": "SEC-101 is in progress.",
  "expect": { "clean": true, "bad_steps": [] }
}
```

`expect` is optional and only used for the scorecard and replay. Without it,
every trace is assumed clean in the replay. Redact sensitive data first, and use
more than a handful of runs.

---

## Troubleshooting

| Symptom                                                   | Fix                                                                                                                            |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `llama-server not reachable for the judge/proposer`       | Start the server and check `/health`.                                                                                          |
| `llama-server` fails to load a model                      | `brew upgrade llama.cpp`; Granite 4.1 needs a recent build.                                                                    |
| Every audit verdict is `None` and every trace is excluded | The `<score>` tags are being stripped. Restart the judge with `--special`.                                                     |
| The proposal always fails verification                    | Read the reasons printed. The model may be wrapping the JSON oddly or generalizing too far. The baseline is the safe fallback. |
| A clean trace is excluded                                 | The judge was too strict. That trace's behavior won't be allowed, which you'll see as breakage in the replay.                  |
| A bad trace is marked clean                               | The dangerous case. Look at the mismatch line, and consider tightening the audit criteria.                                     |
| Run is too slow live                                      | Use `--baseline-only`, or present the recording.                                                                               |
| A stray `__pycache__` folder appears next to the script   | Harmless. Delete it if you like.                                                                                               |
| Out of memory                                             | Lower `-c 8192` to `-c 4096`, or close other apps.                                                                             |

---

## Plan B

If anything fails live, narrate the recording:

```bash
cat lp_output.txt
```

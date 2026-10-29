# Learn Least Privilege from Audited Traces

## Overview

The cheapest way to stop an agent doing something is to not let it. Remove the
tool. Narrow the path. Restrict the recipient. No detector has to be right,
because the call cannot happen.

The difficulty is knowing what to remove. Most agents start with whatever was
convenient on day one: every tool, unrestricted. The honest source of truth for
what an agent **needs** is what it has actually done, and that is in the logs.

So we mine the logs. And that is where it goes wrong.

---

## The catch

**If the logs contain hijacked or misbehaving runs, learning permissions from
them whitelists the bad behavior.**

A poisoned ticket once led the agent to email secrets to an attacker's domain.
If that run is in the log, a policy built from "everything the agent has ever
done" now allows that domain, the secrets file and the shell. The compromise has
become the norm.

So a judge audits each trace first, and the policy learns only from the ones
that survive.

---

## What we build

```text
 14 logged traces --> AUDIT (judge) --> clean traces only
                       goal aligned?          |
                       injected text?         v
                                       MINE usage (deterministic)
                                       tools, file paths, email domains
                                              |
                          +-------------------+------------------+
                          v                                      v
                   BASELINE (rules)                    PROPOSE (Granite 8B)
                   smallest policy that                may generalize a little
                   covers observed use                 (path -> directory, address -> domain)
                          |                                      |
                          |                              VERIFY (deterministic)
                          |                              - valid JSON, known tools
                          |                              - covers every clean action
                          |                              - denies every canary the baseline denies
                          v                                      v
                       fallback  <--------- fails ------ passes -> used
                          |
                   REPLAY on all traces using OUR labels --> report --> human review
```

As in the approval-triage chapter: **the model proposes, deterministic checks
decide.**

---

## What a policy is

A tool listed in the policy is allowed. Everything else is denied.

| Tool         | Restriction available                                                                                                               |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| `read_file`  | `path_prefixes`: directories the agent may read. Paths are normalized first, so `/var/docs/../../etc/passwd` does not sneak through |
| `send_email` | `recipient_domains`: domains the agent may email                                                                                    |
| Others       | Allowed or removed                                                                                                                  |

The **current grants** are everything, unrestricted: `get_ticket`,
`create_ticket`, `search_docs`, `read_file`, `send_email`, `delete_ticket`,
`run_shell` and `list_users`.

## Canaries

Canaries are probe calls that must never be allowed: reading `/etc/passwd`, a
secrets file and a credentials file (plus a `../` trick), emailing an outside
domain, running a shell command, deleting a ticket, listing users. They measure
how broad a policy is **without needing labelled traces**, and they catch an
over-generalized proposal.

---

## The trace log

| Group          | Traces                                                                                                                                                                                                                                                 |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Clean (10)** | Ticket lookups, doc searches and reads under `/var/docs/`, emails to `@company.example`, ticket creation, and one legitimate email to an external vendor (`partner.example.invalid`)                                                                   |
| **Bad (4)**    | `b01-exfil` (poisoned ticket, secrets read, email to an outside address), `b02-recon` (reads of `/etc/passwd` and a credentials path), `b03-shell` (poisoned ticket, shell command), `b04-internal-blast` (an unrequested email to the all-staff list) |

The last bad trace is deliberate. It uses an **allowed domain**, so no
permission policy of this kind can stop it. It shows where least privilege ends
and other layers must take over.

Everything is mocked. The traces are hand-written, no tools run, and the secrets
are fake.

---

## The build plan

| Lesson | You add                                      | Needs           | Checkpoint                                  |
| ------ | -------------------------------------------- | --------------- | ------------------------------------------- |
| 1      | `allowed()`, canaries, a hand-written policy | No model        | `solution/step_01_policy.py`                |
| 2      | The trace log, mining, baseline and replay   | No model        | `solution/step_02_learn_from_everything.py` |
| 3      | The judge audit                              | Judge           | `solution/step_03_audit.py`                 |
| 4      | The model proposal and its verification      | Judge and agent | `solution/step_04_propose.py`               |
| 5      | Hold-out, human review and outputs           | Judge and agent | `solution/step_05_review.py`                |

## Next

Start with the policy itself:
[01-policies-and-canaries.md](./01-policies-and-canaries.md).

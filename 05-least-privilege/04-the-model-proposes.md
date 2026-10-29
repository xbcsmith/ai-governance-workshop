# Lesson 4: The Model Proposes

## Overview

The baseline is the smallest policy that covers the observed usage. A model can
propose something with sensible generalization: a directory instead of each
file, a domain instead of each address. We let it, and we verify what it says.
Start the agent server on port 8080 as well.

### What you will learn

- How to ask a model for a policy as structured JSON
- What deterministic checks make a proposal safe to use
- Why the baseline is the fallback

---

## Update the imports

Add `re`, and bring in the agent server constants:

```python
import re
```

```python
from llama_server import AGENT_TOKENIZER_ID, AGENT_URL, JUDGE_TOKENIZER_ID, JUDGE_URL, LlamaServer
```

---

## Ask for JSON

The prompt gives the model the observed usage from the **clean** traces only,
and the list of tools. It asks for the smallest policy that still covers the
usage, and allows two generalizations: a path to its directory, and an address
to its domain. Models often wrap JSON in prose or code fences, so we extract the
object defensively.

````python
def extract_json(text):
    text = re.sub(r"```(?:json)?", "", text)
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b <= a:
        return None
    try:
        return json.loads(text[a:b + 1])
    except json.JSONDecodeError:
        return None


def propose_with_model(proposer, stats):
    prompt = (
        "You are helping apply least privilege to an AI helpdesk agent. Below is usage observed in CLEAN, "
        "legitimate runs, and the tools the agent can currently use.\n\n"
        f"OBSERVED USAGE: {json.dumps(stats)}\n"
        f"CURRENT TOOLS (all unrestricted): {', '.join(ALL_TOOLS)}\n\n"
        "Propose the SMALLEST policy that still covers the observed usage. Omit tools that were not used. "
        "For read_file give path_prefixes (directories, ending in /). For send_email give recipient_domains. "
        "You may generalize specific paths to their directory and specific addresses to their domain, but no "
        "further. Give a one-sentence reason per tool. Output ONLY JSON in this shape:\n"
        '{"tools": {"get_ticket": {"reason": "..."}, "read_file": {"path_prefixes": ["/x/"], "reason": "..."}, '
        '"send_email": {"recipient_domains": ["example.com"], "reason": "..."}}}')
    raw = proposer.complete(proposer.render([{"role": "user", "content": prompt}]), 900, temperature=0.2)
    return extract_json(raw)
````

---

## Verify, do not trust

The proposal is parsed into a policy and checked. It is used only if it passes:

1. **It is valid:** the right shape, only known tools
2. **It covers every clean action:** nothing legitimate we have already seen
   would break
3. **It does not allow a canary that the baseline denies:** this catches
   over-generalization. A model that turns `/var/docs/` into `/` is rejected,
   because `/etc/passwd` is a canary

```python
def verify_proposal(obj, clean_traces, baseline):
    """Return (policy, reasons, errors). policy is None if the proposal fails verification."""
    errors = []
    if not obj or not isinstance(obj.get("tools"), dict):
        return None, {}, ["not valid JSON in the expected shape"]
    policy, reasons = {}, {}
    for tool, rule in obj["tools"].items():
        if tool not in ALL_TOOLS:
            errors.append(f"unknown tool '{tool}'")
            continue
        rule = rule if isinstance(rule, dict) else {}
        clean = {}
        if isinstance(rule.get("path_prefixes"), list):
            clean["path_prefixes"] = [str(p) for p in rule["path_prefixes"]]
        if isinstance(rule.get("recipient_domains"), list):
            clean["recipient_domains"] = [str(d) for d in rule["recipient_domains"]]
        policy[tool] = clean
        reasons[tool] = str(rule.get("reason", ""))[:200]
    if errors:
        return None, reasons, errors
    # 1. It must not break anything legitimate we already saw.
    blocked = sum(not allowed(policy, s["tool"], s["arguments"]) for tr in clean_traces for s in tr["steps"])
    if blocked:
        errors.append(f"would block {blocked} legitimate action(s) from the clean traces")
    # 2. It must not allow a canary that the baseline denies.
    base_denied = [not allowed(baseline, t, a) for t, a in CANARIES]
    prop_denied = [not allowed(policy, t, a) for t, a in CANARIES]
    leaks = [CANARIES[i][0] for i, (b, p) in enumerate(zip(base_denied, prop_denied)) if b and not p]
    if leaks:
        errors.append(f"allows canary calls the baseline denies ({', '.join(sorted(set(leaks)))})")
    return (None if errors else policy), reasons, errors
```

If it fails, the baseline is used and the reasons are printed. A model that is
wrong costs you nothing but the baseline.

---

## The entry point

The new flag `--baseline-only` skips the model, so you can still run with just
the judge:

```python
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-audit", action="store_true", help="treat every trace as clean (shows why the filter matters)")
    ap.add_argument("--baseline-only", action="store_true", help="skip the model proposal (judge server only)")
    ap.add_argument("--agent-url", default=AGENT_URL, help="proposer (Granite 4.1 8B) server")
    ap.add_argument("--judge-url", default=JUDGE_URL, help="judge (Granite Guardian) server")
    args = ap.parse_args()

    judge = None if args.skip_audit else LlamaServer(args.judge_url, JUDGE_TOKENIZER_ID)
    proposer = None if args.baseline_only else LlamaServer(args.agent_url, AGENT_TOKENIZER_ID)
    for name, srv in [("judge", judge), ("proposer", proposer)]:
        if srv is not None and not srv.healthy():
            sys.exit(f"llama-server not reachable for the {name}.")

    clean_traces = audit(judge, TRACES, skip=args.skip_audit)
    stats = mine(clean_traces)
    baseline = baseline_policy(stats)
    print_usage(stats)

    chosen, source, reasons, proposal = baseline, "rule-based baseline", {}, None
    if proposer:
        print(f"\n{'=' * 78}\nMODEL PROPOSAL AND DETERMINISTIC VERIFICATION\n{'=' * 78}")
        obj = propose_with_model(proposer, stats)
        proposal, reasons, errors = verify_proposal(obj, clean_traces, baseline)
        if proposal is not None:
            chosen, source = proposal, "model proposal (verified)"
            print("The model's proposal passed verification and is used.")
        else:
            print("The model's proposal FAILED verification, so the baseline is used instead:")
            for e in errors:
                print(f"   - {e}")
    else:
        print("\n(--baseline-only: no model proposal)")

    rows = [("current grants", CURRENT_GRANTS), ("baseline", baseline)]
    if proposer:
        rows.append(("model proposal" if proposal is not None else "model proposal (rejected)", proposal))
    print_replay(rows, TRACES)
    print_still(still_allowed(chosen, TRACES))
    print_policy(chosen, stats, f"PROPOSED POLICY  ({source})", reasons)
```

---

## Run it

```bash
python 05-least-privilege/work/policy.py
```

Read the model section. One of two things happens:

- **"The model's proposal passed verification and is used."** Compare its policy
  with the baseline. Are they the same? Did it generalize anywhere?
- **"The model's proposal FAILED verification, so the baseline is used
  instead."** Read the reasons. The model may have wrapped the JSON oddly or
  generalized too far. That is the check doing its job, and it is a result worth
  showing honestly

Each reason in the policy table is the model's own, one sentence per tool. The
replay table now has a third row for the proposal.

## Check your understanding

1. Change a path prefix in the model's output to `/` by hand, before
   verification. Which check rejects it?
2. Why does the check compare against the baseline's canary results, rather than
   require that all canaries are denied?

Checkpoint: `solution/step_04_propose.py`.

## Next

Hand it to a person: [05-review-and-holdout.md](./05-review-and-holdout.md).

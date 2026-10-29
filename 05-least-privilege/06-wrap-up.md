# Lesson 6: Wrap Up

## What you built

A pipeline in about 440 lines that goes from raw agent logs to a reviewed
least-privilege proposal.

| Step     | What your script does                                                    |
| -------- | ------------------------------------------------------------------------ |
| Audit    | A judge excludes hijacked or off-goal traces                             |
| Mine     | Plain counts of tools, paths and domains from the clean ones             |
| Baseline | The smallest policy that covers that usage                               |
| Propose  | A model suggests a policy. Rules verify it, and the baseline is fallback |
| Replay   | The policy is scored with our labels, and with a hold-out set            |
| Review   | A person gets a proposal marked `approved: false`                        |

## What the full demo adds

The script in [demo/](./demo/README.md) has the same pipeline. It adds:

- `--traces PATH`, so you can run it on your own JSONL traces
- Timing for the run
- A presenter guide with a run of show, talking points, a pre-flight checklist
  and a plan B

### Using your own traces

The trace format is the same one the
[trace-audit chapter](../08-trace-audit/README.md) uses. One JSON object per
line:

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

## Reading the numbers honestly

- **Tiny, hand-built log.** Fourteen traces prove nothing about accuracy. A real
  log is larger, noisier and has more edge cases
- **Circular replay.** Without `--holdout`, the legitimate-actions column
  measures the policy against its own training data
- **The audit is the weak link.** If the judge marks a bad trace clean, that
  behavior is learned. The script reports every mismatch against our labels, but
  in real use you will not have labels
- **Canaries are a probe, not a proof.** A policy that denies nine canaries can
  still be too broad somewhere else
- **Logs show what was normal, not what was right.** A habit of emailing a risky
  domain will be learned as normal
- **Rare-but-legitimate behavior gets broken.** That is the price of tightness.
  Measure it on held-out data
- **Same model family.** The auditor and proposer are both Granite, which may
  correlate their blind spots
- **Quantized models.** Both run as 4-bit GGUFs

## Closing points

1. Constrain first: removing a tool or narrowing a path beats any detection
   layer
2. Learn permissions from audited traces only, or you whitelist the attack
3. Let the model propose and let deterministic checks decide, with a safe
   fallback
4. Log-derived policies need a human, for the exceptions the log cannot explain
5. Permissions do not cover everything. Keep the gates, the audits and the
   approvals

## Exercises

1. **Load your own traces.** Write `load_traces(path)` for the JSONL shape
   above, with a default `expect` of clean, and add a `--traces` flag
2. **Add a canary.** Think of a call that should never be allowed and is not in
   the list. Does the baseline deny it? Does the model proposal?
3. **Add a restriction.** Teach `allowed()` a limit for `create_ticket`, such as
   a maximum title length. Where does it belong, and what would mine and replay
   need?
4. **Strengthen the verifier.** Reject any proposal that allows a tool the clean
   traces never used. What does it cost?
5. **Poison the audit.** Write a bad trace the judge marks clean. What did you
   have to change, and what does the resulting policy allow?

## Next

Policy decides what an agent may do. The next chapter asks where the criteria
behind those checks come from:
[06-policy-compiler](../06-policy-compiler/README.md).

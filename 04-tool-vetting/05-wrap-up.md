# Lesson 5: Wrap Up

## What you built

A vetting pipeline in about 250 lines: a catalog, three judge checks, a
quarantine decision, a hash lock and a drift check. The judge reads each
definition, never anything the server could use to argue its case, and an
approved tool is only as good as the last time it was checked.

| Phase | What your script does                                                        |
| ----- | ---------------------------------------------------------------------------- |
| Vet   | `vet` runs three checks. Any flag quarantines the tool                       |
| Pin   | `digest` hashes each approved definition                                     |
| Drift | A changed hash sends the new definition back through `vet`                   |
| Agent | The agent only sees what passed, so a poisoned tool never reaches its prompt |

## What the full demo adds

The script in [demo/](./demo/README.md) has the same four phases. It adds:

- `--mcp-json PATH`, which vets a real MCP `tools/list` response, running the
  vet and pin phases only
- Timing for each verdict
- A presenter guide with a run of show, talking points, a pre-flight checklist
  and a plan B

## Vetting real tools

Save a real server's `tools/list` response as JSON and turn it into catalog
entries. The shape you need is:

```json
{
  "tools": [
    {
      "name": "get_weather",
      "description": "Get the current weather for a city.",
      "inputSchema": {
        "type": "object",
        "properties": { "city": { "type": "string" } }
      }
    }
  ]
}
```

Each tool becomes a catalog entry of the same shape as the ones you wrote:

```python
{"server": path, "expect": None,
 "tool": {"type": "function",
          "function": {"name": name, "description": description, "parameters": inputSchema}}}
```

With `expect` set to `None`, the scorecard is skipped. Treat the output as a
triage list for human review, not an approval.

## Limits, said out loud

- **The judge is an LLM too.** Obfuscated or encoded instructions, or wording
  aimed at the judge itself, may slip past it
- **Definitions only.** A tool with a clean description can still behave
  maliciously on the server
- **False positives.** Tools that legitimately tell users or agents to do things
  ("confirm with the user before deleting") may be flagged. Test the criteria
  against your own tools
- **Tiny sample.** Seven hand-built tools prove nothing about accuracy. The
  criteria are prompts and are sensitive to wording
- **Quantization.** Verdicts from 4-bit models may differ from full precision
- **Semantic changes only get caught by re-vetting.** The hash tells you
  something changed, not whether the change is harmful. The judge decides that

## Closing points

1. The tool description is part of the prompt, so it is part of the attack
   surface
2. Pin what you approve and re-vet on change
3. The judge catches **what a definition says**. It cannot see what the tool's
   server code actually does
4. This sits next to least-privilege permissions, sandboxing and provenance. It
   does not replace them

## Exercises

1. **Vet real tools.** Write `from_mcp_json(path)` using the shape above, add a
   `--mcp-json` flag, and run it on a `tools/list` response you have. Read every
   quarantine yourself
2. **Add a fourth check.** Write a criterion for tools that ask for the
   conversation history. Which `flag_on` does it need?
3. **Hide it from the judge.** Rewrite the `add_numbers` instruction so the
   judge says `no` on all three checks. What did you have to change, and would
   an agent still follow it?
4. **Probe false positives.** Add three honest tools that mention credentials,
   deletion or email in a harmless way. How many does the judge quarantine?
5. **Pin more than the definition.** What else would you want in the lockfile?
   The server name? A signature?

## Next

Vetting decides which tools exist. The next chapter decides what the agent may
do with them: [05-least-privilege](../05-least-privilege/).

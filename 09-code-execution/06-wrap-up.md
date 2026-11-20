# Lesson 6: Wrap Up

## What you built

A gate for agent-written code in about 600 lines, with an interpreter behind it,
scored on 40 labeled snippets.

| Layer        | What it does                                                                             | Who decides              |
| ------------ | ---------------------------------------------------------------------------------------- | ------------------------ |
| Allowlist    | Parses the code and refuses anything not on the list of imports, builtins and attributes | Rules (exact)            |
| Budget rules | Refuses the common shapes of code that never ends or eats memory                         | Rules (guesses)          |
| Judge        | Reads code the rules passed, and sends worrying code to a human                          | A model (a guess)        |
| Review       | A human approves or refuses the code that was held                                       | A human                  |
| Sandbox      | Limits what any code that does run can reach                                             | The platform (not built) |

## What the full demo adds

The script in [demo/](./demo/README.md) has the same layers. It adds:

- `--skip-judge`, so the rules run with no model server at all
- `--code PATH`, so you can ask the gate about a file of your own Python
- A written report, `code_gate_report.md`, with the scores and what was held for
  a human
- A presenter guide with a run of show, a pre-flight checklist and a plan B

## Closing points

1. A code interpreter turns every other risk into a code-execution risk. Give
   the agent narrow tools when they will do
2. Parse code, do not search it. An allowlist on the syntax tree beats a
   denylist of words
3. Allowed modules are attack surface. Allow the part you need
4. A judge reads code surprisingly well, and still makes a good second opinion
   rather than the gate. It may make a decision stricter, never looser
5. The gate decides what code is made of. A sandbox decides what it can reach.
   You need both

---

## Limits

- **Sample size.** Forty snippets say little about how the gate does on real
  code. Several attacks contain giveaway words. Treat the numbers as a
  demonstration
- **The allowlist is not a proof.** Sandboxes built on filtering Python have
  repeatedly been escaped. We caught the `json.codecs` kind of gadget, and there
  may be others in the modules we allowed
- **Rules for abuse are guesses.** The thresholds are arbitrary and a determined
  attacker stays just under them
- **The judge is a quantized 8B model.** A different build can answer
  differently
- **Nothing ran.** We never executed any snippet, so we measured the decision,
  not what the code would have done
- **One language, one interpreter.** Shell tools, SQL, notebooks, code the agent
  writes to disk for something else to run, and generated infrastructure
  templates are not covered
- **Nothing here covers packages.** An agent that installs a library is a supply
  chain problem, which chapter 04 touches for tools but not for packages

---

## Exercises

1. **Widen the gate, then check.** Allow `string` and `decimal`, and list the
   attributes you would permit. Run lesson 1's snippets. Did anything slip
   through?
2. **Write five evasions of your own** and add them to the corpus. Did the
   allowlist catch them? Did the judge?
3. **Break the allowlist.** Add `os` to `ALLOWED_MODULES` and rerun. Which
   snippets get through, and which still do not? Which rule saved you?
4. **Replace the interpreter.** Write a `read_doc(name)` tool that reads only
   from `/var/docs/` and rerun scenario 2 with `run_python` removed. What does
   the user get now?
5. **Tune the budget rules.** Lower `BIG` to `10 ** 6`. What legitimate snippet
   do you break? What do you gain?
6. **Combine with chapter 08.** Write a trace in which an agent runs an allowed
   snippet and then reports a result the interpreter never returned. Does the
   trace audit catch it?

## Next

Back to the [workshop outline](../README.md), or take another chapter: the audit
in [08-trace-audit](../08-trace-audit/README.md) is a good partner for this one.
The same pattern, exact rules first and a judge that can only make a decision
stricter, carries on in [10-agent-messaging](../10-agent-messaging/README.md)
and [11-cascading-failures](../11-cascading-failures/README.md).

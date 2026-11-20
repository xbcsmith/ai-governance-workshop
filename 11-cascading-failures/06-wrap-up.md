# Wrap-up

## What you built

A pipeline and six controls, and a way to count what each one buys:

- **A contract between stages.** One known action, one known service. It stops
  the wildcard and everything that looks like it, 15 of 15 on our orders, with
  no model.
- **Scope.** Production and critical services wait for a human.
- **A budget.** A run restarts only so many services on its own, which caps the
  cost of any mistake the other rules missed.
- **Provenance.** A ticket our own action caused is not acted on automatically.
- **A circuit breaker.** When a restart makes things worse, the line stops. It
  watches effects, so it catches failures nobody wrote a rule for.
- **A judge,** which checks that the order matches the ticket and can only add a
  hold.

## Takeaways

- **Every stage looks fine alone.** The failure is in the loop, so the controls
  go at the boundaries and around the loop.
- **Limit the blast radius first.** A budget and a breaker work when you did not
  predict the failure. A rule that names the failure only works when you did.
- **Break feedback two ways.** Provenance needs good monitoring. The breaker
  needs nothing. Using both means one failing does not reopen the loop.
- **Watch effects as well as requests.** The circuit breaker caught what no
  request-side rule described, and it missed the production wildcard that a
  request-side rule caught. Neither is enough alone.
- **Exact rules decide, the judge only holds.** Same rule as chapters 09 and 10.
- **Count the cost of each control.** Our rules held a legitimate critical
  restart and two harmless alerts. A control that stops legitimate work gets
  turned off.

## What this chapter does not cover

- **Cycles.** Our fleet is a graph with no loops, so every cascade settles. A
  real system with retries can loop until something runs out, and the six-round
  limit in `run_pipeline` is doing work that a real deployment would need a
  timeout and a rate limit to do.
- **A real signal for the breaker.** We count new alerts. A real breaker watches
  error rates, latency, queue depth or saturation, and half-opens to test
  whether things have recovered.
- **Real provenance.** We set `caused_by_pipeline` by hand. A real system has to
  link an alert to the change that preceded it, which is hard and sometimes
  wrong.
- **More than one agent in the chain.** Here one stage is an agent. When several
  are, each hop is a place for a wrong value to be believed, and chapter 10's
  signatures and sender-scoped authority apply to each hop.
- **Rollback.** We stop the damage. Undoing it is a separate problem.
- **A ticket that is simply false.** Nothing here checks that a ticket is true.

## Exercises

1. Add a ninth staging service that two others depend on, and rerun the table.
   Which start ticket gets worse, and which control stops it?
2. Make `stg-api` depend on `stg-web`, creating a cycle. Run the unguarded
   pipeline. What stops it? Which controls stop it sooner?
3. Change `BUDGET` to 1 and to 10. At what number does the budget stop mattering
   for the `stg-db` ticket?
4. Make the breaker trip on three alerts instead of two. Which start tickets
   change?
5. Remove `provenance_rule` from `GUARDED` and run scenario 2. What now stops
   the follow-up alerts, and what does it hold?
6. Write five more drift pairs the judge might miss: a ticket that names two
   services and a correction in the same sentence is a good start.

## Where this leaves the workshop

Every one of the ten OWASP risks now has at least one chapter, some directly and
some only in part. Each chapter built one layer, and none of them is enough
alone: exact checks first, a judge for what they cannot see, and a human for
what the judge is unsure of. The
[intro](../01-intro/00-intro.md#owasp-top-10-for-agentic-applications-2026) has
the full map, including what each chapter leaves out.

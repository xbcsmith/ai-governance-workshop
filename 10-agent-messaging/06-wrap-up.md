# Wrap-up

## What you built

A message bus with three layers, and a way to measure each one:

- **A signed envelope.** HMAC over the sender, recipient, id, time and body. It
  catches forged, altered, stale, replayed and misrouted messages, 11 of the 15
  bad ones in our set, with no model.
- **A policy of who may ask for what.** It catches the four more that are
  authentic and still not allowed, and it is a table a human can review.
- **Sender-scoped tools.** The agent acts with the authority of whoever wrote to
  it, so a message that talks it into a bigger action still fails.
- **A judge on the free text,** which turns a signed, in-scope, hijacked message
  into a hold for review.

## Takeaways

- **A signature says who, not whether to trust.** A compromised agent signs its
  poisoned messages with its own genuine key.
- **Check in the bus, not in the prompt.** The model cannot verify a signature,
  and a rule it is asked to follow is a rule it can be talked out of.
- **Authority travels with the sender.** An agent that holds powerful tools
  should never use them for a sender who could not use them directly.
- **Exact checks first, the judge second, and the judge only makes things
  stricter.** Same rule as chapter 09.
- **Tell the sender as little as possible.** A short refusal gives an attacker
  less to tune.

## What this chapter does not cover

- **Shared keys.** HMAC means the receiver holds the key that signs, so the
  receiver can forge a message from the sender. Real systems use asymmetric
  signatures (a private key per agent, public keys for everyone else), or mutual
  TLS between agents. We used HMAC because it needs only the standard library.
- **Where keys live.** The keys here are strings in the file. Real keys need a
  secrets manager, rotation, and a way to revoke an agent that was compromised.
- **Confidentiality.** We sign messages. We do not encrypt them. Anyone on the
  bus can read them. A shared channel like `post_note` makes that worse.
- **Delivery.** There is no queue, no ordering and no retry. A real bus can
  lose, delay or reorder messages, and the replay window and the `seen` list
  have to survive a restart.
- **The state of `seen`.** It grows forever in our code. A real receiver prunes
  ids older than the freshness window, which is why the window exists.
- **More than two agents.** We have two senders and one receiver. With chains of
  agents, a message passes through several hands, and each hop must re-sign and
  re-check. What happens when one hop goes wrong is the next chapter.

## Exercises

1. Add a third sender, `scheduler`, that may only call `post_note`. Add four
   test messages for it, with one that asks for something else, and score them.
2. Remove `ts` from the signed fields in `canonical`. Which tests start passing
   that should fail? Put it back.
3. Add a `"max_age"` per sender so that `orchestrator` messages must be fresher
   than `triage` ones. Where does it belong, in `verify` or in the policy?
4. Write five more quiet injections for the judge to miss, in the style of the
   quiet ones. How many get through?
5. Make the tool gate return the full reason to the agent, and rerun scenario 4.
   Does the agent change what it tries?
6. Give `post_note` a rule that refuses text containing the characters `KEY=`.
   Is that a policy rule or a judge job? What breaks it?

## Next

The agents are now talking safely. What happens when one of them is wrong
anyway, and the next one believes it:
[chapter 11, cascading failures](../11-cascading-failures/README.md).

# Workshop Session: Introduction

## Outline

### Why a judge

Agents read untrusted text and act on it. Human review of every step does not
scale. We introduce the idea of a second model that answers yes or no about a
piece of text, and we are honest about what that can and cannot do.

### The threat model

A small toy world with mock tools and fake secrets, and the four ways an agent
goes wrong in it: a hostile user, hostile data, a bad tool call, and a leaky
answer.

### The judge contract

How a judge model is asked a question, what its answer means, and the two rules
every script in this workshop follows: read the polarity of each criterion, and
fail closed.

## Key Learning Objectives

- Name the four checkpoints where a judge can guard an agent
- Explain the difference between a risk criterion and a requirement criterion
- Explain why an unparseable verdict is treated as a flag
- Describe what the rest of the workshop builds

## Files

| File                                       | Description                                  |
| ------------------------------------------ | -------------------------------------------- |
| [00-intro.md](./00-intro.md)               | Why a judge, and a map of the workshop       |
| [01-threat-model.md](./01-threat-model.md) | The toy world and four ways an agent fails   |
| [02-the-judge.md](./02-the-judge.md)       | The judge contract, polarity and fail closed |

There is nothing to build in this chapter. It is the vocabulary for the rest.

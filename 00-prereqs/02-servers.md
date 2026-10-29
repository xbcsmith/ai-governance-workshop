# Start the Servers

## Overview

The workshop uses two models, each in its own `llama-server`:

| Role  | Model                   | Port | Job                                     |
| ----- | ----------------------- | ---- | --------------------------------------- |
| Agent | Granite 4.1 8B          | 8080 | Reads requests and calls (mock) tools   |
| Judge | Granite Guardian 4.1 8B | 8081 | Answers yes or no about a piece of text |

We keep them separate on purpose. The judge is a different model from the agent,
so it does not share the agent's context or its mistakes.

---

## Start the agent

In terminal 1:

```bash
llama-server -hf unsloth/granite-4.1-8b-GGUF:UD-Q4_K_XL --port 8080 -c 8192 --special
```

## Start the judge

In terminal 2:

```bash
llama-server -hf ibm-granite/granite-guardian-4.1-8b-GGUF:Q4_K_M --port 8081 -c 8192 --special
```

The first run downloads the model. Wait until the terminal reports that the
server is listening.

### What the flags do

| Flag               | Why we use it                                                                                   |
| ------------------ | ----------------------------------------------------------------------------------------------- |
| `-hf <repo:quant>` | Download the model from Hugging Face and cache it                                               |
| `--port`           | Keeps the agent on 8080 and the judge on 8081                                                   |
| `-c 8192`          | Context window. Lower it to `4096` if you run out of memory                                     |
| `--special`        | Keep special tokens in the output. Without it the judge's `<score>` tag is stripped (see below) |

---

## Check that both are up

Terminal 3 is the one you will work from. Each command should return a 200
response.

```bash
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8081/health
```

To see which model each server loaded:

```bash
curl -s http://127.0.0.1:8080/v1/models | jq .
curl -s http://127.0.0.1:8081/v1/models | jq .
```

---

## The most common mistake

If you forget `--special`, the judge still answers, but the `<score>yes</score>`
tags are stripped from its output. Our code cannot parse the verdict and, by
design, treats an unparseable verdict as a flag. Every check then looks flagged.

If you see verdicts of `None` in later lessons, restart **both** servers with
`--special`.

---

## Next

Run the setup check in [03-check-setup.md](./03-check-setup.md).

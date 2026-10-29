# Shared Source

Helpers used by every chapter, so the walkthrough scripts can stay short and
focus on the idea being taught.

## Install requirements

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
export PYTHONPATH="$PWD/src"
```

Run these from the repository root.

## Files

| File               | Description                                                  |
| ------------------ | ------------------------------------------------------------ |
| `llama_server.py`  | A small client for a local `llama-server`                    |
| `check_setup.py`   | Confirms both servers are up and the judge returns a verdict |
| `requirements.txt` | Python packages the scripts need                             |

## llama_server.py

`LlamaServer(url, tokenizer_id)` wraps one running `llama-server`. It has three
methods:

- `healthy()` returns `True` when `/health` answers
- `render(messages, **template_kwargs)` applies the model's chat template and
  returns the prompt text. Extra keyword arguments reach the template, which is
  how tool definitions are passed to the agent
- `complete(prompt, max_new_tokens, temperature)` sends the prompt to
  `/completion` and returns the generated text

We render the prompt ourselves rather than use the chat endpoint. This applies
the Granite templates exactly as the model cards describe, and it keeps special
tags such as `<score>` and `<tool_call>` in the output. That is why both servers
must be started with `--special`.

The module also defines the default server URLs and tokenizer ids:

| Name                 | Value                                 |
| -------------------- | ------------------------------------- |
| `AGENT_URL`          | `http://127.0.0.1:8080`               |
| `JUDGE_URL`          | `http://127.0.0.1:8081`               |
| `AGENT_TOKENIZER_ID` | `ibm-granite/granite-4.1-8b`          |
| `JUDGE_TOKENIZER_ID` | `ibm-granite/granite-guardian-4.1-8b` |

## check_setup.py

Runs four checks and prints PASS or FAIL for each: the agent server is up, the
judge server is up, the agent can generate text, and the judge returns a
parseable `<score>` verdict.

```bash
python src/check_setup.py
```

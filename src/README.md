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

| File               | Description                                                     |
| ------------------ | --------------------------------------------------------------- |
| `llama_server.py`  | A small client for a local `llama-server`                       |
| `judge.py`         | The judge function from chapter 02, for reuse in later chapters |
| `check_setup.py`   | Confirms both servers are up and the judge returns a verdict    |
| `requirements.txt` | Python packages the scripts need                                |

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

## judge.py

The judge you built in chapter 02, packaged for reuse. From chapter 03 onward
the walkthroughs import it instead of retyping it:

- `judge_text(server, text, criterion, flag_on)` judges one piece of text and
  returns `(label, flagged)`
- `ask_judge(server, messages, criteria, schema, flag_on, think=False)` judges a
  whole conversation and returns `(label, flagged, reasoning)`

`flag_on` is the polarity rule from the introduction: `"yes"` for a risk
criterion, `"no"` for a requirement. An answer that cannot be parsed counts as a
flag. The parser also accepts a reply that is just a bare `yes` or `no`, which
the later demos tolerate. Anything else is unparseable.

## check_setup.py

Runs four checks and prints PASS or FAIL for each: the agent server is up, the
judge server is up, the agent can generate text, and the judge returns a
parseable `<score>` verdict.

```bash
python src/check_setup.py
```

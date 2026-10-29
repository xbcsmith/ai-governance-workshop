# Install the Tools

## Overview

We need three things: a way to serve models locally, a Python environment, and
the shared helper code in `src/`.

---

## Install llama.cpp

`llama-server` is the program that loads a model and answers HTTP requests.

```bash
brew install llama.cpp
```

Already installed? Upgrade it. Granite 4.1 needs a recent build.

```bash
brew upgrade llama.cpp
llama-server --version
```

On Linux, follow the
[llama.cpp install guide](https://github.com/ggml-org/llama.cpp) for your
platform.

---

## Create the Python environment

Run these from the repository root.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
```

The scripts need `transformers` and `jinja2`. They use the model's tokenizer to
render chat prompts. They do not run the models with Python.

Tell Python where the shared helpers live:

```bash
export PYTHONPATH="$PWD/src"
```

Every lesson assumes this variable is set. If a script cannot find
`llama_server`, this is the first thing to check. Set it again in any new
terminal.

---

## Memory

Two 4-bit 8B models need to fit in memory at the same time. The demos were
prepared on a machine with 24 GB. If you have less, start both servers with a
smaller context window (`-c 4096`) and close memory-heavy applications.

---

## Next

Start the servers in [02-servers.md](./02-servers.md).

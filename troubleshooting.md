# Troubleshooting

Fixes for the problems people hit most. Chapter-specific problems are listed in
that chapter's demo guide.

## Servers

| Symptom                                          | Fix                                                                                                                      |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| `llama-server not reachable for the agent/judge` | The server is not running or is still loading. Check `/health` and the server's terminal                                 |
| `llama-server` fails to load a model             | `brew upgrade llama.cpp`. Granite 4.1 needs a recent build                                                               |
| Guardian repo or quant tag not found             | Check the repository's file list on Hugging Face and adjust the `:Q4_K_M` tag                                            |
| Port already in use                              | Another process holds 8080 or 8081. Stop it, or start the server on another port and pass `--agent-url` or `--judge-url` |
| Out of memory                                    | Close other apps, or lower `-c 8192` to `-c 4096` on both servers                                                        |
| First run is very slow                           | The models and tokenizers are downloading. Wait for the server to print that it is listening                             |

## Judge verdicts

| Symptom                                        | Fix                                                                                             |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Verdicts show `None` and everything is flagged | The `<score>` tags are being stripped. Restart **both** servers with `--special`                |
| A verdict differs from the lesson              | Expected sometimes. The models are probabilistic and quantized. Say so, and show what you got   |
| The agent never makes a tool call              | Restart the agent server and rerun. Read the raw agent output before assuming the code is wrong |

## Python

| Symptom                             | Fix                                                                             |
| ----------------------------------- | ------------------------------------------------------------------------------- |
| `ModuleNotFoundError: llama_server` | Run `export PYTHONPATH="$PWD/src"` from the repository root                     |
| `ModuleNotFoundError: transformers` | Activate your virtual environment and run `pip install -r src/requirements.txt` |
| Tokenizer download fails            | Check your network access to Hugging Face, then rerun                           |

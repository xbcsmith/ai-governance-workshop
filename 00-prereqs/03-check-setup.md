# Check the Setup

## Overview

`src/check_setup.py` runs four checks so you find problems now, not in the
middle of a lesson.

## Run it

From the repository root, in terminal 3:

```bash
source .venv/bin/activate
export PYTHONPATH="$PWD/src"
python src/check_setup.py
```

The first run downloads the two tokenizers from Hugging Face, so it may pause
for a moment.

## What you should see

```text
Loading tokenizers (the first run downloads them from Hugging Face)...
[PASS] agent server answers at http://127.0.0.1:8080
[PASS] judge server answers at http://127.0.0.1:8081
[PASS] agent generated text: 'ready'
[PASS] judge returned a verdict: 'no'

All checks passed.
```

The exact text the agent generates may differ.

## If a check fails

| Failing check                 | Likely cause and fix                                                                         |
| ----------------------------- | -------------------------------------------------------------------------------------------- |
| Agent or judge server answers | The server is not running or still loading. Check its terminal, then `/health`               |
| Agent generated text          | Restart the agent server and rerun                                                           |
| Judge returned a verdict      | The judge was started without `--special`. Restart it with `--special`                       |
| `ModuleNotFoundError`         | Activate the virtual environment and set `PYTHONPATH` (see [01-install.md](./01-install.md)) |

More fixes are in [troubleshooting.md](../troubleshooting.md).

## Next

Move on to [01-intro](../01-intro/README.md).

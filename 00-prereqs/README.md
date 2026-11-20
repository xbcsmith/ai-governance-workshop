# Workshop Session: Prerequisites

**OWASP Agentic Top 10 (2026):** ASI04

## Outline

### Install the tools

Install `llama.cpp` and create a Python environment with the two packages the
scripts need. This takes a few minutes, plus model download time on the first
run.

### Start the two model servers

Run one `llama-server` for the agent (Granite 4.1 8B) and one for the judge
(Granite Guardian 4.1 8B), each in its own terminal. Both need the `--special`
flag.

### Check the setup

Run `src/check_setup.py`. It confirms that both servers answer and that the
judge returns a verdict we can parse.

## Key Learning Objectives

- Know which two models the workshop uses and why there are two servers
- Start, stop and health-check a local `llama-server`
- Recognize the symptom of a missing `--special` flag

## OWASP Agentic Top 10 mapping

Tags for this chapter, from the
[OWASP Top 10 for Agentic Applications 2026](../01-intro/00-intro.md#owasp-top-10-for-agentic-applications-2026).
Rows are listed in order of how central the risk is to the chapter.

| ID    | Risk                                 | How this chapter relates                                                                                                                                                                                                      |
| ----- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ASI04 | Agentic Supply Chain Vulnerabilities | Adjacent. The first run downloads model weights and tokenizers from the internet. Download them from the sources in the install lesson, and treat anything you fetch as untrusted input, which is the habit chapter 04 builds |

## Files

| File                                     | Description                                  |
| ---------------------------------------- | -------------------------------------------- |
| [01-install.md](./01-install.md)         | Install llama.cpp and the Python environment |
| [02-servers.md](./02-servers.md)         | Start and check the agent and judge servers  |
| [03-check-setup.md](./03-check-setup.md) | Run the setup check                          |

Do this before the session. The first run downloads several gigabytes of model
files.

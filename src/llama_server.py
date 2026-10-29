"""Minimal client for a local llama-server (llama.cpp), shared by every chapter.

It does three things:
  healthy()   is the server up?
  render()    turn chat messages into the model's prompt text (the tokenizer's chat template)
  complete()  send a prompt to llama-server and return the generated text

We render the prompt ourselves and call /completion so the Granite chat template
(tools, Guardian scoring blocks) is applied exactly as the model cards describe.
"""

import json
import urllib.error
import urllib.request

AGENT_URL = "http://127.0.0.1:8080"
JUDGE_URL = "http://127.0.0.1:8081"

AGENT_TOKENIZER_ID = "ibm-granite/granite-4.1-8b"
JUDGE_TOKENIZER_ID = "ibm-granite/granite-guardian-4.1-8b"


class LlamaServer:
    def __init__(self, url: str, tokenizer_id: str):
        try:
            from transformers import AutoTokenizer
        except ImportError as error:
            raise SystemExit("Install the requirements with: pip install -r src/requirements.txt") from error

        self.url = url.rstrip("/")
        self.tok = AutoTokenizer.from_pretrained(tokenizer_id)

    def healthy(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.url}/health", timeout=5) as response:
                return response.status == 200
        except (urllib.error.URLError, OSError):
            return False

    def render(self, messages, **template_kwargs) -> str:
        return self.tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, **template_kwargs
        )

    def complete(self, prompt: str, max_new_tokens: int = 300, temperature: float = 0.0) -> str:
        body = json.dumps({
            "prompt": prompt,
            "n_predict": max_new_tokens,
            "temperature": temperature,
            "special": True,  # keep <score>, <think> and <tool_call> tags in the output
            "cache_prompt": True,
        }).encode()
        request = urllib.request.Request(
            f"{self.url}/completion",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=600) as response:
            result = json.loads(response.read())
        return result["content"].replace("<|end_of_text|>", "").strip()

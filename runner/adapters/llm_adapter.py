import os
import time
import requests
from abc import ABC, abstractmethod


from pathlib import Path


class LLMAdapter(ABC):
    """Abstract LLM Adapter interface for non-code text generation."""

    _first_phrase_cache: str = None

    @classmethod
    def get_first_phrase(cls) -> str:
        if cls._first_phrase_cache is None:
            try:
                from runner.utils.template_manager import TemplateManager
                cls._first_phrase_cache = TemplateManager.render("common/first_phrase.tpl").strip()
            except Exception as e:
                raise RuntimeError(
                    f"❌ [LLMAdapter Error] Failed to load or render prompt prefix template 'common/first_phrase.tpl': {e}"
                ) from e
        return cls._first_phrase_cache

    def apply_prefix(self, prompt: str) -> str:
        prefix = self.get_first_phrase()
        if not prefix or prefix in prompt:
            return prompt

        # If prompt starts with [INST], insert prefix right after [INST] for tokenizer alignment
        if prompt.startswith("[INST]\n"):
            return f"[INST]\n{prefix}\n\n{prompt[7:]}"
        elif prompt.startswith("[INST]"):
            return f"[INST]\n{prefix}\n\n{prompt[6:].lstrip()}"
        return f"{prefix}\n\n{prompt}"

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        pass


class LocalLLMAdapter(LLMAdapter):
    """Adapter for Local LLM Server (Ollama / Llama-cpp OpenAI-compatible Chat Completion Endpoint)."""

    def __init__(self, endpoint_url: str = "http://127.0.0.1:11435/v1/chat/completions", model_name: str = "devstral"):
        endpoint_url = endpoint_url.strip().rstrip("/")
        if endpoint_url.endswith("/completion"):
            endpoint_url = endpoint_url[:-len("/completion")]
        if not endpoint_url.endswith("/v1/chat/completions"):
            if endpoint_url.endswith("/v1"):
                endpoint_url = f"{endpoint_url}/chat/completions"
            else:
                endpoint_url = f"{endpoint_url}/v1/chat/completions"
        self.endpoint_url = endpoint_url
        self.model_name = model_name

    def generate_text(self, prompt: str, system_instruction: str = "") -> str:
        prompt = self.apply_prefix(prompt)
        headers = {"Content-Type": "application/json"}
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        max_tok = int(os.getenv("LLAMA_MAX_TOKENS", os.getenv("MAX_TOKENS", "8192")))
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": max_tok,
            "cache_prompt": True
        }

        print(f"🔍 [LLM:Local] Requesting chat completion from Local LLM ({self.endpoint_url}). Messages: {len(messages)}, Prompt length: {len(prompt)} chars...", flush=True)

        import urllib.request
        import urllib.parse
        import json

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.endpoint_url, data=data, headers=headers)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        max_attempts = 3
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                with opener.open(req, timeout=180) as response:
                    res_body = response.read().decode("utf-8")
                    res_json = json.loads(res_body)
                    choices = res_json.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "").strip()
                    else:
                        content = res_json.get("content", "").strip()
                    if content:
                        print(f"✅ [LLM:Local] Successfully received {len(content)} chars from local LLM!", flush=True)
                        return content
                    else:
                        last_error = "Received empty response (0 chars)"
                        print(f"⚠️ [LLM:Local Retry {attempt}/{max_attempts}] {last_error}. Retrying in 3s...", flush=True)
                        time.sleep(3)
            except Exception as e:
                last_error = str(e)
                print(f"⚠️ [LLM:Local Retry {attempt}/{max_attempts}] Error: {e}. Retrying in 3s...", flush=True)
                time.sleep(3)

        raise RuntimeError(f"❌ [Local LLM Failure] Max attempts ({max_attempts}) reached for {self.endpoint_url}. Last error: {last_error}")


class GeminiLLMAdapter(LLMAdapter):
    """Adapter for Google Gemini via agy CLI."""

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = os.getenv("EVALUATOR_MODEL", model_name)

    def generate_text(self, prompt: str, system_instruction: str = "") -> str:
        prompt = self.apply_prefix(prompt)
        full_prompt = f"[SYSTEM INSTRUCTION]\n{system_instruction}\n\n[USER REQUEST]\n{prompt}" if system_instruction else prompt
        print(f"🔍 [LLM:Gemini] Requesting completion via agy CLI. Prompt length: {len(full_prompt)} chars...", flush=True)

        import shutil
        import subprocess
        import time

        cli_name = shutil.which("agy") or shutil.which("agy-ide")
        if not cli_name:
            raise RuntimeError("❌ [Gemini Adapter Error] 'agy' or 'agy-ide' CLI command not found in PATH.")

        max_attempts = 3
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                cmd = [cli_name, "--dangerously-skip-permissions", "--print", full_prompt]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if res.returncode == 0 and res.stdout.strip():
                    result_text = res.stdout.strip()
                    print(f"✅ [LLM:Gemini] Successfully received {len(result_text)} chars from agy CLI!", flush=True)
                    return result_text
                else:
                    err_msg = f"ReturnCode {res.returncode}, Stderr: {res.stderr.strip()}"
                    print(f"  ⚠️ [LLM:Gemini] agy CLI attempt #{attempt} failed: {err_msg}", flush=True)
                    last_error = err_msg
            except Exception as e:
                print(f"  ⚠️ [LLM:Gemini] agy CLI attempt #{attempt} raised exception: {e}", flush=True)
                last_error = str(e)

            if attempt < max_attempts:
                sleep_secs = 2 ** attempt
                print(f"  ⏳ [LLM:Gemini] Retrying in {sleep_secs}s...", flush=True)
                time.sleep(sleep_secs)

        raise RuntimeError(f"❌ [AGY CLI Error] Failed after {max_attempts} attempts. Last error: {last_error}")


class LLMAdapterFactory:
    """Factory to get the appropriate LLM Adapter."""

    @staticmethod
    def get_adapter(provider: str = "local") -> LLMAdapter:
        if provider.lower() == "gemini":
            return GeminiLLMAdapter()
        elif provider.lower() in ["local", "ollama"]:
            return LocalLLMAdapter()
        else:
            return LocalLLMAdapter()

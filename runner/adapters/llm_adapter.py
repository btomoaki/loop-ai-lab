import time
import requests
from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    """Abstract LLM Adapter interface for non-code text generation."""

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        pass


class LocalLLMAdapter(LLMAdapter):
    """Adapter for Local LLM Server (Ollama / Llama-cpp HTTP Completion Endpoint)."""

    def __init__(self, endpoint_url: str = "http://127.0.0.1:11435/completion"):
        self.endpoint_url = endpoint_url

    def generate_text(self, prompt: str) -> str:
        headers = {"Content-Type": "application/json"}
        payload = {
            "prompt": prompt,
            "temperature": 0.2,
            "n_predict": 4096,
            "stop": ["</s>", "USER:", "SYSTEM:"]
        }

        print(f"🔍 [LLM:Local] Requesting completion from Local LLM ({self.endpoint_url}). Prompt length: {len(prompt)} chars...", flush=True)

        session = requests.Session()
        session.trust_env = False

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                resp = session.post(self.endpoint_url, headers=headers, json=payload, timeout=120)
                if resp.status_code == 200:
                    res_json = resp.json()
                    content = res_json.get("content", "").strip()
                    if content:
                        print(f"✅ [LLM:Local] Successfully received {len(content)} chars from local LLM!", flush=True)
                        return content
                    else:
                        print(f"⚠️ [LLM:Local Retry {attempt}/{max_attempts}] Received empty response (0 chars). Retrying in 2s...", flush=True)
                        time.sleep(2)
                else:
                    print(f"⚠️ [LLM:Local Retry {attempt}/{max_attempts}] HTTP Status {resp.status_code}. Retrying in 2s...", flush=True)
                    time.sleep(2)
            except Exception as e:
                print(f"⚠️ [LLM:Local Retry {attempt}/{max_attempts}] Error: {e}. Retrying in 2s...", flush=True)
                time.sleep(2)

        print("❌ [LLM:Local Failure] Max attempts reached for local LLM request.", flush=True)
        return ""


class GeminiLLMAdapter(LLMAdapter):
    """Adapter for Google Gemini API."""

    def __init__(self, model_name: str = "gemini-1.5-pro"):
        self.model_name = model_name

    def generate_text(self, prompt: str) -> str:
        print(f"🔍 [LLM:Gemini] Requesting completion with {self.model_name}. Prompt length: {len(prompt)} chars...", flush=True)
        return f"Gemini mock response for prompt length {len(prompt)}"


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

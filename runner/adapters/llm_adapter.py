import os
import requests
import json
from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        pass


class GeminiAdapter(LLMAdapter):
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name

    def generate_text(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("❌ [LLM:Gemini Escalation] GEMINI_API_KEY is missing! Cannot proceed with Gemini provider. Halting for user intervention.")

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json", "Connection": "close"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            raise RuntimeError(f"❌ [LLM:Gemini Escalation] Gemini API call failed: {e}. Halting for user intervention.")


class LlamaCppAdapter(LLMAdapter):
    def __init__(self, endpoint_url: str = None):
        self.endpoint_url = endpoint_url or os.environ.get("LOCAL_LLM_URL", "http://127.0.0.1:11435/completion")

    def generate_text(self, prompt: str) -> str:
        try:
            print(f"🔍 [LLM:Local] Requesting completion from Local LLM ({self.endpoint_url}). Prompt length: {len(prompt)} chars...")
            
            headers = {
                "Content-Type": "application/json",
                "Connection": "close"
            }
            payload = {
                "prompt": prompt,
                "temperature": 0.2,
                "n_predict": 1024,
                "stop": ["</s>", "[END_OF_TEXT]"]
            }

            session = requests.Session()
            session.keep_alive = False

            resp = session.post(self.endpoint_url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("content", "")
            print(f"✅ [LLM:Local] Successfully received {len(content)} chars from local LLM!")
            return content
        except Exception as e:
            raise RuntimeError(f"❌ [LLM:Local Escalation] Local LLM call failed on endpoint {self.endpoint_url}: {e}. Halting for user intervention.")


class LLMAdapterFactory:
    @staticmethod
    def get_adapter(provider: str = "gemini") -> LLMAdapter:
        provider_lower = (provider or "gemini").lower()
        if provider_lower == "gemini":
            return GeminiAdapter()
        elif provider_lower in ["local", "llama", "llamacpp"]:
            return LlamaCppAdapter()
        else:
            return LlamaCppAdapter()

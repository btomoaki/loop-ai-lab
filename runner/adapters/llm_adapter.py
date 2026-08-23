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
            print("⚠️ [LLM:Gemini Warning] GEMINI_API_KEY が未設定です。ローカルLLMにフォールバックします。")
            fallback = LlamaCppAdapter()
            return fallback.generate_text(prompt)

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"⚠️ [LLM:Gemini Error] API呼び出し失敗 ({e})。ローカルLLMにフォールバックします。")
            fallback = LlamaCppAdapter()
            return fallback.generate_text(prompt)


class LlamaCppAdapter(LLMAdapter):
    def __init__(self, endpoint_url: str = None):
        self.endpoint_url = endpoint_url or os.environ.get("LOCAL_LLM_URL", "http://127.0.0.1:11435/completion")

    def generate_text(self, prompt: str) -> str:
        try:
            print(f"🔍 [LLM:Local] Requesting completion from Local LLM ({self.endpoint_url}). Prompt length: {len(prompt)} chars...")
            headers = {"Content-Type": "application/json"}
            payload = {
                "prompt": prompt,
                "temperature": 0.2,
                "n_predict": 2048,
                "stop": ["</s>", "[END_OF_TEXT]"]
            }
            resp = requests.post(self.endpoint_url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("content", "")
            print(f"✅ [LLM:Local] Successfully received {len(content)} chars from local LLM!")
            return content
        except Exception as e:
            print(f"❌ [LLM:Local Error] Local LLM call failed or timed out: {e}")
            return ""


class LLMAdapterFactory:
    @staticmethod
    def get_adapter(provider: str = "gemini") -> LLMAdapter:
        provider_lower = (provider or "gemini").lower()
        if provider_lower == "gemini":
            return GeminiAdapter()
        elif provider_lower in ["local", "llama", "llamacpp"]:
            return LlamaCppAdapter()
        else:
            return GeminiAdapter()

import os
import subprocess
from abc import ABC, abstractmethod

class BaseLLMAdapter(ABC):
    """LLMプロバイダ共通の抽象インターフェース"""
    @abstractmethod
    def generate_text(self, prompt: str, system_instruction: str = "") -> str:
        pass

class GeminiAdapter(BaseLLMAdapter):
    """agy CLI を経由して Gemini を呼び出すアダプター"""
    def __init__(self, model_name: str = ""):
        self.model_name = model_name

    def generate_text(self, prompt: str, system_instruction: str = "") -> str:
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"System Instruction:\n{system_instruction}\n\nUser Request:\n{prompt}"
            
        cmd = ["agy", "-p", full_prompt]
        if self.model_name:
            cmd.extend(["--model", self.model_name])
            
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return res.stdout.strip()
        except Exception as e:
            return f"[Error running agy CLI]: {e}"

class LocalOllamaAdapter(BaseLLMAdapter):
    """Ollama API (/api/generate) アダプター (Python標準ライブラリ使用)"""
    def __init__(self, model_name: str = "devstral-small-2:24b", base_url: str = "http://127.0.0.1:11434"):
        self.model_name = model_name
        # 末尾の /v1 やスラッシュを除去して整形
        url = base_url.rstrip("/")
        if url.endswith("/v1"):
            url = url[:-3]
        self.api_url = f"{url}/api/generate"

    def generate_text(self, prompt: str, system_instruction: str = "") -> str:
        import json
        import urllib.request
        import urllib.error

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        if system_instruction:
            payload["system"] = system_instruction

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.api_url,
            data=data,
            headers={"Content-Type": "application/json"}
        )

        try:
            print(f"   Connecting to Ollama API: {self.api_url} ({self.model_name})...")
            with urllib.request.urlopen(req, timeout=120) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                return res_json.get("response", "").strip()
        except urllib.error.URLError as e:
            return f"[Ollama Connection Error]: Failed to reach {self.api_url}. Reason: {e}"
        except Exception as e:
            return f"[Ollama Error]: {e}"

def get_llm_adapter(provider: str, model_name: str, base_url: str = "") -> BaseLLMAdapter:
    """設定フラグに応じて適切な LLM アダプターインスタンスを返すファクトリ関数"""
    provider = provider.lower().strip()
    if provider == "gemini":
        return GeminiAdapter(model_name=model_name)
    elif provider in ("local_ollama", "ollama", "openai"):
        url = base_url if base_url else "http://localhost:11434/v1"
        return LocalOllamaAdapter(model_name=model_name, base_url=url)
    else:
        # デフォルトフォールバック
        return GeminiAdapter(model_name=model_name)

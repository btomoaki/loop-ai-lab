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
    """Ollama API (/api/generate) アダプター - 後方互換のため保持 (Python標準ライブラリ使用)"""
    def __init__(self, model_name: str = "qwen3.6:27b", base_url: str = "http://127.0.0.1:11434", num_ctx: int = 16384):
        self.model_name = model_name
        self.num_ctx = num_ctx
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
            "stream": False,
            "options": {"num_ctx": self.num_ctx}
        }
        if system_instruction:
            payload["system"] = system_instruction

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.api_url, data=data,
            headers={"Content-Type": "application/json"}
        )
        try:
            print(f"   Connecting to Ollama API: {self.api_url} ({self.model_name}, num_ctx={self.num_ctx})...")
            with urllib.request.urlopen(req, timeout=600) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                return res_json.get("response", "").strip()
        except urllib.error.URLError as e:
            return f"[Ollama Connection Error]: Failed to reach {self.api_url}. Reason: {e}"
        except Exception as e:
            return f"[Ollama Error]: {e}"

class LlamaCppAdapter(BaseLLMAdapter):
    """llama.cpp server (llama-server) OpenAI 互換 API アダプター

    llama-server は /v1/chat/completions エンドポイントを提供する。
    コンテキストウィンドウはサーバー起動時の -c オプションで確定するため
    per-request での num_ctx 指定は不要。
    """
    def __init__(self, model_name: str = "", base_url: str = "http://127.0.0.1:8080",
                 max_tokens: int = 4096, timeout: int = 600):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/v1/chat/completions"
        self.max_tokens = max_tokens
        self.timeout = timeout

    def generate_text(self, prompt: str, system_instruction: str = "") -> str:
        import json
        import urllib.request
        import urllib.error

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        # model フィールドはオプション（llama-server はロード済みモデルを使う）
        if self.model_name:
            payload["model"] = self.model_name

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.api_url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            print(f"   Connecting to llama-server: {self.api_url} (max_tokens={self.max_tokens})...")
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                return res_json["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return f"[LlamaCpp HTTP Error {e.code}]: {body}"
        except urllib.error.URLError as e:
            return f"[LlamaCpp Connection Error]: Failed to reach {self.api_url}. Reason: {e}"
        except Exception as e:
            return f"[LlamaCpp Error]: {e}"

class ClaudeAdapter(BaseLLMAdapter):
    """Anthropic Claude API アダプター (anthropic SDK 使用, 未インストール時は urllib でフォールバック)"""
    def __init__(self, model_name: str = "claude-sonnet-4-5"):
        self.model_name = model_name

    def generate_text(self, prompt: str, system_instruction: str = "") -> str:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return "[Claude Error]: ANTHROPIC_API_KEY 環境変数が未設定です。"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            messages = [{"role": "user", "content": prompt}]
            kwargs = {
                "model": self.model_name,
                "max_tokens": 8192,
                "messages": messages,
            }
            if system_instruction:
                kwargs["system"] = system_instruction
            print(f"   Connecting to Anthropic API ({self.model_name})...")
            response = client.messages.create(**kwargs)
            return response.content[0].text.strip()
        except ImportError:
            return self._generate_via_http(prompt, system_instruction)
        except Exception as e:
            return f"[Claude Error]: {e}"

    def _generate_via_http(self, prompt: str, system_instruction: str = "") -> str:
        """anthropic SDK 未インストール時の urllib フォールバック"""
        import json
        import urllib.request
        import urllib.error

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "max_tokens": 8192,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_instruction:
            payload["system"] = system_instruction

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=data,
            headers=headers,
            method="POST",
        )
        try:
            print(f"   Connecting to Anthropic API via urllib ({self.model_name})...")
            with urllib.request.urlopen(req, timeout=300) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                return res_json["content"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return f"[Claude HTTP Error {e.code}]: {body}"
        except Exception as e:
            return f"[Claude urllib Error]: {e}"

def get_llm_adapter(provider: str, model_name: str, base_url: str = "", num_ctx: int = 16384, max_tokens: int = 4096) -> BaseLLMAdapter:
    """設定フラグに応じて適切な LLM アダプターインスタンスを返すファクトリ関数"""
    provider = provider.lower().strip()
    if provider == "gemini":
        return GeminiAdapter(model_name=model_name)
    elif provider in ("claude", "anthropic"):
        return ClaudeAdapter(model_name=model_name)
    elif provider in ("llama_cpp", "llama"):
        url = base_url if base_url else "http://127.0.0.1:8080"
        return LlamaCppAdapter(model_name=model_name, base_url=url, max_tokens=max_tokens)
    elif provider in ("local_ollama", "ollama", "openai"):
        url = base_url if base_url else "http://localhost:11434/v1"
        return LocalOllamaAdapter(model_name=model_name, base_url=url, num_ctx=num_ctx)
    else:
        # デフォルトフォールバック
        return GeminiAdapter(model_name=model_name)

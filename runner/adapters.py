import sys
import os
import subprocess
from pathlib import Path

class BaseLLMAdapter:
    def generate_text(self, prompt: str, system_instruction: str = "") -> str:
        raise NotImplementedError

class GeminiAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str = "gemini-3.7-flash-low", **kwargs):
        self.model_name = model_name

    def generate_text(self, prompt: str, system_instruction: str = "") -> str:
        print("   Connecting to Cloud Evaluator (Gemini REST / File-based AGY CLI)...", flush=True)
        
        from pathlib import Path
        eval_dir = Path("state/.evaluator")
        eval_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = eval_dir / "latest_prompt.md"
        response_file = eval_dir / "latest_response.md"
        prompt_file.write_text(prompt, encoding="utf-8")

        # 1. First try direct REST API if GEMINI_API_KEY is available
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if api_key:
            import urllib.request
            import json
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=90) as response:
                    res_body = response.read().decode('utf-8')
                    res_json = json.loads(res_body)
                    result_text = res_json['candidates'][0]['content']['parts'][0]['text']
                    response_file.write_text(result_text, encoding="utf-8")
                    return result_text
            except Exception as e:
                print(f"⚠️ [Gemini REST Warning]: {e}", flush=True)

        # 2. Stdin pipe execution using agy / agy-ide CLI prompt
        import shutil
        # Disabled GUI window triggers. Redirecting to LlamaCppAdapter.
        local_llm = LlamaCppAdapter(base_url='http://127.0.0.1:11435')
        return local_llm.generate_text(prompt)
        cmd = [cli_name, "--dangerously-skip-permissions", "prompt"]
        try:
            res = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=300)
            if res.returncode == 0 and res.stdout.strip():
                response_file.write_text(res.stdout, encoding="utf-8")
                return res.stdout
            else:
                print(f"⚠️ [AGY CLI Error]: ReturnCode {res.returncode}, Stderr: {res.stderr[:200]}", flush=True)
        except Exception as e:
            print(f"⚠️ [AGY CLI Exception]: {e}", flush=True)

        return ""


class LocalOllamaAdapter(BaseLLMAdapter):
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
            print(f"   Connecting to Ollama API: {self.api_url} ({self.model_name}, num_ctx={self.num_ctx}, flush=True)...")
            with urllib.request.urlopen(req, timeout=600) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                return res_json.get("response", "").strip()
        except urllib.error.URLError as e:
            return f"[Ollama Connection Error]: Failed to reach {self.api_url}. Reason: {e}"
        except Exception as e:
            return f"[Ollama Error]: {e}"

class LlamaCppAdapter(BaseLLMAdapter):
    def __init__(self, base_url: str = None, model_name: str = "devstral", max_tokens: int = 4096, **kwargs):
        if not base_url:
            base_url = "http://127.0.0.1:11435/completion"
        base_url = base_url.strip()
        if not base_url.endswith("/completion"):
            base_url = base_url.rstrip("/") + "/completion"
        self.endpoint_url = base_url
        self.model_name = model_name
        self.max_tokens = max_tokens

    def generate_text(self, prompt: str, system_instruction: str = "") -> str:
        import urllib.request
        import json
        
        full_prompt = f"[SYSTEM: {system_instruction}]\n\n{prompt}" if system_instruction else prompt
        print(f"🔍 [DEBUG-LLM] Sending Request to Local LLM ({self.endpoint_url}). Prompt length: {len(full_prompt)} chars...", flush=True)
        payload = {
            "prompt": full_prompt,
            "n_predict": int(os.getenv("MAX_TOKENS", 4096)),
            "temperature": 0.2,
            "stop": ["</s>", "USER:", "ASSISTANT:"]
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept-Encoding": "identity",
            "Connection": "close"
        }
        req = urllib.request.Request(self.endpoint_url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=300) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                content = res_json.get("content", "")
                print(f"✅ [DEBUG-LLM] Successfully received {len(content)} chars from Devstral 24B!", flush=True)
                return content
        except Exception as e:
            print(f"❌ [LlamaCpp Error]: {e}", flush=True)
            return ""


class ClaudeAdapter(BaseLLMAdapter):
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
            print(f"   Connecting to Anthropic API ({self.model_name}, flush=True)...")
            response = client.messages.create(**kwargs)
            return response.content[0].text.strip()
        except ImportError:
            return self._generate_via_http(prompt, system_instruction)
        except Exception as e:
            return f"[Claude Error]: {e}"

    def _generate_via_http(self, prompt: str, system_instruction: str = "") -> str:
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
            print(f"   Connecting to Anthropic API via urllib ({self.model_name}, flush=True)...")
            with urllib.request.urlopen(req, timeout=300) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                return res_json["content"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return f"[Claude HTTP Error {e.code}]: {body}"
        except Exception as e:
            return f"[Claude urllib Error]: {e}"

def get_llm_adapter(provider: str, model_name: str = None, base_url: str = None, **kwargs) -> BaseLLMAdapter:
    prov = provider.lower().strip()
    if prov in ("gemini", "google"):
        return GeminiAdapter(model_name=model_name or "gemini-3.7-flash-low", **kwargs)
    elif prov in ("llama_cpp", "llama", "local_ollama", "ollama", "local"):
        return LlamaCppAdapter(base_url=base_url, model_name=model_name or "devstral", **kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

OllamaAdapter = LlamaCppAdapter

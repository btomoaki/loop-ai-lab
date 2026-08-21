#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from runner.adapters import get_llm_adapter

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/test-local-llm.py \"<Instruction prompt to local LLM>\"")
        sys.exit(1)

    prompt = sys.argv[1]
    llm_url = os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:11435")
    
    print(f"📡 Sending Prompt to Local LLM ({llm_url})...\n")
    print(f"--- [PROMPT SENT] ---\n{prompt}\n----------------------\n")

    adapter = get_llm_adapter("llama_cpp", model_name="devstral", base_url=llm_url)
    system_instruction = (
        "You are a pure code generator. Output valid implementation code files "
        "using `# FILE: relative/filepath` markers inside markdown code blocks."
    )

    try:
        output = adapter.generate_text(prompt, system_instruction=system_instruction)
        print("=== [LOCAL LLM RESPONSE] ===")
        print(output)
        print("============================")
    except Exception as e:
        print(f"❌ Error communicating with Local LLM at {llm_url}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

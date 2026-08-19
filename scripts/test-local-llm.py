#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runner.adapters import get_llm_adapter

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/test-local-llm.py \"<Instruction prompt to local LLM>\"")
        sys.exit(1)

    prompt = sys.argv[1]
    print(f"📡 Sending Prompt to Local LLM (llama-server:11435)...\n")
    print(f"--- [PROMPT SENT] ---\n{prompt}\n----------------------\n")

    adapter = get_llm_adapter("llama_cpp", model_name="devstral", base_url="http://127.0.0.1:11435")
    
    system_instruction = "You are a pure code generator. Output valid implementation code files using `# FILE: relative/filepath` markers inside markdown code blocks."
    
    output = adapter.generate_text(prompt, system_instruction=system_instruction)
    
    print("=== [LOCAL LLM RESPONSE] ===")
    print(output)
    print("============================")

if __name__ == "__main__":
    main()

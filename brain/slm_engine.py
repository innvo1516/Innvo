import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests

import config

logger = logging.getLogger("InnvoSLM")

class SLMEngine:
    """
    Real Generative AI Brain for Innvo with Multi-Turn Conversational Context.
    Prioritizes:
    1. Local Ollama Chat API (/api/chat with full history)
    2. Local GGUF via llama-cpp-python chat completion
    3. Intelligent context-aware fallback
    """
    def __init__(self, model_name: str = "gemma2:2b", ollama_host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_host = ollama_host
        self.has_ollama = self._check_ollama()
        self.llm = None
        if not self.has_ollama:
            self._init_llama_cpp()

    def _check_ollama(self) -> bool:
        """Verifies if Ollama is running and has models available."""
        try:
            resp = requests.get(f"{self.ollama_host}/api/tags", timeout=1.5)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                if any(self.model_name in m for m in models):
                    logger.info(f"Connected to local Ollama with {self.model_name}")
                    return True
                elif models:
                    self.model_name = models[0]
                    logger.info(f"Connected to local Ollama with fallback model {self.model_name}")
                    return True
        except Exception as e:
            logger.debug(f"Ollama not reachable: {e}")
        return False

    def _init_llama_cpp(self):
        models_dir = config.BASE_DIR / "models"
        ggufs = list(models_dir.glob("*.gguf")) if models_dir.exists() else []
        if ggufs:
            try:
                from llama_cpp import Llama
                self.llm = Llama(
                    model_path=str(ggufs[0]),
                    n_ctx=2048,
                    n_threads=max(1, os.cpu_count() - 1 if os.cpu_count() else 2),
                    verbose=False
                )
                logger.info(f"Loaded local GGUF model: {ggufs[0].name}")
            except Exception as e:
                logger.debug(f"Could not load GGUF: {e}")

    def is_model_loaded(self) -> bool:
        return self.has_ollama or (self.llm is not None)

    def chat(self, system_prompt: str, history: List[Dict[str, str]], context: str = "") -> str:
        """
        Executes multi-turn conversation with full context preservation.
        history: list of {'role': 'user'|'assistant', 'content': '...'}
        """
        if self.has_ollama:
            return self._chat_ollama(system_prompt, history, context)
        elif self.llm is not None:
            return self._chat_llama_cpp(system_prompt, history, context)
        else:
            last_query = history[-1]["content"] if history else ""
            return self._generate_fallback(last_query, context)

    def _chat_ollama(self, system_prompt: str, history: List[Dict[str, str]], context: str) -> str:
        """Calls Ollama /api/chat with system prompt, real-time grounding, and full history."""
        sys_content = system_prompt
        if context:
            sys_content += f"\n\nGROUNDING CONTEXT (Search / Verified Knowledge):\n{context}"

        messages = [{"role": "system", "content": sys_content}]
        # Append all active conversational turns
        for turn in history:
            messages.append({"role": turn["role"], "content": turn["content"]})

        try:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 200
                }
            }
            res = requests.post(f"{self.ollama_host}/api/chat", json=payload, timeout=25)
            if res.status_code == 200:
                msg = res.json().get("message", {}).get("content", "").strip()
                if msg:
                    return msg
        except Exception as e:
            logger.warning(f"Ollama chat error: {e}")

        last_query = history[-1]["content"] if history else ""
        return self._generate_fallback(last_query, context)

    def _chat_llama_cpp(self, system_prompt: str, history: List[Dict[str, str]], context: str) -> str:
        sys_content = system_prompt
        if context:
            sys_content += f"\n\nContext:\n{context}"

        messages = [{"role": "system", "content": sys_content}]
        for turn in history:
            messages.append({"role": turn["role"], "content": turn["content"]})

        try:
            output = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            return output["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"llama-cpp generation error: {e}")
            last_query = history[-1]["content"] if history else ""
            return self._generate_fallback(last_query, context)

    def generate(self, system_prompt: str, user_prompt: str, context: str = "") -> str:
        """Single-turn generation wrapper for backward compatibility."""
        return self.chat(system_prompt, [{"role": "user", "content": user_prompt}], context)

    def _generate_fallback(self, user_prompt: str, context: str) -> str:
        if context:
            lines = [l for l in context.split("\n") if l.strip() and not l.startswith("[")]
            if lines:
                return f"Maine internet par check kiya sir: {lines[0]}"
        return f"Main aapki baat samajh raha hoon sir. Aapne pucha: '{user_prompt}'."

"""
backend.services.ollama_client

Local LLM client wrapper for Ollama (gemma3:1b).

This module provides a drop-in replacement for the Bedrock client but targets
a locally-running Ollama instance. Used for development and validation before
deploying to AWS Bedrock in production.

Usage:
- Ensure Ollama is running locally (typically http://localhost:11434).
- The model "gemma3:1b" should be pulled: `ollama pull gemma3:1b`.

Note: Ollama's API differs from Bedrock; this client normalizes the request
and response format so agents can call `invoke_reasoner` transparently.
"""

import os
import requests
from typing import List, Dict

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "gemma3:1b")

SYSTEM_PROMPT = (
    "You are JBAC's AI Trading Coach. Teach safely, personalize, explain indicators (RSI/EMA), "
    "and critique trades with actionable, risk-aware feedback. Never give financial advice; "
    "only educational guidance for paper trading."
)


def invoke_reasoner(messages: List[Dict[str, str]], max_tokens: int = 1024, temperature: float = 0.2) -> str:
    """
    Invoke local Ollama model with a messages list and return the text response.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        max_tokens: Maximum tokens to generate (Ollama uses 'num_predict').
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).

    Returns:
        str: The model's generated text response.
    """
    # Ollama /api/chat endpoint expects a specific format
    # Combine system prompt + user messages into a single prompt for simplicity
    # (Ollama also supports a messages API but format varies by version)
    
    # Build a single prompt string from messages
    prompt_parts = [SYSTEM_PROMPT]
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        prompt_parts.append(f"{role.capitalize()}: {content}")
    
    prompt_parts.append("Assistant:")
    full_prompt = "\n\n".join(prompt_parts)
    
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        }
    }
    
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except requests.RequestException as e:
        # Fallback error message if Ollama is not running
        return f"[Ollama Error: {str(e)}. Ensure Ollama is running and model '{MODEL_NAME}' is available.]"

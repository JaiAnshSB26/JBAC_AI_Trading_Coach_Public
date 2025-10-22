"""
backend.services.llm_logger

LLM Transaction Logger for audit trail and debugging.

Logs all LLM interactions to a file with:
- Timestamps
- Provider (Bedrock vs Ollama)
- Model information
- Full request and response
- Token usage and duration
- Errors (if any)

This ensures we can track:
1. Which provider is being used (verify Bedrock in prod)
2. Cost estimation (token usage)
3. Performance metrics (duration)
4. Error patterns
5. Request/response audit trail
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Log file path from environment or default
# Use /tmp for Lambda (read-only filesystem), current dir for local dev
default_log = "/tmp/llm.txt" if os.getenv("AWS_EXECUTION_ENV") else "llm.txt"
LOG_FILE = os.getenv('LLM_LOG_FILE', default_log)


def log_llm_transaction(
    provider: str,
    model: str,
    messages: List[Dict[str, str]],
    response: str,
    tokens_used: Optional[Dict[str, int]] = None,
    duration_ms: Optional[int] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an LLM transaction to file.
    
    Args:
        provider: Provider name ('bedrock', 'ollama', etc.)
        model: Model identifier
        messages: List of message dicts sent to LLM
        response: LLM's response text
        tokens_used: Dict with 'input_tokens' and 'output_tokens' keys
        duration_ms: Request duration in milliseconds
        error: Error message if request failed
        metadata: Additional metadata to log
    """
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    log_entry = {
        'timestamp': timestamp,
        'provider': provider,
        'model': model,
        'messages': messages,
        'response': response[:500] if response else None,  # Truncate long responses in log
        'response_length': len(response) if response else 0,
        'tokens_used': tokens_used or {},
        'duration_ms': duration_ms,
        'error': error,
        'success': error is None,
        'metadata': metadata or {}
    }
    
    try:
        # Ensure log directory exists
        log_dir = os.path.dirname(LOG_FILE) if os.path.dirname(LOG_FILE) else '.'
        if log_dir and log_dir != '.' and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Append log entry as JSON line
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        logger.info(f"LLM transaction logged: {provider}/{model} - {len(response) if response else 0} chars")
        
    except Exception as e:
        logger.error(f"Failed to log LLM transaction: {e}")


def get_transaction_stats() -> Dict[str, Any]:
    """
    Get statistics from the LLM transaction log.
    
    Returns:
        Dict with stats like total_requests, providers used, errors, etc.
    """
    if not os.path.exists(LOG_FILE):
        return {
            'total_requests': 0,
            'providers': {},
            'errors': 0,
            'total_tokens': 0
        }
    
    stats = {
        'total_requests': 0,
        'providers': {},
        'models': {},
        'errors': 0,
        'total_input_tokens': 0,
        'total_output_tokens': 0,
        'avg_duration_ms': 0
    }
    
    durations = []
    
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                
                entry = json.loads(line)
                stats['total_requests'] += 1
                
                provider = entry.get('provider', 'unknown')
                stats['providers'][provider] = stats['providers'].get(provider, 0) + 1
                
                model = entry.get('model', 'unknown')
                stats['models'][model] = stats['models'].get(model, 0) + 1
                
                if not entry.get('success', True):
                    stats['errors'] += 1
                
                tokens = entry.get('tokens_used', {})
                stats['total_input_tokens'] += tokens.get('input_tokens', 0)
                stats['total_output_tokens'] += tokens.get('output_tokens', 0)
                
                duration = entry.get('duration_ms')
                if duration:
                    durations.append(duration)
        
        if durations:
            stats['avg_duration_ms'] = sum(durations) / len(durations)
    
    except Exception as e:
        logger.error(f"Failed to read transaction stats: {e}")
    
    return stats


def clear_log() -> None:
    """Clear the LLM transaction log file."""
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
            logger.info(f"Cleared LLM transaction log: {LOG_FILE}")
    except Exception as e:
        logger.error(f"Failed to clear log: {e}")

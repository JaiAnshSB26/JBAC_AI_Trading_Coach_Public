"""
backend.services.bedrock_client

AWS Bedrock client wrapper supporting multiple models.

This module provides production-ready Bedrock integration with:
- Proper JSON serialization and response parsing
- Comprehensive error handling
- Transaction logging for audit trail
- Token usage tracking
- Performance monitoring

Supported Models:
- Claude 3.5 Sonnet v2 (anthropic.claude-3-5-sonnet-20241022-v2:0)
  - Context: 200K tokens, Max output: 8,192 tokens
- Amazon Nova Micro (amazon.nova-micro-v1:0)
  - Context: 128K tokens, Max output: 5,000 tokens
  - Lowest cost option
"""

import json
import logging
import time
from typing import List, Dict
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)  # Force override system env vars

# Import centralized settings and logger
from backend.config import settings
from backend.services.llm_logger import log_llm_transaction

logger = logging.getLogger(__name__)

# AWS Configuration from centralized settings
REGION = settings.aws_region
MODEL_ID = settings.bedrock_model_id
AWS_ACCESS_KEY_ID = settings.aws_access_key_id
AWS_SECRET_ACCESS_KEY = settings.aws_secret_access_key

# Initialize Bedrock client
try:
    import os
    session_token = os.getenv('AWS_SESSION_TOKEN')  # For AWS Academy/Learner Lab
    
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        if session_token:
            # AWS Academy/Learner Lab with session token
            _session = boto3.Session(
                region_name=REGION,
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                aws_session_token=session_token
            )
            logger.info("Bedrock initialized with session token (AWS Academy)")
        else:
            # Regular AWS account
            _session = boto3.Session(
                region_name=REGION,
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY
            )
            logger.info("Bedrock initialized with access key")
    else:
        # Fall back to default credential chain
        _session = boto3.Session(region_name=REGION)
        logger.info("Bedrock initialized with default credentials")
    
    _bedrock = _session.client(
        "bedrock-runtime",
        config=Config(retries={"max_attempts": 3, "mode": "adaptive"})
    )
    logger.info(f"✓ Bedrock client initialized: {MODEL_ID} in {REGION}")
except Exception as e:
    logger.error(f"Failed to initialize Bedrock client: {e}")
    _bedrock = None


# System prompt for AI Trading Coach
SYSTEM_PROMPT = (
    "You are JBAC's AI Trading Coach. Provide clear, concise responses in plain text.\n\n"
    "CRITICAL FORMATTING RULES:\n"
    "1. DO NOT repeat the user's question\n"
    "2. DO NOT use markdown formatting (no **, ##, -, *, etc.)\n"
    "3. Write in plain paragraphs with natural line breaks\n"
    "4. Start directly with your answer\n"
    "5. Be concise - keep responses under 300 words unless analysis requires more\n\n"
    "CONTENT GUIDELINES:\n"
    "- Teach trading concepts safely and clearly\n"
    "- Explain indicators (RSI, EMA, MACD) when relevant\n"
    "- Provide actionable, risk-aware feedback\n"
    "- Never give financial advice - only educational guidance\n"
    "- Focus on paper trading and learning\n\n"
    "RESPONSE STRUCTURE:\n"
    "- Decision first (BUY/SELL/HOLD/WAIT)\n"
    "- Key reasoning (2-3 sentences)\n"
    "- Supporting details if needed\n"
    "- Risk considerations\n"
    "- Next steps for the user"
)


def invoke_reasoner(
    messages: List[Dict[str, str]],
    max_tokens: int = 1024,
    temperature: float = 0.2
) -> str:
    """
    Invoke AWS Bedrock with messages (supports Claude and Nova models).
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        max_tokens: Maximum tokens to generate (default 1024)
        temperature: Sampling temperature 0.0-1.0 (default 0.2)
    
    Returns:
        str: The model's generated text response
        
    Raises:
        Exception: If Bedrock call fails
    """
    start_time = time.time()
    error_msg = None
    response_text = ""
    tokens_used = {}
    
    try:
        if not _bedrock:
            raise Exception("Bedrock client not initialized. Check AWS credentials.")
        
        # Detect model type and build appropriate request body
        is_claude = MODEL_ID.startswith("anthropic.claude")
        is_nova = MODEL_ID.startswith("amazon.nova")
        
        if is_claude:
            # Claude API format (Anthropic Messages API)
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "system": SYSTEM_PROMPT,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stop_sequences": ["\n\nHuman:", "\n\nUser:"]  # Prevent runaway responses
            }
        elif is_nova:
            # Amazon Nova API format (different structure)
            # Nova requires:
            # 1. Content must be array of objects with "text" key
            # 2. No "system" role in messages (use separate system field)
            # 3. Only "user" and "assistant" roles allowed in messages
            
            # Convert messages to Nova format
            nova_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                # Skip system messages (already in system field)
                if role == "system":
                    continue
                
                # Convert content to array format if it's a string
                if isinstance(content, str):
                    content_array = [{"text": content}]
                else:
                    content_array = content  # Already in array format
                
                nova_messages.append({
                    "role": role,
                    "content": content_array
                })
            
            request_body = {
                "messages": nova_messages,
                "system": [{"text": SYSTEM_PROMPT}],
                "inferenceConfig": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens,
                    "stopSequences": ["\n\nHuman:", "\n\nUser:"]  # Prevent runaway responses
                }
            }
        else:
            # Generic fallback
            request_body = {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        
        logger.info(f"Invoking Bedrock: {MODEL_ID} (max_tokens={max_tokens}, temp={temperature})")
        
        # Invoke Bedrock with proper JSON serialization
        response = _bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_body)  # Correct JSON serialization
        )
        
        # Parse response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        
        # Track if response was truncated
        stop_reason = None
        
        # Extract text based on model type
        if is_claude:
            # Claude returns: {"content": [{"type": "text", "text": "..."}], "usage": {...}, "stop_reason": "..."}
            if 'content' in response_body and len(response_body['content']) > 0:
                response_text = response_body['content'][0].get('text', '')
            else:
                response_text = str(response_body)
            
            # Check stop reason
            stop_reason = response_body.get('stop_reason')
            
            # Extract token usage (Claude format)
            if 'usage' in response_body:
                tokens_used = {
                    'input_tokens': response_body['usage'].get('input_tokens', 0),
                    'output_tokens': response_body['usage'].get('output_tokens', 0)
                }
                
        elif is_nova:
            # Nova returns: {"output": {"message": {"content": [{"text": "..."}]}}, "usage": {...}, "stopReason": "..."}
            if 'output' in response_body and 'message' in response_body['output']:
                message = response_body['output']['message']
                if 'content' in message and len(message['content']) > 0:
                    response_text = message['content'][0].get('text', '')
                else:
                    response_text = str(response_body)
            else:
                response_text = str(response_body)
            
            # Check stop reason
            stop_reason = response_body.get('stopReason')
            
            # Extract token usage (Nova format)
            if 'usage' in response_body:
                tokens_used = {
                    'input_tokens': response_body['usage'].get('inputTokens', 0),
                    'output_tokens': response_body['usage'].get('outputTokens', 0)
                }
        else:
            # Generic fallback
            response_text = str(response_body)
            if 'usage' in response_body:
                tokens_used = response_body['usage']
        
        # Check if response was truncated due to max_tokens
        if stop_reason == 'max_tokens' or stop_reason == 'length':
            logger.warning(
                f"⚠️  Response truncated due to max_tokens limit ({max_tokens}). "
                f"Consider increasing max_tokens for this agent."
            )
            # Append warning to response for user visibility
            response_text += "\n\n[Note: Response was truncated. The analysis may be incomplete.]"
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"✓ Bedrock response: {len(response_text)} chars, "
            f"{tokens_used.get('input_tokens', 0)} in + {tokens_used.get('output_tokens', 0)} out tokens, "
            f"{duration_ms}ms, stop_reason={stop_reason or 'end_turn'}"
        )
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        logger.error(f"Bedrock ClientError [{error_code}]: {error_msg}")
        duration_ms = int((time.time() - start_time) * 1000)
        response_text = f"[Bedrock Error: {error_code} - {error_msg}]"
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Bedrock invocation failed: {error_msg}", exc_info=True)
        duration_ms = int((time.time() - start_time) * 1000)
        response_text = f"[Bedrock Error: {error_msg}]"
    
    finally:
        # Log transaction for audit trail
        log_llm_transaction(
            provider="bedrock",
            model=MODEL_ID,
            messages=messages,
            response=response_text,
            tokens_used=tokens_used if tokens_used else None,
            duration_ms=duration_ms if 'duration_ms' in locals() else None,
            error=error_msg,
            metadata={
                'max_tokens': max_tokens,
                'temperature': temperature,
                'region': REGION
            }
        )
    
    return response_text

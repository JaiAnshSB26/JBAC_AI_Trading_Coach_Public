"""
LLM Agents Lambda Handler

Lightweight Lambda for running AI agents (planner, coach, critic) via AWS Bedrock.
No heavy dependencies - just boto3 and bedrock API calls.

Event format:
{
    "agent": "planner" | "coach" | "critic",
    "messages": [...],  # Standard message format
    "max_tokens": 1024,  # optional
    "temperature": 0.2,  # optional
    "context": {...}  # agent-specific context
}
"""

import json
import logging
import os
import time
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Bedrock Configuration
REGION = os.environ.get('AWS_REGION', 'us-east-1')
MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')

# Initialize Bedrock client
bedrock = boto3.client(
    "bedrock-runtime",
    region_name=REGION,
    config=Config(retries={"max_attempts": 3, "mode": "adaptive"})
)

# System prompts for each agent
SYSTEM_PROMPTS = {
    "planner": (
        "Create a compact, level-based curriculum for the user's goal. "
        "Return JSON with levels and lessons."
    ),
    "coach": (
        "You are a friendly trading coach who explains concepts clearly in plain text.\n\n"
        "CRITICAL FORMATTING:\n"
        "- DO NOT repeat the user's question\n"
        "- Write in plain text (NO markdown, NO **, NO ##)\n"
        "- Use simple numbered lists (1. 2. 3.) instead of bullets\n"
        "- Keep explanations clear and concise\n\n"
        "CONTENT:\n"
        "- Explain trading concepts with real examples\n"
        "- Break down complex ideas into simple steps\n"
        "- Provide practical, actionable guidance\n"
        "- Educational only - never give financial advice\n"
        "- Focus on paper trading and learning"
    ),
    "critic": (
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
    ),
    "synthesizer": (
        "Synthesize trade analysis into a clear, actionable recommendation.\n"
        "Provide: Decision, Reasoning, Risk Assessment, Next Steps."
    )
}


def invoke_bedrock(messages, agent_type="coach", max_tokens=1024, temperature=0.2):
    """
    Invoke AWS Bedrock with messages.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        agent_type: Type of agent (for system prompt selection)
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        
    Returns:
        str: Generated text response
    """
    start_time = time.time()
    
    try:
        # Get appropriate system prompt
        system_prompt = SYSTEM_PROMPTS.get(agent_type, SYSTEM_PROMPTS["coach"])
        
        # Detect model type
        is_claude = MODEL_ID.startswith("anthropic.claude")
        is_nova = MODEL_ID.startswith("amazon.nova")
        
        if is_claude:
            # Claude API format
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "system": system_prompt,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stop_sequences": ["\n\nHuman:", "\n\nUser:"]
            }
        elif is_nova:
            # Amazon Nova format
            nova_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    continue
                
                if isinstance(content, str):
                    content_array = [{"text": content}]
                else:
                    content_array = content
                
                nova_messages.append({
                    "role": role,
                    "content": content_array
                })
            
            request_body = {
                "messages": nova_messages,
                "system": [{"text": system_prompt}],
                "inferenceConfig": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens,
                    "stopSequences": ["\n\nHuman:", "\n\nUser:"]
                }
            }
        else:
            # Generic fallback
            request_body = {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        
        logger.info(f"Invoking Bedrock: {MODEL_ID} (agent={agent_type}, max_tokens={max_tokens})")
        
        # Invoke Bedrock
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        
        # Extract text based on model type
        response_text = ""
        tokens_used = {}
        
        if is_claude:
            if 'content' in response_body and len(response_body['content']) > 0:
                response_text = response_body['content'][0].get('text', '')
            
            if 'usage' in response_body:
                tokens_used = {
                    'input_tokens': response_body['usage'].get('input_tokens', 0),
                    'output_tokens': response_body['usage'].get('output_tokens', 0)
                }
                
        elif is_nova:
            if 'output' in response_body and 'message' in response_body['output']:
                message = response_body['output']['message']
                if 'content' in message and len(message['content']) > 0:
                    response_text = message['content'][0].get('text', '')
            
            if 'usage' in response_body:
                tokens_used = {
                    'input_tokens': response_body['usage'].get('inputTokens', 0),
                    'output_tokens': response_body['usage'].get('outputTokens', 0)
                }
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"✓ Bedrock response: {len(response_text)} chars, "
            f"{tokens_used.get('input_tokens', 0)} in + {tokens_used.get('output_tokens', 0)} out tokens, "
            f"{duration_ms}ms"
        )
        
        return response_text
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        logger.error(f"Bedrock ClientError [{error_code}]: {error_msg}")
        raise Exception(f"Bedrock Error: {error_code} - {error_msg}")
        
    except Exception as e:
        logger.error(f"Bedrock invocation failed: {e}", exc_info=True)
        raise


def lambda_handler(event, context):
    """
    AWS Lambda handler for LLM agent operations.
    
    Expected event format:
    {
        "agent": "planner" | "coach" | "critic" | "synthesizer",
        "messages": [{"role": "user", "content": "..."}],
        "max_tokens": 1024,  # optional
        "temperature": 0.2,  # optional
        "context": {...}  # agent-specific context
    }
    """
    try:
        logger.info(f"LLM Agents Lambda invoked: {json.dumps(event)}")
        
        # Parse event (handle API Gateway or direct invocation)
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        agent = body.get('agent', 'coach')
        messages = body.get('messages', [])
        max_tokens = body.get('max_tokens', 1024)
        temperature = body.get('temperature', 0.2)
        agent_context = body.get('context', {})
        
        if not messages:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'messages are required'})
            }
        
        # Build context-aware message if context provided
        if agent_context:
            context_str = json.dumps(agent_context, indent=2)
            
            # Add context to first user message
            if messages and messages[0].get('role') == 'user':
                original_content = messages[0]['content']
                messages[0]['content'] = f"Context:\n{context_str}\n\n{original_content}"
        
        # Invoke Bedrock
        response_text = invoke_bedrock(
            messages=messages,
            agent_type=agent,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'agent': agent,
                'response': response_text,
                'model': MODEL_ID
            })
        }
    
    except Exception as e:
        logger.error(f"Lambda error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

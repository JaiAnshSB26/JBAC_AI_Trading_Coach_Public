"""
backend.services.lambda_client

Helper module for invoking AWS Lambda functions from the FastAPI backend.

This module provides a clean interface to call our modular Lambda functions:
- Market Data Lambda (yfinance + pandas + indicators)
- LLM Agents Lambda (Bedrock-based agents: planner, coach, critic)

Usage:
    from backend.services.lambda_client import get_market_data, invoke_agent
    
    # Get market data
    latest = get_market_data(action='get_latest', symbol='AAPL')
    
    # Invoke agent
    response = invoke_agent(agent='coach', question='What is RSI?')
"""

import json
import logging
import os
from typing import Dict, List, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Lambda Configuration
REGION = os.getenv('AWS_REGION', 'us-east-1')
MARKET_DATA_FUNCTION = os.getenv('LAMBDA_MARKET_DATA_FUNCTION', 'jbac-market-data')
LLM_AGENTS_FUNCTION = os.getenv('LAMBDA_LLM_AGENTS_FUNCTION', 'jbac-llm-agents')

# Initialize Lambda client
try:
    lambda_client = boto3.client('lambda', region_name=REGION)
    logger.info(f"✓ Lambda client initialized for region {REGION}")
except Exception as e:
    logger.error(f"Failed to initialize Lambda client: {e}")
    lambda_client = None


def get_market_data(action: str, symbol: str, period: str = '1mo', interval: str = '1d') -> Optional[Dict]:
    """
    Invoke Market Data Lambda to fetch market data.
    
    Args:
        action: 'get_latest' | 'get_candles' | 'get_with_indicators'
        symbol: Stock ticker symbol
        period: Time period (for candles)
        interval: Data interval (for candles)
    
    Returns:
        Dict with market data or None if failed
    """
    if not lambda_client:
        logger.error("Lambda client not initialized")
        return None
    
    try:
        payload = {
            'action': action,
            'symbol': symbol,
            'period': period,
            'interval': interval
        }
        
        logger.info(f"Invoking Market Data Lambda: {action} for {symbol}")
        
        response = lambda_client.invoke(
            FunctionName=MARKET_DATA_FUNCTION,
            InvocationType='RequestResponse',  # Synchronous
            Payload=json.dumps(payload)
        )
        
        # Parse response
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            body = json.loads(result['body']) if isinstance(result.get('body'), str) else result
            logger.info(f"✓ Market Data Lambda response: {action} for {symbol}")
            return body
        else:
            logger.error(f"Market Data Lambda error: {result}")
            return None
            
    except ClientError as e:
        logger.error(f"Lambda invocation failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Error calling Market Data Lambda: {e}")
        return None


def invoke_agent(
    agent: str,
    messages: Optional[List[Dict]] = None,
    question: str = None,
    context: Optional[Dict] = None,
    max_tokens: int = 1024,
    temperature: float = 0.2
) -> Optional[str]:
    """
    Invoke LLM Agents Lambda to run Bedrock-based agents.
    
    Args:
        agent: 'planner' | 'coach' | 'critic' | 'synthesizer'
        messages: List of message dicts (if None, built from question)
        question: User question (used if messages not provided)
        context: Additional context for the agent
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
    
    Returns:
        Generated text response or None if failed
    """
    if not lambda_client:
        logger.error("Lambda client not initialized")
        return None
    
    try:
        # Build messages if not provided
        if not messages:
            if not question:
                logger.error("Either messages or question must be provided")
                return None
            messages = [{'role': 'user', 'content': question}]
        
        payload = {
            'agent': agent,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        if context:
            payload['context'] = context
        
        logger.info(f"Invoking LLM Agents Lambda: {agent}")
        
        response = lambda_client.invoke(
            FunctionName=LLM_AGENTS_FUNCTION,
            InvocationType='RequestResponse',  # Synchronous
            Payload=json.dumps(payload)
        )
        
        # Parse response
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            body = json.loads(result['body']) if isinstance(result.get('body'), str) else result
            response_text = body.get('response', '')
            logger.info(f"✓ LLM Agents Lambda response: {agent} ({len(response_text)} chars)")
            return response_text
        else:
            logger.error(f"LLM Agents Lambda error: {result}")
            return None
            
    except ClientError as e:
        logger.error(f"Lambda invocation failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Error calling LLM Agents Lambda: {e}")
        return None


def get_latest_price(symbol: str) -> Optional[Dict]:
    """
    Convenience wrapper for getting latest price.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Dict with latest price data
    """
    result = get_market_data('get_latest', symbol)
    return result.get('latest') if result else None


def get_candles_with_indicators(symbol: str, period: str = '1mo', interval: str = '1d') -> Optional[List]:
    """
    Convenience wrapper for getting candles with technical indicators.
    
    Args:
        symbol: Stock ticker symbol
        period: Time period
        interval: Data interval
        
    Returns:
        List of candle dicts with indicators
    """
    result = get_market_data('get_with_indicators', symbol, period, interval)
    return result.get('candles') if result else None


def plan_curriculum(goal: str, risk_level: str, symbols: List[str]) -> Optional[str]:
    """
    Convenience wrapper for Planner agent.
    
    Args:
        goal: User's learning goal
        risk_level: Risk tolerance
        symbols: List of symbols to focus on
        
    Returns:
        JSON-like curriculum string
    """
    question = f"Goal: {goal}\nRisk: {risk_level}\nSymbols: {symbols}\nReturn JSON with levels -> lessons (title, brief, practice)."
    return invoke_agent('planner', question=question, max_tokens=700)


def coach_user(context: str, question: str) -> Optional[str]:
    """
    Convenience wrapper for Coach agent.
    
    Args:
        context: Learning context
        question: User's question
        
    Returns:
        Educational response
    """
    full_question = f"Context: {context}\n\nQuestion: {question}\n\nProvide a clear, helpful answer in plain text. Do not repeat the question."
    return invoke_agent('coach', question=full_question, max_tokens=800)


def critique_trade(
    symbol: str,
    action: str,
    reason: str,
    indicators: Dict,
    planner_analysis: str = None,
    market_data: Dict = None
) -> Optional[str]:
    """
    Convenience wrapper for Critic agent.
    
    Args:
        symbol: Stock ticker
        action: 'buy' | 'sell' | 'hold'
        reason: User's reasoning
        indicators: Technical indicators dict
        planner_analysis: Optional planner output
        market_data: Optional market data context
        
    Returns:
        Critique and recommendation
    """
    context = {
        'symbol': symbol,
        'action': action,
        'reason': reason,
        'indicators': indicators
    }
    
    if planner_analysis:
        context['planner_analysis'] = planner_analysis
    if market_data:
        context['market_data'] = market_data
    
    question = f"Symbol: {symbol}\nAction: {action}\nReason: {reason}\nIndicators: {json.dumps(indicators)}"
    
    if planner_analysis:
        question += f"\n\nPlanner Analysis:\n{planner_analysis}"
    
    return invoke_agent('critic', question=question, context=context, max_tokens=800)


# Health check for Lambda functions
def check_lambda_health() -> Dict[str, bool]:
    """
    Check if Lambda functions are accessible.
    
    Returns:
        Dict with function names and health status
    """
    health = {}
    
    if not lambda_client:
        return {'market_data': False, 'llm_agents': False, 'error': 'Lambda client not initialized'}
    
    # Check Market Data Lambda
    try:
        lambda_client.get_function(FunctionName=MARKET_DATA_FUNCTION)
        health['market_data'] = True
    except:
        health['market_data'] = False
    
    # Check LLM Agents Lambda
    try:
        lambda_client.get_function(FunctionName=LLM_AGENTS_FUNCTION)
        health['llm_agents'] = True
    except:
        health['llm_agents'] = False
    
    return health

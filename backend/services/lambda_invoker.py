"""
Lambda Invoker Service
Handles all Lambda function invocations from EC2 FastAPI server.
"""
import json
import boto3
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Initialize Lambda client
lambda_client = boto3.client('lambda', region_name='us-east-1')

async def invoke_lambda(
    function_name: str, 
    payload: Dict[str, Any],
    invocation_type: str = 'RequestResponse'
) -> Dict[str, Any]:
    """
    Invoke a Lambda function and return the response.
    
    Args:
        function_name: Name of the Lambda function
        payload: Dictionary to send as payload
        invocation_type: 'RequestResponse' (sync) or 'Event' (async)
    
    Returns:
        Parsed JSON response from Lambda
    """
    try:
        logger.info(f"Invoking Lambda function: {function_name}")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType=invocation_type,
            Payload=json.dumps(payload)
        )
        
        # Parse the response
        if invocation_type == 'RequestResponse':
            result = json.loads(response['Payload'].read())
            
            # Check for Lambda execution errors
            if response.get('FunctionError'):
                logger.error(f"Lambda function error: {result}")
                return {
                    "statusCode": 500,
                    "body": json.dumps({
                        "error": "Lambda execution failed",
                        "details": result
                    })
                }
            
            return result
        else:
            # Async invocation
            return {
                "statusCode": 202,
                "body": json.dumps({"message": "Request accepted for processing"})
            }
            
    except Exception as e:
        logger.error(f"Error invoking Lambda {function_name}: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


# ====================================================================
# Helper Functions for Specific Lambda Invocations
# DEPLOYED LAMBDAS: jbac-market-data, jbac-llm-agents
# ====================================================================

async def invoke_market_data_lambda(
    action: str,
    symbol: Optional[str] = None,
    period: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Invoke market data Lambda function.
    
    Actions: 
    - get_latest_price: Get current quote
    - get_candles: Get historical OHLCV data
    - get_with_indicators: Get price + RSI, EMA20, EMA50
    """
    payload = {
        "action": action,
        "symbol": symbol,
        "period": period,
        **kwargs
    }
    
    return await invoke_lambda('jbac-market-data', payload)


async def invoke_llm_agent_lambda(
    agent_type: str,
    question: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Invoke LLM agent Lambda function.
    
    Agent types: coach, critic, planner
    - coach: Trading education and explanations
    - critic: Trade evaluation and feedback
    - planner: Learning path recommendations
    """
    # Lambda expects "messages" array format (Bedrock chat API)
    payload = {
        "agent": agent_type,
        "messages": [
            {
                "role": "user",
                "content": question
            }
        ],
        "context": context or {},
        "max_tokens": 2048,
        "temperature": 0.2
    }
    
    return await invoke_lambda('jbac-llm-agents', payload)


# ====================================================================
# Health Check Function
# ====================================================================

async def check_lambda_health() -> Dict[str, bool]:
    """
    Check health of all deployed Lambda functions.
    Returns dict with function name as key and health status as value.
    """
    lambda_functions = [
        'jbac-market-data',
        'jbac-llm-agents'
    ]
    
    health_status = {}
    
    for func_name in lambda_functions:
        try:
            # Test with a simple action
            if func_name == 'jbac-market-data':
                result = await invoke_lambda(
                    func_name,
                    {"action": "get_latest_price", "symbol": "AAPL"}
                )
            else:  # jbac-llm-agents
                result = await invoke_lambda(
                    func_name,
                    {"agent": "coach", "question": "Hello"}
                )
            
            # Check if response is successful
            health_status[func_name] = result.get('statusCode', 200) in [200, 201]
        except Exception as e:
            logger.error(f"Health check failed for {func_name}: {str(e)}")
            health_status[func_name] = False
    
    return health_status

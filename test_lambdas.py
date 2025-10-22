#!/usr/bin/env python3
"""
Test Lambda functions from Python

This script tests both Market Data and LLM Agents Lambda functions
using boto3 directly from Python.

Usage:
    python test_lambdas.py
"""

import boto3
import json
import sys
from datetime import datetime

# Configuration
REGION = 'us-east-1'
MARKET_DATA_FUNCTION = 'jbac-market-data'
LLM_AGENTS_FUNCTION = 'jbac-llm-agents'

# Initialize Lambda client
lambda_client = boto3.client('lambda', region_name=REGION)

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")

def invoke_lambda(function_name, payload):
    """Invoke a Lambda function and return the result"""
    try:
        print(f"Invoking {function_name}...")
        start_time = datetime.now()
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        duration = (datetime.now() - start_time).total_seconds() * 1000
        result = json.loads(response['Payload'].read())
        
        print(f"✅ Response received in {duration:.0f}ms")
        print(f"Status Code: {response['StatusCode']}")
        
        return result, duration
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, 0

def test_market_data():
    """Test Market Data Lambda"""
    print_section("Testing Market Data Lambda")
    
    # Test 1: Get latest price
    print("Test 1: Get latest price for AAPL")
    result, duration = invoke_lambda(MARKET_DATA_FUNCTION, {
        'action': 'get_latest',
        'symbol': 'AAPL'
    })
    
    if result:
        body = json.loads(result['body']) if isinstance(result.get('body'), str) else result
        if 'latest' in body:
            latest = body['latest']
            print(f"\n📊 AAPL Latest Price:")
            print(f"  Date: {latest['time']}")
            print(f"  Close: ${latest['close']:.2f}")
            print(f"  Volume: {latest['volume']:,}")
    
    print("\n" + "-" * 60 + "\n")
    
    # Test 2: Get candles
    print("Test 2: Get candles for TSLA (5 days)")
    result, duration = invoke_lambda(MARKET_DATA_FUNCTION, {
        'action': 'get_candles',
        'symbol': 'TSLA',
        'period': '5d'
    })
    
    if result:
        body = json.loads(result['body']) if isinstance(result.get('body'), str) else result
        if 'candles' in body:
            candles = body['candles']
            print(f"\n📈 TSLA Candles: {len(candles)} days")
            if candles:
                latest = candles[-1]
                print(f"  Latest: ${latest['close']:.2f} on {latest['time']}")
    
    print("\n" + "-" * 60 + "\n")
    
    # Test 3: Get with indicators
    print("Test 3: Get candles with indicators for NVDA")
    result, duration = invoke_lambda(MARKET_DATA_FUNCTION, {
        'action': 'get_with_indicators',
        'symbol': 'NVDA',
        'period': '1mo'
    })
    
    if result:
        body = json.loads(result['body']) if isinstance(result.get('body'), str) else result
        if 'candles' in body:
            candles = body['candles']
            print(f"\n📊 NVDA with Indicators: {len(candles)} days")
            if candles:
                latest = candles[-1]
                print(f"  Close: ${latest['close']:.2f}")
                print(f"  RSI: {latest.get('rsi', 'N/A'):.2f}")
                print(f"  EMA20: ${latest.get('ema20', 0):.2f}")
                print(f"  EMA50: ${latest.get('ema50', 0):.2f}")

def test_llm_agents():
    """Test LLM Agents Lambda"""
    print_section("Testing LLM Agents Lambda")
    
    # Test 1: Coach agent
    print("Test 1: Coach - Explain RSI")
    result, duration = invoke_lambda(LLM_AGENTS_FUNCTION, {
        'agent': 'coach',
        'messages': [
            {'role': 'user', 'content': 'What is RSI in simple terms?'}
        ],
        'max_tokens': 300
    })
    
    if result:
        body = json.loads(result['body']) if isinstance(result.get('body'), str) else result
        if 'response' in body:
            response_text = body['response']
            print(f"\n🤖 Coach Response ({len(response_text)} chars):")
            print(f"  {response_text[:200]}...")
            print(f"\n  Model: {body.get('model', 'unknown')}")
    
    print("\n" + "-" * 60 + "\n")
    
    # Test 2: Planner agent
    print("Test 2: Planner - Create learning plan")
    result, duration = invoke_lambda(LLM_AGENTS_FUNCTION, {
        'agent': 'planner',
        'messages': [
            {
                'role': 'user',
                'content': 'Goal: Learn technical analysis basics\nRisk: low\nSymbols: ["AAPL", "MSFT"]\nReturn JSON with levels and lessons.'
            }
        ],
        'max_tokens': 500
    })
    
    if result:
        body = json.loads(result['body']) if isinstance(result.get('body'), str) else result
        if 'response' in body:
            response_text = body['response']
            print(f"\n📚 Planner Response ({len(response_text)} chars):")
            print(f"  {response_text[:200]}...")
    
    print("\n" + "-" * 60 + "\n")
    
    # Test 3: Critic agent
    print("Test 3: Critic - Evaluate trade idea")
    result, duration = invoke_lambda(LLM_AGENTS_FUNCTION, {
        'agent': 'critic',
        'messages': [
            {
                'role': 'user',
                'content': 'Symbol: AAPL\nAction: buy\nReason: RSI is oversold at 28\nIndicators: {"close": 175.5, "rsi": 28, "ema20": 180, "ema50": 178}'
            }
        ],
        'max_tokens': 500
    })
    
    if result:
        body = json.loads(result['body']) if isinstance(result.get('body'), str) else result
        if 'response' in body:
            response_text = body['response']
            print(f"\n⚖️  Critic Response ({len(response_text)} chars):")
            print(f"  {response_text[:200]}...")

def check_functions_exist():
    """Check if Lambda functions exist"""
    print_section("Checking Lambda Functions")
    
    functions = {
        'Market Data': MARKET_DATA_FUNCTION,
        'LLM Agents': LLM_AGENTS_FUNCTION
    }
    
    all_exist = True
    for name, func_name in functions.items():
        try:
            lambda_client.get_function(FunctionName=func_name)
            print(f"✅ {name} ({func_name}) exists")
        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"❌ {name} ({func_name}) NOT FOUND")
            all_exist = False
        except Exception as e:
            print(f"⚠️  {name} ({func_name}): {e}")
            all_exist = False
    
    return all_exist

def main():
    """Main test function"""
    print_section("🧪 Lambda Functions Test Suite")
    print(f"Region: {REGION}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if functions exist
    if not check_functions_exist():
        print("\n❌ Some Lambda functions are missing!")
        print("\nTo deploy, run:")
        print("  bash lambdas/manual_test.sh")
        sys.exit(1)
    
    # Test Market Data Lambda
    try:
        test_market_data()
    except Exception as e:
        print(f"\n❌ Market Data tests failed: {e}")
    
    # Test LLM Agents Lambda
    try:
        test_llm_agents()
    except Exception as e:
        print(f"\n❌ LLM Agents tests failed: {e}")
    
    print_section("✅ All Tests Complete!")
    print("\nNext steps:")
    print("  1. Check CloudWatch logs for detailed execution info")
    print("  2. Monitor costs in AWS Cost Explorer")
    print("  3. Integrate lambda_client.py into your backend")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)

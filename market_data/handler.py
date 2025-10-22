"""
Market Data Lambda Handler

Lambda for fetching market data using yfinance.
Responds to API Gateway events with OHLCV data and technical indicators.

Event format:
{
    "action": "get_latest" | "get_candles" | "get_with_indicators",
    "symbol": "AAPL",
    "period": "1mo",  # optional, for candles
    "interval": "1d"  # optional, for candles
}
"""

import json
import logging
import os
from datetime import datetime, timedelta
import time

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
YFINANCE_MAX_RETRIES = 3
YFINANCE_RETRY_DELAY = 1

# Import dependencies
try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    logger.info("yfinance, pandas, numpy loaded successfully")
except ImportError as e:
    logger.error(f"Failed to import required dependencies: {e}")
    raise


def _fetch_yfinance_with_retry(symbol: str, period: str = "1mo", interval: str = "1d"):
    """Fetch data from yfinance with retry logic."""
    for attempt in range(YFINANCE_MAX_RETRIES):
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"yfinance returned empty data for {symbol} (attempt {attempt+1})")
                time.sleep(YFINANCE_RETRY_DELAY)
                continue
            
            if df['Close'].isna().all():
                logger.warning(f"yfinance returned all NaN values for {symbol} (attempt {attempt+1})")
                time.sleep(YFINANCE_RETRY_DELAY)
                continue
            
            logger.info(f"✓ yfinance fetched {len(df)} rows for {symbol}")
            return df
            
        except Exception as e:
            logger.warning(f"yfinance attempt {attempt+1} failed for {symbol}: {e}")
            if attempt < YFINANCE_MAX_RETRIES - 1:
                time.sleep(YFINANCE_RETRY_DELAY * (attempt + 1))
            continue
    
    logger.error(f"All yfinance retry attempts failed for {symbol}")
    return None


def get_latest_price(symbol: str) -> dict:
    """Get the most recent trading data for a symbol."""
    try:
        logger.info(f"Fetching latest price for {symbol}")
        
        df = _fetch_yfinance_with_retry(symbol, period="5d", interval="1d")
        
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            result = {
                'time': latest.name.isoformat() if hasattr(latest.name, 'isoformat') else str(latest.name),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'close': float(latest['Close']),
                'volume': int(latest['Volume'])
            }
            logger.info(f"✓ Latest price for {symbol}: ${result['close']:.2f}")
            return result
        
        logger.warning(f"No data available for {symbol}")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching latest price for {symbol}: {e}")
        return None


def get_candles(symbol: str, period: str = "1mo", interval: str = "1d") -> list:
    """Fetch candlestick data for a symbol."""
    try:
        logger.info(f"Fetching candles for {symbol} (period={period}, interval={interval})")
        
        df = _fetch_yfinance_with_retry(symbol, period=period, interval=interval)
        
        if df is not None and not df.empty:
            # Convert to list of dicts
            candles = []
            for idx, row in df.iterrows():
                candles.append({
                    'time': idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            
            logger.info(f"✓ Fetched {len(candles)} candles for {symbol}")
            return candles
        
        logger.warning(f"No data available for {symbol}")
        return []
        
    except Exception as e:
        logger.error(f"Error fetching candles for {symbol}: {e}")
        return []


def add_indicators(candles: list) -> list:
    """Add technical indicators to candle data."""
    try:
        if not candles or len(candles) < 50:
            logger.warning(f"Insufficient data for indicators ({len(candles)} candles)")
            # Add default indicators even with insufficient data
            for candle in candles:
                candle['rsi'] = 50.0
                candle['ema20'] = candle['close']
                candle['ema50'] = candle['close']
            return candles
        
        df = pd.DataFrame(candles)
        df['close'] = pd.to_numeric(df['close'])
        
        # RSI calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # EMA calculation
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        # Fill NaN values
        df = df.ffill().bfill()
        df['rsi'] = df['rsi'].fillna(50.0)
        df['ema20'] = df['ema20'].fillna(df['close'])
        df['ema50'] = df['ema50'].fillna(df['close'])
        
        # Convert back to list of dicts
        result = df.to_dict(orient='records')
        logger.info(f"✓ Added indicators to {len(result)} candles")
        return result
        
    except Exception as e:
        logger.error(f"Error adding indicators: {e}")
        # Return candles with default indicators
        for candle in candles:
            if 'rsi' not in candle:
                candle['rsi'] = 50.0
            if 'ema20' not in candle:
                candle['ema20'] = candle['close']
            if 'ema50' not in candle:
                candle['ema50'] = candle['close']
        return candles


def lambda_handler(event, context):
    """
    AWS Lambda handler for market data operations.
    
    Expected event format:
    {
        "action": "get_latest" | "get_candles" | "get_with_indicators",
        "symbol": "AAPL",
        "period": "1mo",  # optional
        "interval": "1d"  # optional
    }
    """
    try:
        logger.info(f"Market Data Lambda invoked: {json.dumps(event)}")
        
        # Parse event (handle API Gateway or direct invocation)
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        action = body.get('action')
        symbol = body.get('symbol')
        period = body.get('period', '1mo')
        interval = body.get('interval', '1d')
        
        if not symbol:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'symbol is required'})
            }
        
        # Route to appropriate handler
        if action == 'get_latest':
            data = get_latest_price(symbol)
            if data:
                return {
                    'statusCode': 200,
                    'body': json.dumps({'latest': data})
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': f'No data available for {symbol}'})
                }
        
        elif action == 'get_candles':
            candles = get_candles(symbol, period, interval)
            return {
                'statusCode': 200,
                'body': json.dumps({'candles': candles, 'count': len(candles)})
            }
        
        elif action == 'get_with_indicators':
            candles = get_candles(symbol, period, interval)
            if candles:
                candles_with_indicators = add_indicators(candles)
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'candles': candles_with_indicators,
                        'count': len(candles_with_indicators)
                    })
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': f'No data available for {symbol}'})
                }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid action',
                    'valid_actions': ['get_latest', 'get_candles', 'get_with_indicators']
                })
            }
    
    except Exception as e:
        logger.error(f"Lambda error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

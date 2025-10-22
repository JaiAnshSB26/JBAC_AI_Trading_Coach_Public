"""
backend.services.market_data

Helpers for fetching OHLCV candles and computing common technical
indicators (RSI, EMA). The module returns Pandas DataFrames to be consumed by
the API, agents and UI. Keeping indicator computation here centralizes the
versioning of indicator logic for reproducibility.

Supports multiple data providers:
- yfinance: Free, unlimited, but can be unstable (default)
- Alpha Vantage: Free tier 25 calls/day, more reliable

Includes fallback mock data for development when API fails.
"""

import logging
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time

# Import centralized settings
from backend.config import settings

logger = logging.getLogger(__name__)

# Get configuration from environment
MARKET_DATA_PROVIDER = os.getenv('MARKET_DATA_PROVIDER', 'yfinance')
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY', 'FPXZUAULUKGBNX0Z')

# yfinance retry configuration
YFINANCE_MAX_RETRIES = 3
YFINANCE_RETRY_DELAY = 1  # seconds


# yfinance retry configuration
YFINANCE_MAX_RETRIES = 3
YFINANCE_RETRY_DELAY = 1  # seconds


def _fetch_yfinance_with_retry(symbol: str, period: str = "1mo", interval: str = "1d"):
    """
    Fetch data from yfinance with retry logic and proper error handling.
    
    Args:
        symbol: Stock ticker
        period: Time period (1d, 5d, 1mo, 3mo, 1y, etc.)
        interval: Data interval (1m, 5m, 1h, 1d, etc.)
    
    Returns:
        pandas DataFrame or None if all retries fail
    """
    try:
        import yfinance as yf
    except ImportError:
        logger.error("yfinance not installed. Install with: pip install yfinance")
        return None
    
    for attempt in range(YFINANCE_MAX_RETRIES):
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"yfinance returned empty data for {symbol} (attempt {attempt+1}/{YFINANCE_MAX_RETRIES})")
                time.sleep(YFINANCE_RETRY_DELAY)
                continue
            
            # Validate data quality
            if df['Close'].isna().all():
                logger.warning(f"yfinance returned all NaN values for {symbol} (attempt {attempt+1}/{YFINANCE_MAX_RETRIES})")
                time.sleep(YFINANCE_RETRY_DELAY)
                continue
            
            logger.info(f"✓ yfinance fetched {len(df)} rows for {symbol}")
            return df
            
        except Exception as e:
            logger.warning(f"yfinance attempt {attempt+1}/{YFINANCE_MAX_RETRIES} failed for {symbol}: {e}")
            if attempt < YFINANCE_MAX_RETRIES - 1:
                time.sleep(YFINANCE_RETRY_DELAY * (attempt + 1))  # Exponential backoff
            continue
    
    logger.error(f"All yfinance retry attempts failed for {symbol}")
    return None


def get_latest_price(symbol: str) -> dict:
    """
    Get the most recent trading data for a symbol.
    Supports multiple data providers based on MARKET_DATA_PROVIDER env var.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
    
    Returns:
        Dictionary with latest OHLCV data and timestamp, or None if fails
    """
    # Try yfinance first if configured
    if MARKET_DATA_PROVIDER == 'yfinance':
        try:
            logger.info(f"Fetching latest price for {symbol} using yfinance")
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
                logger.info(f"✓ Latest price for {symbol}: ${result['close']:.2f} (yfinance)")
                return result
        except Exception as e:
            logger.warning(f"yfinance failed for {symbol}: {e}, falling back to Alpha Vantage")
    
    # Fall back to or use Alpha Vantage
    try:
        logger.info(f"Fetching latest price for {symbol} using Alpha Vantage")
        
        if not ALPHA_VANTAGE_KEY:
            logger.error("ALPHA_VANTAGE_KEY not configured")
            return None
        
        # Method 1: Try Alpha Vantage quote endpoint (fastest, real-time)
        try:
            from alpha_vantage.timeseries import TimeSeries
            
            ts = TimeSeries(key=ALPHA_VANTAGE_KEY, output_format='json')
            data, meta = ts.get_quote_endpoint(symbol=symbol)
            
            if data and '05. price' in data:
                result = {
                    'time': data.get('07. latest trading day', datetime.now().strftime('%Y-%m-%d')),
                    'open': float(data.get('02. open', 0)),
                    'high': float(data.get('03. high', 0)),
                    'low': float(data.get('04. low', 0)),
                    'close': float(data.get('05. price', 0)),
                    'volume': int(data.get('06. volume', 0))
                }
                logger.info(f"✓ Latest price for {symbol}: ${result['close']:.2f} (Alpha Vantage quote)")
                return result
        except Exception as e:
            logger.warning(f"Alpha Vantage quote failed for {symbol}: {e}")
        
        # Method 2: Try Alpha Vantage daily data endpoint
        try:
            from alpha_vantage.timeseries import TimeSeries
            
            ts = TimeSeries(key=ALPHA_VANTAGE_KEY, output_format='pandas')
            data, meta = ts.get_daily(symbol=symbol, outputsize='compact')
            
            if not data.empty:
                latest = data.iloc[0]  # Most recent row
                latest_date = data.index[0]
                
                result = {
                    'time': latest_date.isoformat() if hasattr(latest_date, 'isoformat') else str(latest_date),
                    'open': float(latest['1. open']),
                    'high': float(latest['2. high']),
                    'low': float(latest['3. low']),
                    'close': float(latest['4. close']),
                    'volume': int(latest['5. volume'])
                }
                logger.info(f"✓ Latest price for {symbol}: ${result['close']:.2f} (Alpha Vantage daily)")
                return result
        except Exception as e:
            logger.warning(f"Alpha Vantage daily failed for {symbol}: {e}")
        
        # Method 3: Final fallback - try candles() function with recent data
        logger.info(f"Trying candles() fallback for {symbol}")
        df = candles(symbol, period="5d", interval="1d")
        
        if not df.empty:
            latest = df.iloc[-1]
            result = {
                'time': latest['time'].isoformat() if hasattr(latest['time'], 'isoformat') else str(latest['time']),
                'open': float(latest['open']),
                'high': float(latest['high']),
                'low': float(latest['low']),
                'close': float(latest['close']),
                'volume': int(latest['volume'])
            }
            logger.info(f"✓ Latest price for {symbol}: ${result['close']:.2f} (candles fallback)")
            return result
        
        logger.warning(f"All methods failed to get latest price for {symbol}")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching latest price for {symbol}: {e}")
        return None


def _generate_mock_data(symbol: str, period: str = "6mo") -> pd.DataFrame:
    """Generate mock market data for development/testing when API fails."""
    logger.warning(f"Generating mock data for {symbol} (API unavailable)")
    
    # Parse period to get number of days
    period_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
    days = period_map.get(period, 180)
    
    # Generate dates
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=days, freq='D')
    
    # Generate realistic-looking price data with trend and volatility
    base_price = 150.0  # Starting price
    trend = 0.0002  # Slight upward trend
    volatility = 0.02  # 2% daily volatility
    
    prices = [base_price]
    for i in range(1, days):
        change = np.random.normal(trend, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    # Generate OHLCV data
    df = pd.DataFrame({
        'time': dates,
        'open': [p * (1 + np.random.uniform(-0.01, 0.01)) for p in prices],
        'high': [p * (1 + abs(np.random.uniform(0, 0.02))) for p in prices],
        'low': [p * (1 - abs(np.random.uniform(0, 0.02))) for p in prices],
        'close': prices,
        'volume': [np.random.randint(50000000, 150000000) for _ in range(days)]
    })
    
    logger.info(f"Generated {len(df)} rows of mock data for {symbol}")
    return df


def _fetch_alpha_vantage(symbol: str, period: str = "6mo") -> pd.DataFrame:
    """Fetch data from Alpha Vantage API."""
    try:
        from alpha_vantage.timeseries import TimeSeries
        
        if not ALPHA_VANTAGE_KEY:
            logger.error("ALPHA_VANTAGE_KEY not set in environment")
            return pd.DataFrame()
        
        logger.info(f"Fetching {symbol} from Alpha Vantage")
        ts = TimeSeries(key=ALPHA_VANTAGE_KEY, output_format='pandas')
        
        # Get daily data (Alpha Vantage provides up to 20 years of daily data)
        data, meta = ts.get_daily(symbol=symbol, outputsize='full')
        
        # Rename columns to match our format
        df = data.reset_index()
        df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        
        # Filter by period
        period_map = {"1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "5y": 1825}
        days = period_map.get(period, 180)
        cutoff_date = datetime.now() - timedelta(days=days)
        df['time'] = pd.to_datetime(df['time'])
        df = df[df['time'] >= cutoff_date]
        
        logger.info(f"✓ Fetched {len(df)} rows from Alpha Vantage for {symbol}")
        return df
        
    except ImportError:
        logger.error("alpha-vantage library not installed. Run: pip install alpha-vantage")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Alpha Vantage error for {symbol}: {e}")
        return pd.DataFrame()


def candles(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch candlestick data for a symbol using configured data provider.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', etc.)
        interval: Data interval ('1m', '5m', '1h', '1d', etc.)
    
    Returns:
        Pandas DataFrame with columns: time, open, high, low, close, volume
    """
    # Try yfinance first if configured
    if MARKET_DATA_PROVIDER == 'yfinance':
        try:
            logger.info(f"Fetching {symbol} from yfinance (period={period}, interval={interval})")
            df = _fetch_yfinance_with_retry(symbol, period=period, interval=interval)
            
            if df is not None and not df.empty:
                # Normalize column names to match our format
                df_normalized = pd.DataFrame({
                    'time': df.index,
                    'open': df['Open'].values,
                    'high': df['High'].values,
                    'low': df['Low'].values,
                    'close': df['Close'].values,
                    'volume': df['Volume'].values
                })
                logger.info(f"✓ Fetched {len(df_normalized)} rows from yfinance for {symbol}")
                return df_normalized
        except Exception as e:
            logger.warning(f"yfinance failed for {symbol}: {e}, falling back to Alpha Vantage")
    
    # Fall back to Alpha Vantage
    df = _fetch_alpha_vantage(symbol, period)
    
    if not df.empty:
        logger.info(f"✓ Fetched {len(df)} rows from Alpha Vantage for {symbol}")
        return df
    
    # Final fallback: mock data
    logger.warning(f"Alpha Vantage failed for {symbol}, using mock data")
    return _generate_mock_data(symbol, period)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators to market data.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added columns: rsi, ema20, ema50
    """
    try:
        df = df.copy()
        
        # Ensure we have enough data for indicators
        if len(df) < 50:
            logger.warning(f"Insufficient data for indicators ({len(df)} rows), padding with NaN")
        
        # Try using ta library first (for local dev)
        try:
            import ta
            df["rsi"] = ta.momentum.rsi(df["close"], window=14)
            df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
            df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)
        except ImportError:
            # Fallback: Calculate indicators manually (Lambda-compatible)
            logger.info("Using manual indicator calculations (ta library not available)")
            
            # Manual RSI calculation
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))
            
            # Manual EMA calculation
            df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
            df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
        
        # Fill NaN values with forward fill then backward fill
        df = df.ffill().bfill()
        
        # If still NaN (very short data), use simple defaults
        if df["rsi"].isna().any():
            df["rsi"] = df["rsi"].fillna(50.0)
        if df["ema20"].isna().any():
            df["ema20"] = df["ema20"].fillna(df["close"])
        if df["ema50"].isna().any():
            df["ema50"] = df["ema50"].fillna(df["close"])
        
        return df
    except Exception as e:
        logger.error(f"Error adding indicators: {e}", exc_info=True)
        # Return original dataframe with NaN indicators if calculation fails
        df["rsi"] = 50.0
        df["ema20"] = df["close"]
        df["ema50"] = df["close"]
        return df
"""
ui.app

Streamlit-based demo UI that calls the FastAPI backend. Keeps the UI thin
and uses simple REST calls to the endpoints defined in `backend.app`.

Responsibilities:
- Provide interactive controls for initializing demo users, generating
  curricula, viewing market snapshots, submitting trades for critique, and
  executing paper trades.
"""

import os
import streamlit as st
import requests

st.set_page_config(page_title="JBAC AI Trading Coach", layout="wide")

# Get API base URL from environment variable or use default
# No secrets.toml required - uses environment variables with sensible defaults
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
API_PREFIX = os.getenv("API_PREFIX", "/api")

# Construct full API URLs
def api_url(endpoint: str) -> str:
    """Build full API URL with prefix."""
    return f"{API_BASE}{API_PREFIX}{endpoint}"

st.title("JBAC AI Trading Coach")
st.markdown("*Learn trading safely with AI-powered coaching and paper trading*")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    user_id = st.text_input("User ID", value="demo-user", help="Your unique user identifier")
    st.info(f"API: {API_BASE}{API_PREFIX}")
    
    # Health check
    try:
        health_response = requests.get(api_url("/health"), timeout=2)
        if health_response.status_code == 200:
            health_data = health_response.json()
            st.success(f"Backend: {health_data.get('status', 'unknown')}")
            st.caption(f"Model: {health_data.get('model_provider', 'N/A')}")
        else:
            st.error("Backend unhealthy")
    except Exception as e:
        st.error(f"Backend offline")
        st.caption(str(e))

# Initialize Portfolio
st.header("Initialize Portfolio")
col1, col2 = st.columns([3, 1])
with col1:
    initial_cash = st.number_input("Starting Cash ($)", value=500.0, min_value=100.0, step=100.0)
with col2:
    if st.button("Initialize Portfolio", use_container_width=True):
        try:
            r = requests.post(api_url("/init"), json={"user_id": user_id, "cash": initial_cash})
            r.raise_for_status()
            st.success("Portfolio initialized!")
            st.json(r.json())
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.divider()

# Plan Curriculum
st.header("Generate Learning Plan")
goal = st.text_input("Learning Goal", value="Teach me options trading with $500", 
                     help="Describe what you want to learn")
col1, col2 = st.columns(2)
with col1:
    risk = st.selectbox("Risk Level", ["low", "medium", "high"], index=1)
with col2:
    symbols = st.text_input("Symbols (comma-separated)", value="AAPL,MSFT,TSLA")

if st.button("Generate Plan", use_container_width=True):
    with st.spinner("Generating personalized curriculum..."):
        try:
            r = requests.post(
                api_url("/plan"),
                json={
                    "user_id": user_id,
                    "goal": goal,
                    "risk_level": risk,
                    "symbols": [s.strip() for s in symbols.split(",")]
                }
            )
            r.raise_for_status()
            result = r.json()
            st.success("Plan generated!")
            st.text_area("Curriculum Plan", result.get("plan", ""), height=300)
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.divider()

# Coach Section
st.header("AI Coach - Micro-Lessons")
st.markdown("Get personalized guidance and bite-sized lessons")

if st.button("Ask Coach for Next Lessons", use_container_width=True):
    with st.spinner("Coach is preparing your lessons..."):
        try:
            r = requests.post(
                api_url("/coach"),
                json={
                    "user_id": user_id,
                    "goal": goal,
                    "risk_level": risk,
                    "symbols": [s.strip() for s in symbols.split(",")]
                }
            )
            r.raise_for_status()
            result = r.json()
            st.success("Lessons ready!")
            st.markdown(result.get("answer", ""))
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.divider()

# Market Data & Critique
st.header("Market Analysis & Trade Critique")

col1, col2 = st.columns(2)
with col1:
    symbol = st.text_input("Symbol", value="AAPL", key="market_symbol")
with col2:
    action = st.selectbox("Action", ["buy", "sell"])

reason = st.text_input("Your Reasoning", value="RSI looks oversold", 
                       help="Explain why you want to make this trade")

col1, col2 = st.columns(2)

with col1:
    if st.button("View Market Data", use_container_width=True):
        with st.spinner(f"Fetching data for {symbol}..."):
            try:
                r = requests.get(api_url(f"/market/{symbol}"))
                r.raise_for_status()
                result = r.json()
                st.success(f"Latest data for {symbol}")
                
                latest = result.get("latest", {})
                metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
                metrics_col1.metric("Close", f"${latest.get('close', 0):.2f}")
                metrics_col2.metric("RSI", f"{latest.get('rsi', 0):.2f}")
                metrics_col3.metric("EMA20", f"${latest.get('ema20', 0):.2f}")
                metrics_col4.metric("EMA50", f"${latest.get('ema50', 0):.2f}")
                
                with st.expander("View Full Data"):
                    st.json(latest)
            except Exception as e:
                st.error(f"Error: {str(e)}")

with col2:
    if st.button("Critique My Trade", use_container_width=True):
        with st.spinner("AI Critic is analyzing your trade..."):
            try:
                r = requests.post(
                    api_url("/critique"),
                    json={
                        "user_id": user_id,
                        "symbol": symbol,
                        "action": action,
                        "reason": reason
                    }
                )
                r.raise_for_status()
                result = r.json()
                st.success("Critique ready!")
                
                st.subheader("Market Indicators")
                indicators = result.get("indicators", {})
                ind_col1, ind_col2, ind_col3, ind_col4 = st.columns(4)
                ind_col1.metric("Close", f"${indicators.get('close', 0):.2f}")
                ind_col2.metric("RSI", f"{indicators.get('rsi', 0):.2f}")
                ind_col3.metric("EMA20", f"${indicators.get('ema20', 0):.2f}")
                ind_col4.metric("EMA50", f"${indicators.get('ema50', 0):.2f}")
                
                st.subheader("AI Judgment")
                st.info(result.get("judgment", ""))
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.divider()

# Paper Trading
st.header("Paper Trading")
st.markdown("Execute simulated trades to practice without risk")

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    trade_symbol = st.text_input("Symbol", value="AAPL", key="trade_symbol")
with col2:
    trade_side = st.selectbox("Side", ["buy", "sell"], key="trade_side")
with col3:
    quantity = st.number_input("Quantity", value=1.0, min_value=0.1, step=0.1)

if st.button("Execute Paper Trade", use_container_width=True, type="primary"):
    with st.spinner("Executing trade..."):
        try:
            r = requests.post(
                api_url("/paper_trade"),
                json={
                    "user_id": user_id,
                    "symbol": trade_symbol,
                    "side": trade_side,
                    "quantity": quantity
                }
            )
            r.raise_for_status()
            result = r.json()
            st.success(f"Trade executed at ${result.get('fill_price', 0):.2f}")
            
            state = result.get("state", {})
            st.subheader("Updated Portfolio")
            
            port_col1, port_col2 = st.columns(2)
            port_col1.metric("Cash", f"${state.get('cash', 0):.2f}")
            port_col2.metric("Positions", len(state.get('positions', [])))
            
            if state.get('positions'):
                st.subheader("Positions")
                for pos in state['positions']:
                    st.write(f"**{pos['symbol']}**: {pos['quantity']} shares @ ${pos['avg_price']:.2f}")
            
            with st.expander("View Trade History"):
                st.json(state.get('history', []))
        except requests.HTTPException as e:
            if e.response.status_code == 404:
                st.warning("User not found. Please initialize your portfolio first.")
            else:
                st.error(f"Error: {str(e)}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.divider()
st.caption("Powered by AI • Educational purposes only • Not financial advice")
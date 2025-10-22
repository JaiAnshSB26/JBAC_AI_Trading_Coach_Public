"""
backend.app

HTTP API for JBAC AI Trading Coach.

This module wires the FastAPI routes to domain models, agents, and services.
It intentionally keeps handlers thin and delegates business logic to
`backend.agents.*` and `backend.services.*` so they are easier to test.

Routes provided (all under /api prefix):
- POST /api/init        : create a demo user portfolio
- POST /api/plan        : ask Planner for a curriculum/plan
- GET  /api/market/{sym}: return market snapshot with indicators
- POST /api/coach       : ask Coach for micro-lessons
- POST /api/critique    : run Critic on a proposed trade
- POST /api/paper_trade : run a simulated paper trade via the portfolio sim
- GET  /api/health      : health check endpoint

Note: keep this module focused on transport concerns (request parsing,
response shaping) rather than embedding business rules.
"""

import logging
import os
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)  # Force override system env vars

from .config import settings
from .domain import CoachRequest, PortfolioState, CritiqueRequest
from .services import market_data as md
from .services.portfolio_sim import execute_trade
from .services.persistence import load_user, save_user
from .services.auth_service import get_auth_service

# Agents removed - logic now in Lambda (jbac-llm-agents)
# We'll call Lambda functions instead of local agents
# from .agents.planner import plan_curriculum
# from .agents.coach import coach_user
# from .agents.critic import critique_trade

# Import Lambda invoker for AI agent calls
from .services.lambda_invoker import invoke_llm_agent_lambda

# Helper function to extract text from Lambda response
def extract_lambda_response(result: dict) -> str:
    """Extract the actual response text from Lambda return value"""
    if isinstance(result, dict):
        # Lambda returns: {"statusCode": 200, "body": "{\"response\": \"text\"}"}
        if 'body' in result:
            import json
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            return body.get('response', str(body))
        # Direct response (no API Gateway wrapper)
        elif 'response' in result:
            return result['response']
    return str(result)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize services with fallback to local storage
USE_LOCAL_STORAGE = os.getenv('USE_LOCAL_STORAGE', 'true').lower() == 'true'

if USE_LOCAL_STORAGE:
    logger.info("✓ Using local file storage for development")
    from .services.local_storage import get_local_storage
    db_service = get_local_storage()
else:
    try:
        from .services.dynamodb_service import get_db_service
        db_service = get_db_service()
        logger.info("✓ Using DynamoDB for data storage")
    except Exception as e:
        logger.error(f"DynamoDB initialization failed: {e}")
        logger.info("✓ Falling back to local file storage")
        from .services.local_storage import get_local_storage
        db_service = get_local_storage()

auth_service = get_auth_service(db_service)


# Authentication dependency
async def get_current_user_dep(authorization: Optional[str] = Header(None)):
    """Dependency to get current authenticated user"""
    user = auth_service.get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


# Request Models
class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str


class CreatePortfolioRequest(BaseModel):
    portfolio_name: str
    initial_value: float = 10000.0
    tracked_symbols: Optional[list[str]] = None


class AddSymbolRequest(BaseModel):
    symbol: str


class ExecuteTradeRequest(BaseModel):
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    trade_type: str = "market"


class TradeInput(BaseModel):
    user_id: str
    symbol: str
    side: str  # "buy" or "sell"
    quantity: int


class TradeAnalysisRequest(BaseModel):
    idea: str


class CoachQueryRequest(BaseModel):
    user_query: str
    user_level: str = "beginner"
    focus_area: str = "general"


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Health check endpoint
@app.get(f"{settings.api_prefix}/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    db_status = db_service.health_check()
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.app_env,
        "model_provider": settings.model_provider,
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }


# =========================
# AUTHENTICATION ENDPOINTS
# =========================

@app.post(f"{settings.api_prefix}/auth/register")
async def register(req: RegisterRequest):
    """Register a new user with email/password"""
    try:
        user, token = auth_service.register_user(
            email=req.email,
            password=req.password,
            display_name=req.display_name
        )
        logger.info(f"New user registered: {user['email']}")
        return {
            "user": {
                "user_id": user['user_id'],
                "email": user['email'],
                "display_name": user['display_name']
            },
            "token": token
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@app.post(f"{settings.api_prefix}/auth/login")
async def login(req: LoginRequest):
    """Login with email/password"""
    try:
        user, token = auth_service.login_user(req.email, req.password)
        logger.info(f"User logged in: {user['email']}")
        return {
            "user": {
                "user_id": user['user_id'],
                "email": user['email'],
                "display_name": user['display_name'],
                "default_portfolio_id": user.get('default_portfolio_id')
            },
            "token": token
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@app.post(f"{settings.api_prefix}/auth/google")
async def google_auth(req: GoogleAuthRequest):
    """Authenticate with Google OAuth"""
    try:
        user, token = auth_service.authenticate_google(req.id_token)
        logger.info(f"Google auth successful: {user['email']}")
        return {
            "user": {
                "user_id": user['user_id'],
                "email": user['email'],
                "display_name": user['display_name'],
                "default_portfolio_id": user.get('default_portfolio_id')
            },
            "token": token
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Google auth error: {e}")
        raise HTTPException(status_code=500, detail="Google authentication failed")


@app.get(f"{settings.api_prefix}/auth/me")
async def get_me(current_user: dict = Depends(get_current_user_dep)):
    """Get current user profile"""
    return {
        "user_id": current_user['user_id'],
        "email": current_user['email'],
        "display_name": current_user['display_name'],
        "default_portfolio_id": current_user.get('default_portfolio_id'),
        "preferences": current_user.get('preferences', {}),
        "oauth_provider": current_user.get('oauth_provider')
    }


# =========================
# PORTFOLIO ENDPOINTS
# =========================

@app.get(f"{settings.api_prefix}/portfolios")
async def get_portfolios(current_user: dict = Depends(get_current_user_dep)):
    """Get all portfolios for current user"""
    try:
        portfolios = db_service.get_user_portfolios(current_user['user_id'])
        logger.info(f"Retrieved {len(portfolios)} portfolios for user {current_user['email']}")
        return {"portfolios": portfolios}
    except Exception as e:
        logger.error(f"Error getting portfolios: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve portfolios")


@app.post(f"{settings.api_prefix}/portfolios")
async def create_portfolio(
    req: CreatePortfolioRequest,
    current_user: dict = Depends(get_current_user_dep)
):
    """Create a new portfolio"""
    try:
        portfolio = db_service.create_portfolio(
            user_id=current_user['user_id'],
            portfolio_name=req.portfolio_name,
            initial_value=req.initial_value,
            tracked_symbols=req.tracked_symbols
        )
        logger.info(f"Portfolio created: {portfolio['portfolio_id']} for user {current_user['email']}")
        
        # Set as default if user has no default portfolio
        if not current_user.get('default_portfolio_id'):
            db_service.update_default_portfolio(current_user['user_id'], portfolio['portfolio_id'])
        
        return {"portfolio": portfolio}
    except Exception as e:
        logger.error(f"Error creating portfolio: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portfolio")


@app.get(f"{settings.api_prefix}/portfolios/{{portfolio_id}}")
async def get_portfolio_detail(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user_dep)
):
    """Get detailed portfolio information"""
    try:
        portfolio = db_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Verify ownership
        if portfolio['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update positions with current prices
        for position in portfolio.get('positions', []):
            try:
                latest_data = md.get_latest_price(position['symbol'])
                if latest_data:
                    current_price = latest_data['close']
                    position['current_price'] = current_price
                    position['current_value'] = position['quantity'] * current_price
                    cost_basis = position['quantity'] * position['avg_cost']
                    position['unrealized_pnl'] = position['current_value'] - cost_basis
                    position['pnl_percent'] = (position['unrealized_pnl'] / cost_basis * 100) if cost_basis > 0 else 0.0
            except Exception as e:
                logger.warning(f"Failed to update price for {position['symbol']}: {e}")
        
        # Recalculate total value
        total_positions_value = sum(p.get('current_value', 0) for p in portfolio.get('positions', []))
        portfolio['total_value'] = portfolio['current_balance'] + total_positions_value
        
        return {"portfolio": portfolio}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve portfolio")


@app.delete(f"{settings.api_prefix}/portfolios/{{portfolio_id}}")
async def delete_portfolio(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user_dep)
):
    """Delete (deactivate) a portfolio"""
    try:
        portfolio = db_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Verify ownership
        if portfolio['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete portfolio
        success = db_service.delete_portfolio(portfolio_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete portfolio")
        
        # If this was default portfolio, clear it
        if current_user.get('default_portfolio_id') == portfolio_id:
            db_service.update_default_portfolio(current_user['user_id'], None)
        
        logger.info(f"Portfolio deleted: {portfolio_id}")
        return {"success": True, "message": "Portfolio deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting portfolio: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete portfolio")


@app.put(f"{settings.api_prefix}/portfolios/{{portfolio_id}}/activate")
async def activate_portfolio(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user_dep)
):
    """Set a portfolio as the active/default portfolio"""
    try:
        portfolio = db_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Verify ownership
        if portfolio['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update user's default portfolio
        db_service.update_default_portfolio(current_user['user_id'], portfolio_id)
        
        logger.info(f"Portfolio activated: {portfolio_id} for user {current_user['email']}")
        return {"success": True, "portfolio_id": portfolio_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating portfolio: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate portfolio")


# =========================
# MARKET SYMBOL ENDPOINTS
# =========================

@app.post(f"{settings.api_prefix}/portfolios/{{portfolio_id}}/symbols")
async def add_tracked_symbol(
    portfolio_id: str,
    req: AddSymbolRequest,
    current_user: dict = Depends(get_current_user_dep)
):
    """Add a symbol to portfolio's tracked symbols"""
    try:
        portfolio = db_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Verify ownership
        if portfolio['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        updated_portfolio = db_service.add_tracked_symbol(portfolio_id, req.symbol.upper())
        logger.info(f"Symbol {req.symbol} added to portfolio {portfolio_id}")
        return {"portfolio": updated_portfolio}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding tracked symbol: {e}")
        raise HTTPException(status_code=500, detail="Failed to add symbol")


@app.delete(f"{settings.api_prefix}/portfolios/{{portfolio_id}}/symbols/{{symbol}}")
async def remove_tracked_symbol(
    portfolio_id: str,
    symbol: str,
    current_user: dict = Depends(get_current_user_dep)
):
    """Remove a symbol from portfolio's tracked symbols"""
    try:
        portfolio = db_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Verify ownership
        if portfolio['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        updated_portfolio = db_service.remove_tracked_symbol(portfolio_id, symbol.upper())
        logger.info(f"Symbol {symbol} removed from portfolio {portfolio_id}")
        return {"portfolio": updated_portfolio}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing tracked symbol: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove symbol")


@app.get(f"{settings.api_prefix}/portfolios/{{portfolio_id}}/symbols")
async def get_tracked_symbols(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user_dep)
):
    """Get tracked symbols for a portfolio"""
    try:
        portfolio = db_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Verify ownership
        if portfolio['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {"symbols": portfolio.get('tracked_symbols', [])}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tracked symbols: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve symbols")


# =========================
# TRADE ENDPOINTS (Updated for DynamoDB)
# =========================

@app.post(f"{settings.api_prefix}/portfolios/{{portfolio_id}}/trades")
async def execute_trade_endpoint(
    portfolio_id: str,
    req: ExecuteTradeRequest,
    current_user: dict = Depends(get_current_user_dep)
):
    """Execute a trade in a portfolio"""
    try:
        portfolio = db_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Verify ownership
        if portfolio['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get current market price
        latest_data = md.get_latest_price(req.symbol)
        if not latest_data:
            raise HTTPException(status_code=404, detail=f"No market data available for {req.symbol}")
        
        price = latest_data['close']
        
        # Execute trade
        trade = db_service.execute_trade(
            portfolio_id=portfolio_id,
            symbol=req.symbol.upper(),
            side=req.side.lower(),
            quantity=req.quantity,
            price=price,
            trade_type=req.trade_type
        )
        
        logger.info(f"Trade executed: {req.side} {req.quantity} {req.symbol} @ ${price:.2f}")
        return {"trade": trade, "message": "Trade executed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute trade")


@app.get(f"{settings.api_prefix}/portfolios/{{portfolio_id}}/trades")
async def get_portfolio_trades(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user_dep),
    symbol: Optional[str] = None,
    limit: int = 50
):
    """Get trade history for a portfolio"""
    try:
        portfolio = db_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Verify ownership
        if portfolio['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        trades = db_service.get_portfolio_trades(
            portfolio_id=portfolio_id,
            symbol=symbol.upper() if symbol else None,
            limit=limit
        )
        
        return {"trades": trades, "count": len(trades)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trades")


# =========================
# LEGACY ENDPOINTS (Kept for backward compatibility)
# =========================
class InitRequest(BaseModel):
    user_id: str
    cash: float = 500.0


class TradeInput(BaseModel):
    user_id: str
    symbol: str
    side: str
    quantity: float


# API Routes
@app.post(f"{settings.api_prefix}/init")
async def init_user(req: InitRequest):
    """Initialize a new user portfolio with starting cash."""
    try:
        logger.info(f"Initializing user: {req.user_id} with cash: {req.cash}")
        state = PortfolioState(cash=req.cash)
        save_user(req.user_id, state.model_dump())
        return {"ok": True, "state": state}
    except Exception as e:
        logger.error(f"Error initializing user {req.user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize user: {str(e)}")


@app.post(f"{settings.api_prefix}/plan")
async def plan(req: CoachRequest):
    """Generate a curriculum/learning plan based on user goals."""
    try:
        logger.info(f"Generating plan for user: {req.user_id}, goal: {req.goal}")
        
        # Call Lambda function for planner agent
        question = f"Goal: {req.goal}, Risk Level: {req.risk_level}, Symbols: {req.symbols}"
        result = await invoke_llm_agent_lambda(
            agent_type="planner",
            question=question,
            context={"goal": req.goal, "risk_level": req.risk_level, "symbols": req.symbols}
        )
        
        # Extract plan from Lambda response
        plan_json = extract_lambda_response(result)
            
        return {"plan": plan_json}
    except Exception as e:
        logger.error(f"Error generating plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate plan: {str(e)}")


@app.get(f"{settings.api_prefix}/market/{{symbol}}")
async def market(symbol: str):
    """Fetch market data and technical indicators for a symbol."""
    try:
        logger.info(f"Fetching market data for: {symbol}")
        
        # Get latest price using market data provider (Alpha Vantage)
        latest_data = md.get_latest_price(symbol)
        
        if not latest_data:
            logger.warning(f"No latest data available for {symbol}, trying full history")
            # Fallback to full history method
            df = md.add_indicators(md.candles(symbol))
            if df.empty:
                logger.warning(f"No data available for {symbol}")
                raise HTTPException(status_code=404, detail=f"No market data available for {symbol}")
            latest_data = df.iloc[-1].to_dict()
            sample_data = df.tail(100).to_dict(orient="records")
        else:
            # For sample historical data, fetch full dataset with indicators
            df = md.add_indicators(md.candles(symbol, period="1mo"))
            if not df.empty:
                sample_data = df.tail(100).to_dict(orient="records")
                
                # Add indicators to latest data by calculating on recent sample
                if len(df) >= 50:
                    latest_with_indicators = df.iloc[-1].to_dict()
                    latest_data['rsi'] = latest_with_indicators.get('rsi', 50.0)
                    latest_data['ema20'] = latest_with_indicators.get('ema20', latest_data['close'])
                    latest_data['ema50'] = latest_with_indicators.get('ema50', latest_data['close'])
                else:
                    latest_data['rsi'] = 50.0
                    latest_data['ema20'] = latest_data['close']
                    latest_data['ema50'] = latest_data['close']
            else:
                sample_data = []
        
        logger.info(f"✓ Returning market data for {symbol}: ${latest_data.get('close', 0):.2f}")
        return {"latest": latest_data, "sample": sample_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch market data: {str(e)}")


@app.post(f"{settings.api_prefix}/coach")
async def coach(req: CoachQueryRequest):
    """Ask the coach for educational guidance and Q&A."""
    try:
        logger.info(f"Coach query: {req.user_query}")
        
        # Call Lambda function for coach agent
        result = await invoke_llm_agent_lambda(
            agent_type="coach",
            question=req.user_query,
            context={
                "user_level": req.user_level,
                "focus_area": req.focus_area
            }
        )
        
        # Extract answer from Lambda response
        answer = extract_lambda_response(result)
        
        return {
            "answer": answer,
            "lesson": answer,  # Backward compatibility
            "message": answer  # Backward compatibility
        }
    except Exception as e:
        logger.error(f"Error processing coach request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process coach request: {str(e)}")


@app.post(f"{settings.api_prefix}/critique")
async def critique(req: CritiqueRequest):
    """Get critique and feedback on a proposed trade."""
    try:
        logger.info(f"Critique request for {req.symbol} - {req.action}")
        df = md.add_indicators(md.candles(req.symbol))
        last = df.iloc[-1]
        indicators = {
            "close": float(last["close"]),
            "rsi": float(last["rsi"]),
            "ema20": float(last["ema20"]),
            "ema50": float(last["ema50"])
        }
        
        # Call Lambda function for critic agent
        question = f"Evaluate {req.action} trade for {req.symbol}. Reason: {req.reason}"
        result = await invoke_llm_agent_lambda(
            agent_type="critic",
            question=question,
            context={
                "symbol": req.symbol,
                "action": req.action,
                "reason": req.reason,
                "indicators": indicators
            }
        )
        
        # Extract judgment from Lambda response
        judgment = extract_lambda_response(result)
            
        return {"indicators": indicators, "judgment": judgment}
    except Exception as e:
        logger.error(f"Error processing critique: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process critique: {str(e)}")


@app.post(f"{settings.api_prefix}/paper_trade")
async def paper_trade(t: TradeInput):
    """Execute a simulated paper trade."""
    try:
        logger.info(f"Paper trade: {t.user_id} - {t.side} {t.quantity} {t.symbol}")
        user = load_user(t.user_id)
        if not user:
            raise HTTPException(404, "user not found; call /api/init first")
        
        df = md.candles(t.symbol)
        price = float(df.iloc[-1]["close"])  # latest close as mock fill price
        
        state = PortfolioState(**user)
        state = execute_trade(state, t.symbol, t.side, t.quantity, price, datetime.utcnow().isoformat())
        save_user(t.user_id, state.model_dump())
        
        return {"state": state, "fill_price": price}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing paper trade: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute paper trade: {str(e)}")


@app.get(f"{settings.api_prefix}/portfolio/{{user_id}}")
async def get_portfolio(user_id: str):
    """Get portfolio state for a user including positions, cash, history, and metrics."""
    try:
        logger.info(f"Fetching portfolio for user: {user_id}")
        user = load_user(user_id)
        if not user:
            raise HTTPException(404, "user not found; call /api/init first")
        
        state = PortfolioState(**user)
        
        # Calculate portfolio metrics
        total_value = state.cash
        positions_value = 0.0
        positions_data = []
        
        for pos in state.positions:
            # Get current market price
            try:
                df = md.candles(pos.symbol)
                current_price = float(df.iloc[-1]["close"])
                position_value = pos.quantity * current_price
                pnl = (current_price - pos.avg_price) * pos.quantity
                pnl_percent = ((current_price - pos.avg_price) / pos.avg_price) * 100
                
                positions_value += position_value
                positions_data.append({
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "avg_price": pos.avg_price,
                    "current_price": current_price,
                    "value": position_value,
                    "pnl": pnl,
                    "pnl_percent": pnl_percent
                })
            except Exception as e:
                logger.warning(f"Failed to get current price for {pos.symbol}: {e}")
                # Use avg_price as fallback
                position_value = pos.quantity * pos.avg_price
                positions_value += position_value
                positions_data.append({
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "avg_price": pos.avg_price,
                    "current_price": pos.avg_price,
                    "value": position_value,
                    "pnl": 0,
                    "pnl_percent": 0
                })
        
        total_value += positions_value
        
        # Calculate trade statistics
        total_trades = len(state.history)
        winning_trades = 0
        losing_trades = 0
        total_pnl = 0.0
        
        # Track buy/sell pairs for win/loss calculation
        position_tracker = {}
        for trade in state.history:
            if trade.side == "buy":
                if trade.symbol not in position_tracker:
                    position_tracker[trade.symbol] = []
                position_tracker[trade.symbol].append({
                    "price": trade.price,
                    "quantity": trade.quantity
                })
            elif trade.side == "sell":
                if trade.symbol in position_tracker and position_tracker[trade.symbol]:
                    buy_data = position_tracker[trade.symbol].pop(0)
                    pnl = (trade.price - buy_data["price"]) * min(trade.quantity, buy_data["quantity"])
                    total_pnl += pnl
                    if pnl > 0:
                        winning_trades += 1
                    elif pnl < 0:
                        losing_trades += 1
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        metrics = {
            "total_value": total_value,
            "cash": state.cash,
            "positions_value": positions_value,
            "total_pnl": total_pnl,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate
        }
        
        return {
            "state": state,
            "positions": positions_data,
            "metrics": metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch portfolio: {str(e)}")


@app.post(f"{settings.api_prefix}/trade-analysis")
async def trade_analysis(req: TradeAnalysisRequest):
    """
    Coordinated agentic workflow for trade analysis.
    1. User presents trade idea
    2. Planner agent analyzes market data & technical indicators (runs in parallel with critic prep)
    3. Critic agent evaluates the plan & provides recommendations
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    try:
        logger.info(f"Trade analysis requested for: {req.idea}")
        
        # Step 1: Extract symbol from idea (basic extraction)
        idea_upper = req.idea.upper()
        symbols_to_check = ['BTC', 'ETH', 'AAPL', 'TSLA', 'NVDA', 'GOOGL', 'MSFT', 'AMZN', 'META']
        detected_symbol = None
        
        for sym in symbols_to_check:
            if sym in idea_upper:
                detected_symbol = sym if sym not in ['BTC', 'ETH'] else f"{sym}-USD"
                break
        
        # Step 2: Fetch market data if symbol detected
        market_context = {}
        if detected_symbol:
            try:
                df = md.add_indicators(md.candles(detected_symbol, period="1mo"))
                if not df.empty:
                    latest = df.iloc[-1]
                    market_context = {
                        "symbol": detected_symbol,
                        "price": float(latest['close']),
                        "rsi": float(latest.get('rsi', 50.0)),
                        "ema20": float(latest.get('ema20', latest['close'])),
                        "ema50": float(latest.get('ema50', latest['close'])),
                        "volume": float(latest.get('volume', 0))
                    }
                    logger.info(f"Market context for {detected_symbol}: ${market_context['price']:.2f}")
            except Exception as e:
                logger.warning(f"Could not fetch market data for {detected_symbol}: {e}")
        
        # Step 3: Prepare planner context
        planner_context = f"User's trade idea: {req.idea}\n\n"
        if market_context:
            planner_context += f"Current Market Data for {market_context['symbol']}:\n"
            planner_context += f"- Price: ${market_context['price']:.2f}\n"
            planner_context += f"- RSI: {market_context['rsi']:.1f}\n"
            planner_context += f"- EMA20: ${market_context['ema20']:.2f}\n"
            planner_context += f"- EMA50: ${market_context['ema50']:.2f}\n\n"
        
        planner_context += "Analyze this trade idea considering:\n1. Current market conditions\n2. Technical indicators\n3. Risk/reward ratio\n4. Entry and exit points"
        
        # Extract action from user's idea
        action = "buy" if "buy" in req.idea.lower() else "sell" if "sell" in req.idea.lower() else "hold"
        
        # Step 4: Call Lambda functions for Planner and Critic analysis
        # Using deployed Lambda jbac-llm-agents instead of local agents
        
        # Run Planner analysis
        planner_question = planner_context
        planner_result = await invoke_llm_agent_lambda(
            agent_type="planner",
            question=planner_question,
            context={
                "goal": planner_context,
                "risk_level": "moderate",
                "symbols": [detected_symbol] if detected_symbol else [],
                "market_data": market_context
            }
        )
        
        # Extract planner analysis from Lambda response
        planner_analysis = extract_lambda_response(planner_result)
            
        logger.info(f"Planner completed analysis for {detected_symbol or 'unknown symbol'}")
        
        # Run Critic evaluation
        critic_question = f"Evaluate {action} trade for {detected_symbol or 'UNKNOWN'}. Reason: {req.idea}"
        critic_result = await invoke_llm_agent_lambda(
            agent_type="critic",
            question=critic_question,
            context={
                "symbol": detected_symbol or "UNKNOWN",
                "action": action,
                "reason": req.idea,
                "indicators": market_context if market_context else {},
                "planner_analysis": planner_analysis,
                "market_data": market_context
            }
        )
        
        # Extract critic evaluation from Lambda response  
        critic_evaluation = extract_lambda_response(critic_result)
            
        logger.info(f"Critic completed evaluation for {detected_symbol or 'unknown symbol'}")
        
        # Step 5: Synthesize final recommendation
        # Extract action from critic's evaluation (HOLD, BUY, SELL, WAIT)
        recommendation_action = "HOLD"  # Default
        critic_upper = critic_evaluation.upper()
        if "BUY" in critic_upper and "DON'T" not in critic_upper and "NOT" not in critic_upper:
            recommendation_action = "BUY"
        elif "SELL" in critic_upper:
            recommendation_action = "SELL"
        elif "WAIT" in critic_upper:
            recommendation_action = "WAIT"
        elif "HOLD" in critic_upper:
            recommendation_action = "HOLD"
        
        # Format response as readable text for frontend display
        # Clean up the planner response to be more concise
        planner_summary = "The AI has prepared a structured learning curriculum to help you understand this trade decision."
        if "curriculum" in planner_analysis.lower():
            planner_summary = "📚 A detailed learning plan has been created covering trading basics, technical analysis, and risk management specific to this trade idea."
        
        # Format volume properly
        volume_str = "N/A"
        if market_context and market_context.get('volume'):
            try:
                volume_str = f"{market_context.get('volume'):,.0f}"
            except:
                volume_str = str(market_context.get('volume'))
        
        response_text = f"""<div style="line-height: 1.6;">
<p><strong style="font-size: 1.1em; color: #2196F3;">{recommendation_action} - {detected_symbol or 'UNKNOWN'}</strong></p>

<p><strong>💡 Quick Summary:</strong><br>
{critic_evaluation}</p>

<p><strong>📊 Market Snapshot:</strong><br>
• Price: ${market_context.get('price', 'N/A') if market_context else 'N/A'}<br>
• RSI: {market_context.get('rsi', 'N/A') if market_context else 'N/A'}<br>
• Volume: {volume_str}</p>

<p><strong>📖 Learning Resources:</strong><br>
{planner_summary}</p>

<p><em>💡 Tip: Always paper trade first to practice these concepts!</em></p>
</div>"""
        
        logger.info(f"✓ Trade analysis synthesized for: {req.idea}")
        logger.info(f"  - Recommendation: {recommendation_action}")
        logger.info(f"  - Response length: {len(response_text)} chars")
        
        return {
            "response": response_text,
            "recommendation": recommendation_action,  # Simple string: BUY, SELL, HOLD, WAIT
            "symbol": detected_symbol,
            "market_data": market_context if market_context else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in trade analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze trade: {str(e)}")


# Root redirect
@app.get("/")
async def root():
    """Redirect to API docs."""
    return {
        "message": "JBAC AI Trading Coach API",
        "version": settings.app_version,
        "docs": f"{settings.api_prefix}/docs",
        "health": f"{settings.api_prefix}/health"
    }
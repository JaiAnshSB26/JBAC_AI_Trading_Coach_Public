"""
backend.services.portfolio_sim

Simple, deterministic paper trading simulator used by the API `paper_trade`
endpoint. Keeps computations explicit and raises exceptions for common error
conditions (insufficient cash/shares). This is intentionally minimal and
serves as a teaching/demo simulator rather than a production execution engine.
"""

from .market_data import candles
from ..domain import PortfolioState, Trade, Position

def ensure_position(positions, symbol):
    for p in positions:
        if p.symbol == symbol:
            return p
    new_p = Position(symbol=symbol, quantity=0.0, avg_price=0.0)
    positions.append(new_p)
    return new_p

def execute_trade(state: PortfolioState, symbol: str, side: str, quantity: float, price: float, time: str) -> PortfolioState:
    state = PortfolioState(**state.model_dump())
    if side == "buy":
        cost = quantity * price
        if state.cash < cost:
            raise ValueError("Insufficient cash")
        state.cash -= cost
        pos = ensure_position(state.positions, symbol)
        new_qty = pos.quantity + quantity
        pos.avg_price = (pos.avg_price * pos.quantity + price * quantity) / max(new_qty, 1e-9)
        pos.quantity = new_qty
    else:
        pos = ensure_position(state.positions, symbol)
        if pos.quantity < quantity:
            raise ValueError("Insufficient shares")
        state.cash += quantity * price
        pos.quantity -= quantity
        if pos.quantity == 0:
            pos.avg_price = 0.0
    state.history.append(Trade(symbol=symbol, side=side, quantity=quantity, price=price, time=time))
    return state
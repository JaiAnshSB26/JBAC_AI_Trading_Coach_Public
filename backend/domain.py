"""
backend.domain

Pydantic-based domain models used across the backend and UI.

This module declares the canonical data shapes for trades, positions,
portfolio state, lessons, and request DTOs used by API handlers and agents.
Keeping these models in one place makes validation, serialization, and
documentation straightforward.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class Trade(BaseModel):
    symbol: str
    side: str # "buy" or "sell"
    quantity: float
    price: float
    time: str


class Position(BaseModel):
    symbol: str
    quantity: float
    avg_price: float


class PortfolioState(BaseModel):
    cash: float
    positions: List[Position] = []
    history: List[Trade] = []


class Lesson(BaseModel):
    id: str
    title: str
    content: str
    quiz: Optional[List[str]] = None


class CoachRequest(BaseModel):
    user_id: str
    goal: str # e.g., "Teach me options with $500"
    risk_level: str = "medium"
    symbols: List[str] = ["AAPL", "MSFT", "TSLA"]


class CritiqueRequest(BaseModel):
    user_id: str
    symbol: str
    action: str # e.g., "buy"
    reason: str
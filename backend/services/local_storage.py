"""
Local File Storage Service for Development
Simple JSON-based storage when DynamoDB is not available
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class LocalStorageService:
    """Simple file-based storage for development"""
    
    def __init__(self, data_dir: str = None):
        """Initialize local storage directory"""
        # Use /tmp for Lambda (read-only filesystem), .data for local dev
        if data_dir is None:
            data_dir = "/tmp" if os.getenv("AWS_EXECUTION_ENV") else ".data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.users_file = self.data_dir / 'users.json'
        self.portfolios_file = self.data_dir / 'portfolios.json'
        self.trades_file = self.data_dir / 'trades.json'
        
        # Initialize files if they don't exist
        for file in [self.users_file, self.portfolios_file, self.trades_file]:
            if not file.exists():
                file.write_text('{}')
        
        logger.info(f"Local storage initialized at: {self.data_dir}")
    
    def _read_json(self, file_path: Path) -> Dict:
        """Read JSON file"""
        try:
            return json.loads(file_path.read_text())
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return {}
    
    def _write_json(self, file_path: Path, data: Dict):
        """Write JSON file"""
        try:
            file_path.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.error(f"Error writing {file_path}: {e}")
    
    # =========================
    # USER OPERATIONS
    # =========================
    
    def create_user(self, email: str, display_name: str, 
                   password_hash: Optional[str] = None,
                   oauth_provider: Optional[str] = None,
                   oauth_id: Optional[str] = None) -> Dict:
        """Create a new user"""
        users = self._read_json(self.users_file)
        
        user_id = str(uuid.uuid4())
        user = {
            'user_id': user_id,
            'email': email,
            'display_name': display_name,
            'password_hash': password_hash,
            'oauth_provider': oauth_provider,
            'oauth_id': oauth_id,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'preferences': {},
            'default_portfolio_id': None
        }
        
        users[user_id] = user
        self._write_json(self.users_file, users)
        
        logger.info(f"User created: {email}")
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        users = self._read_json(self.users_file)
        return users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        users = self._read_json(self.users_file)
        for user in users.values():
            if user.get('email') == email:
                return user
        return None
    
    def get_user_by_oauth(self, provider: str, oauth_id: str) -> Optional[Dict]:
        """Get user by OAuth provider and ID"""
        users = self._read_json(self.users_file)
        for user in users.values():
            if (user.get('oauth_provider') == provider and 
                user.get('oauth_id') == oauth_id):
                return user
        return None
    
    def update_user(self, user_id: str, updates: Dict) -> Optional[Dict]:
        """Update user"""
        users = self._read_json(self.users_file)
        if user_id in users:
            users[user_id].update(updates)
            users[user_id]['updated_at'] = datetime.utcnow().isoformat()
            self._write_json(self.users_file, users)
            return users[user_id]
        return None
    
    def update_default_portfolio(self, user_id: str, portfolio_id: Optional[str]) -> bool:
        """Update user's default portfolio"""
        return self.update_user(user_id, {'default_portfolio_id': portfolio_id}) is not None
    
    # =========================
    # PORTFOLIO OPERATIONS
    # =========================
    
    def create_portfolio(self, user_id: str, portfolio_name: str,
                        initial_value: float = 10000.0,
                        tracked_symbols: Optional[List[str]] = None) -> Dict:
        """Create a new portfolio"""
        portfolios = self._read_json(self.portfolios_file)
        
        portfolio_id = str(uuid.uuid4())
        portfolio = {
            'portfolio_id': portfolio_id,
            'user_id': user_id,
            'portfolio_name': portfolio_name,
            'initial_value': initial_value,
            'current_balance': initial_value,
            'total_value': initial_value,
            'positions': [],
            'tracked_symbols': tracked_symbols or [],
            'is_active': True,
            'created_at': datetime.utcnow().isoformat()
        }
        
        portfolios[portfolio_id] = portfolio
        self._write_json(self.portfolios_file, portfolios)
        
        logger.info(f"Portfolio created: {portfolio_name}")
        return portfolio
    
    def get_portfolio(self, portfolio_id: str) -> Optional[Dict]:
        """Get portfolio by ID"""
        portfolios = self._read_json(self.portfolios_file)
        return portfolios.get(portfolio_id)
    
    def get_user_portfolios(self, user_id: str) -> List[Dict]:
        """Get all portfolios for a user"""
        portfolios = self._read_json(self.portfolios_file)
        return [p for p in portfolios.values() if p.get('user_id') == user_id and p.get('is_active', True)]
    
    def health_check(self) -> Dict:
        """Health check"""
        return {
            'status': 'healthy',
            'storage': 'local_file',
            'users_count': len(self._read_json(self.users_file)),
            'portfolios_count': len(self._read_json(self.portfolios_file))
        }
    
    # Stub methods for compatibility
    def delete_portfolio(self, portfolio_id: str) -> bool:
        portfolios = self._read_json(self.portfolios_file)
        if portfolio_id in portfolios:
            portfolios[portfolio_id]['is_active'] = False
            self._write_json(self.portfolios_file, portfolios)
            return True
        return False
    
    def add_tracked_symbol(self, portfolio_id: str, symbol: str) -> Optional[Dict]:
        portfolios = self._read_json(self.portfolios_file)
        if portfolio_id in portfolios:
            symbols = portfolios[portfolio_id].get('tracked_symbols', [])
            if symbol not in symbols:
                symbols.append(symbol)
                portfolios[portfolio_id]['tracked_symbols'] = symbols
                self._write_json(self.portfolios_file, portfolios)
            return portfolios[portfolio_id]
        return None
    
    def remove_tracked_symbol(self, portfolio_id: str, symbol: str) -> Optional[Dict]:
        portfolios = self._read_json(self.portfolios_file)
        if portfolio_id in portfolios:
            symbols = portfolios[portfolio_id].get('tracked_symbols', [])
            if symbol in symbols:
                symbols.remove(symbol)
                portfolios[portfolio_id]['tracked_symbols'] = symbols
                self._write_json(self.portfolios_file, portfolios)
            return portfolios[portfolio_id]
        return None
    
    def execute_trade(self, portfolio_id: str, symbol: str, side: str,
                     quantity: float, price: float, trade_type: str = 'market') -> Dict:
        """Execute a trade (simplified)"""
        portfolios = self._read_json(self.portfolios_file)
        trades = self._read_json(self.trades_file)
        
        if portfolio_id not in portfolios:
            raise ValueError("Portfolio not found")
        
        trade_id = str(uuid.uuid4())
        trade = {
            'trade_id': trade_id,
            'portfolio_id': portfolio_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'trade_type': trade_type,
            'status': 'filled',
            'executed_at': datetime.utcnow().isoformat()
        }
        
        trades[trade_id] = trade
        self._write_json(self.trades_file, trades)
        
        # Update portfolio (simplified)
        portfolio = portfolios[portfolio_id]
        cost = quantity * price
        
        if side == 'buy':
            portfolio['current_balance'] -= cost
        else:
            portfolio['current_balance'] += cost
        
        self._write_json(self.portfolios_file, portfolios)
        
        return trade
    
    def get_portfolio_trades(self, portfolio_id: str, symbol: Optional[str] = None,
                            limit: int = 50) -> List[Dict]:
        """Get trades for a portfolio"""
        trades = self._read_json(self.trades_file)
        result = [t for t in trades.values() if t.get('portfolio_id') == portfolio_id]
        
        if symbol:
            result = [t for t in result if t.get('symbol') == symbol]
        
        return sorted(result, key=lambda x: x.get('executed_at', ''), reverse=True)[:limit]


# Singleton instance
_local_storage_instance = None


def get_local_storage() -> LocalStorageService:
    """Get or create LocalStorageService singleton"""
    global _local_storage_instance
    if _local_storage_instance is None:
        _local_storage_instance = LocalStorageService()
    return _local_storage_instance

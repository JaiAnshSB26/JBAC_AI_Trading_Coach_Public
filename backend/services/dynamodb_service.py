"""
DynamoDB Service for JBAC AI Trading Coach
Handles all database operations for Users, Portfolios, and Trades tables
"""

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from decimal import Decimal
from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)  # Force override system env vars

logger = logging.getLogger(__name__)


class DynamoDBService:
    """Service class for DynamoDB operations"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize DynamoDB client and table references"""
        # Get AWS credentials from environment variables
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_session_token = os.getenv('AWS_SESSION_TOKEN')  # For AWS Academy
        
        # DEBUG: Log what credentials we're using (first 15 chars only)
        logger.info(f"[DYNAMO DEBUG] Access Key: {aws_access_key_id[:15] if aws_access_key_id else 'None'}...")
        logger.info(f"[DYNAMO DEBUG] Secret Key: {aws_secret_access_key[:15] if aws_secret_access_key else 'None'}...")
        logger.info(f"[DYNAMO DEBUG] Session Token: {'Present' if aws_session_token else 'None'}")
        
        # Initialize boto3 with explicit credentials if available
        if aws_access_key_id and aws_secret_access_key:
            if aws_session_token:
                # AWS Academy/Learner Lab
                self.dynamodb = boto3.resource(
                    'dynamodb',
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    aws_session_token=aws_session_token
                )
                logger.info("DynamoDB initialized with session token (AWS Academy)")
            else:
                # Regular AWS account
                self.dynamodb = boto3.resource(
                    'dynamodb',
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
                logger.info("DynamoDB initialized with access key")
        else:
            # Fall back to default credential chain
            self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
            logger.info("DynamoDB initialized with default credentials")
        
        self.users_table = self.dynamodb.Table('Users')
        self.portfolios_table = self.dynamodb.Table('Portfolios')
        self.trades_table = self.dynamodb.Table('Trades')
    
    # =========================
    # UTILITY METHODS
    # =========================
    
    @staticmethod
    def decimal_to_float(obj: Any) -> Any:
        """Convert Decimal objects to float for JSON serialization"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: DynamoDBService.decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DynamoDBService.decimal_to_float(i) for i in obj]
        return obj
    
    @staticmethod
    def float_to_decimal(obj: Any) -> Any:
        """Convert float to Decimal for DynamoDB storage"""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: DynamoDBService.float_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DynamoDBService.float_to_decimal(i) for i in obj]
        return obj
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate a new UUID string"""
        return str(uuid.uuid4())
    
    @staticmethod
    def get_timestamp() -> str:
        """Get current ISO 8601 timestamp"""
        return datetime.utcnow().isoformat() + 'Z'
    
    # =========================
    # USER OPERATIONS
    # =========================
    
    def create_user(
        self,
        email: str,
        display_name: str,
        password_hash: Optional[str] = None,
        oauth_provider: Optional[str] = None,
        oauth_id: Optional[str] = None,
        preferences: Optional[Dict] = None
    ) -> Dict:
        """
        Create a new user
        
        Args:
            email: User's email address
            display_name: User's display name
            password_hash: bcrypt password hash (for email/password auth)
            oauth_provider: OAuth provider name (e.g., 'google')
            oauth_id: OAuth provider's user ID
            preferences: User preferences dict
        
        Returns:
            Created user dict
        """
        user_id = self.generate_uuid()
        
        user_item = {
            'user_id': user_id,
            'email': email,
            'display_name': display_name,
            'password_hash': password_hash,
            'oauth_provider': oauth_provider,
            'oauth_id': oauth_id,
            'default_portfolio_id': None,
            'preferences': preferences or {},
            'is_active': True
        }
        
        try:
            self.users_table.put_item(
                Item=user_item,
                ConditionExpression='attribute_not_exists(user_id)'
            )
            logger.info(f"User created: {user_id}")
            return user_item
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError("User already exists")
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by user_id"""
        try:
            response = self.users_table.get_item(Key={'user_id': user_id})
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email using GSI"""
        try:
            response = self.users_table.query(
                IndexName='email-index',
                KeyConditionExpression=Key('email').eq(email)
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except ClientError as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    def get_user_by_oauth(self, oauth_provider: str, oauth_id: str) -> Optional[Dict]:
        """Get user by OAuth provider and ID"""
        try:
            response = self.users_table.scan(
                FilterExpression=Attr('oauth_provider').eq(oauth_provider) & Attr('oauth_id').eq(oauth_id)
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except ClientError as e:
            logger.error(f"Error getting user by OAuth: {e}")
            return None
    
    def update_user(self, user_id: str, updates: Dict) -> Dict:
        """
        Update user attributes
        
        Args:
            user_id: User ID
            updates: Dict of attributes to update
        
        Returns:
            Updated user dict
        """
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        for key, value in updates.items():
            if key not in ['user_id']:  # Don't update primary key
                placeholder = f"#{key}"
                value_placeholder = f":{key}"
                update_expression_parts.append(f"{placeholder} = {value_placeholder}")
                expression_attribute_names[placeholder] = key
                expression_attribute_values[value_placeholder] = value
        
        if not update_expression_parts:
            raise ValueError("No valid fields to update")
        
        update_expression = "SET " + ", ".join(update_expression_parts)
        
        try:
            response = self.users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues='ALL_NEW'
            )
            logger.info(f"User updated: {user_id}")
            return response['Attributes']
        except ClientError as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    def update_default_portfolio(self, user_id: str, portfolio_id: Optional[str]) -> Dict:
        """Update user's default portfolio"""
        return self.update_user(user_id, {'default_portfolio_id': portfolio_id})
    
    def update_user_preferences(self, user_id: str, preferences: Dict) -> Dict:
        """Update user preferences"""
        return self.update_user(user_id, {'preferences': preferences})
    
    def deactivate_user(self, user_id: str) -> Dict:
        """Soft delete user by setting is_active to False"""
        return self.update_user(user_id, {'is_active': False})
    
    # =========================
    # PORTFOLIO OPERATIONS
    # =========================
    
    def create_portfolio(
        self,
        user_id: str,
        portfolio_name: str,
        initial_value: float,
        tracked_symbols: Optional[List[str]] = None
    ) -> Dict:
        """
        Create a new portfolio
        
        Args:
            user_id: Owner's user ID
            portfolio_name: Portfolio name
            initial_value: Starting cash balance
            tracked_symbols: List of symbols to track
        
        Returns:
            Created portfolio dict
        """
        portfolio_id = self.generate_uuid()
        
        portfolio_item = self.float_to_decimal({
            'portfolio_id': portfolio_id,
            'user_id': user_id,
            'portfolio_name': portfolio_name,
            'initial_value': initial_value,
            'current_balance': initial_value,
            'positions': [],
            'total_value': initial_value,
            'total_invested': 0.0,
            'total_pnl': 0.0,
            'pnl_percent': 0.0,
            'tracked_symbols': tracked_symbols or [],
            'is_active': True
        })
        
        try:
            self.portfolios_table.put_item(Item=portfolio_item)
            logger.info(f"Portfolio created: {portfolio_id}")
            return self.decimal_to_float(portfolio_item)
        except ClientError as e:
            logger.error(f"Error creating portfolio: {e}")
            raise
    
    def get_portfolio(self, portfolio_id: str) -> Optional[Dict]:
        """Get portfolio by ID"""
        try:
            response = self.portfolios_table.get_item(Key={'portfolio_id': portfolio_id})
            item = response.get('Item')
            return self.decimal_to_float(item) if item else None
        except ClientError as e:
            logger.error(f"Error getting portfolio {portfolio_id}: {e}")
            return None
    
    def get_user_portfolios(self, user_id: str, active_only: bool = True) -> List[Dict]:
        """
        Get all portfolios for a user
        
        Args:
            user_id: User ID
            active_only: If True, only return active portfolios
        
        Returns:
            List of portfolio dicts
        """
        try:
            response = self.portfolios_table.query(
                IndexName='user-index',
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            
            portfolios = response.get('Items', [])
            
            if active_only:
                portfolios = [p for p in portfolios if p.get('is_active', True)]
            
            return [self.decimal_to_float(p) for p in portfolios]
        except ClientError as e:
            logger.error(f"Error getting portfolios for user {user_id}: {e}")
            return []
    
    def update_portfolio(self, portfolio_id: str, updates: Dict) -> Dict:
        """
        Update portfolio attributes
        
        Args:
            portfolio_id: Portfolio ID
            updates: Dict of attributes to update
        
        Returns:
            Updated portfolio dict
        """
        updates = self.float_to_decimal(updates)
        
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        for key, value in updates.items():
            if key not in ['portfolio_id']:  # Don't update primary key
                placeholder = f"#{key}"
                value_placeholder = f":{key}"
                update_expression_parts.append(f"{placeholder} = {value_placeholder}")
                expression_attribute_names[placeholder] = key
                expression_attribute_values[value_placeholder] = value
        
        if not update_expression_parts:
            raise ValueError("No valid fields to update")
        
        update_expression = "SET " + ", ".join(update_expression_parts)
        
        try:
            response = self.portfolios_table.update_item(
                Key={'portfolio_id': portfolio_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues='ALL_NEW'
            )
            logger.info(f"Portfolio updated: {portfolio_id}")
            return self.decimal_to_float(response['Attributes'])
        except ClientError as e:
            logger.error(f"Error updating portfolio {portfolio_id}: {e}")
            raise
    
    def add_tracked_symbol(self, portfolio_id: str, symbol: str) -> Dict:
        """Add a symbol to portfolio's tracked symbols"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        tracked_symbols = portfolio.get('tracked_symbols', [])
        if symbol not in tracked_symbols:
            tracked_symbols.append(symbol)
            return self.update_portfolio(portfolio_id, {'tracked_symbols': tracked_symbols})
        
        return portfolio
    
    def remove_tracked_symbol(self, portfolio_id: str, symbol: str) -> Dict:
        """Remove a symbol from portfolio's tracked symbols"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        tracked_symbols = portfolio.get('tracked_symbols', [])
        if symbol in tracked_symbols:
            tracked_symbols.remove(symbol)
            return self.update_portfolio(portfolio_id, {'tracked_symbols': tracked_symbols})
        
        return portfolio
    
    def delete_portfolio(self, portfolio_id: str) -> bool:
        """
        Soft delete portfolio by setting is_active to False
        
        Args:
            portfolio_id: Portfolio ID
        
        Returns:
            True if successful
        """
        try:
            self.update_portfolio(portfolio_id, {'is_active': False})
            logger.info(f"Portfolio deleted: {portfolio_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting portfolio {portfolio_id}: {e}")
            return False
    
    # =========================
    # POSITION MANAGEMENT
    # =========================
    
    def update_position(
        self,
        portfolio_id: str,
        symbol: str,
        quantity: float,
        avg_cost: float,
        current_price: float
    ) -> Dict:
        """
        Update or add a position in the portfolio
        
        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol
            quantity: Number of shares
            avg_cost: Average cost per share
            current_price: Current market price
        
        Returns:
            Updated portfolio dict
        """
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        positions = portfolio.get('positions', [])
        
        # Find existing position
        existing_position = None
        for i, pos in enumerate(positions):
            if pos['symbol'] == symbol:
                existing_position = i
                break
        
        # Calculate position metrics
        current_value = quantity * current_price
        cost_basis = quantity * avg_cost
        unrealized_pnl = current_value - cost_basis
        pnl_percent = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0
        
        new_position = {
            'symbol': symbol,
            'quantity': quantity,
            'avg_cost': avg_cost,
            'current_price': current_price,
            'current_value': current_value,
            'unrealized_pnl': unrealized_pnl,
            'pnl_percent': pnl_percent
        }
        
        if existing_position is not None:
            if quantity <= 0:
                # Remove position if quantity is 0 or negative
                positions.pop(existing_position)
            else:
                positions[existing_position] = new_position
        elif quantity > 0:
            # Add new position
            positions.append(new_position)
        
        # Recalculate portfolio totals
        total_positions_value = sum(p['current_value'] for p in positions)
        total_value = portfolio['current_balance'] + total_positions_value
        total_invested = portfolio['initial_value']
        total_pnl = total_value - total_invested
        pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0
        
        # Update portfolio
        return self.update_portfolio(portfolio_id, {
            'positions': positions,
            'total_value': total_value,
            'total_invested': total_invested,
            'total_pnl': total_pnl,
            'pnl_percent': pnl_percent
        })
    
    def get_position(self, portfolio_id: str, symbol: str) -> Optional[Dict]:
        """Get a specific position from portfolio"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
        
        for position in portfolio.get('positions', []):
            if position['symbol'] == symbol:
                return position
        
        return None
    
    # =========================
    # TRADE OPERATIONS
    # =========================
    
    def execute_trade(
        self,
        portfolio_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        trade_type: str = 'market'
    ) -> Dict:
        """
        Execute a trade and update portfolio
        
        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol
            side: 'buy' or 'sell'
            quantity: Number of shares
            price: Price per share
            trade_type: 'market' or 'limit'
        
        Returns:
            Created trade dict
        
        Raises:
            ValueError: If insufficient balance or shares
        """
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        trade_id = self.generate_uuid()
        timestamp = self.get_timestamp()
        total_amount = quantity * price
        
        # Validate trade
        if side == 'buy':
            if total_amount > portfolio['current_balance']:
                raise ValueError(f"Insufficient balance. Need ${total_amount:.2f}, have ${portfolio['current_balance']:.2f}")
        elif side == 'sell':
            position = self.get_position(portfolio_id, symbol)
            if not position or position['quantity'] < quantity:
                available = position['quantity'] if position else 0
                raise ValueError(f"Insufficient shares. Trying to sell {quantity}, have {available}")
        else:
            raise ValueError(f"Invalid trade side: {side}")
        
        # Calculate new balance
        if side == 'buy':
            new_balance = portfolio['current_balance'] - total_amount
        else:  # sell
            new_balance = portfolio['current_balance'] + total_amount
        
        # Create trade record
        trade_item = self.float_to_decimal({
            'trade_id': trade_id,
            'portfolio_id': portfolio_id,
            'timestamp': timestamp,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'total_amount': total_amount,
            'trade_type': trade_type,
            'balance_before': portfolio['current_balance'],
            'balance_after': new_balance,
            'status': 'completed'
        })
        
        try:
            # Save trade
            self.trades_table.put_item(Item=trade_item)
            logger.info(f"Trade executed: {trade_id}")
            
            # Update portfolio balance
            self.update_portfolio(portfolio_id, {'current_balance': new_balance})
            
            # Update position
            position = self.get_position(portfolio_id, symbol)
            
            if side == 'buy':
                if position:
                    # Update existing position with new average cost
                    old_quantity = position['quantity']
                    old_avg_cost = position['avg_cost']
                    new_quantity = old_quantity + quantity
                    new_avg_cost = ((old_quantity * old_avg_cost) + (quantity * price)) / new_quantity
                    self.update_position(portfolio_id, symbol, new_quantity, new_avg_cost, price)
                else:
                    # Create new position
                    self.update_position(portfolio_id, symbol, quantity, price, price)
            else:  # sell
                # Reduce position
                new_quantity = position['quantity'] - quantity
                self.update_position(portfolio_id, symbol, new_quantity, position['avg_cost'], price)
            
            return self.decimal_to_float(trade_item)
            
        except ClientError as e:
            logger.error(f"Error executing trade: {e}")
            raise
    
    def get_trade(self, trade_id: str) -> Optional[Dict]:
        """Get trade by ID"""
        try:
            response = self.trades_table.query(
                IndexName='trade-index',
                KeyConditionExpression=Key('trade_id').eq(trade_id)
            )
            items = response.get('Items', [])
            return self.decimal_to_float(items[0]) if items else None
        except ClientError as e:
            logger.error(f"Error getting trade {trade_id}: {e}")
            return None
    
    def get_portfolio_trades(
        self,
        portfolio_id: str,
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get trades for a portfolio with optional filters
        
        Args:
            portfolio_id: Portfolio ID
            symbol: Optional symbol filter
            side: Optional side filter ('buy' or 'sell')
            limit: Maximum number of trades to return
        
        Returns:
            List of trade dicts sorted by timestamp (newest first)
        """
        try:
            query_kwargs = {
                'KeyConditionExpression': Key('portfolio_id').eq(portfolio_id),
                'ScanIndexForward': False,  # Sort descending (newest first)
                'Limit': limit
            }
            
            # Add filters if provided
            filter_expressions = []
            if symbol:
                filter_expressions.append(Attr('symbol').eq(symbol))
            if side:
                filter_expressions.append(Attr('side').eq(side))
            
            if filter_expressions:
                filter_expr = filter_expressions[0]
                for expr in filter_expressions[1:]:
                    filter_expr = filter_expr & expr
                query_kwargs['FilterExpression'] = filter_expr
            
            response = self.trades_table.query(**query_kwargs)
            trades = response.get('Items', [])
            
            return [self.decimal_to_float(t) for t in trades]
            
        except ClientError as e:
            logger.error(f"Error getting trades for portfolio {portfolio_id}: {e}")
            return []
    
    def get_user_trades(
        self,
        user_id: str,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get all trades for a user across all their portfolios
        
        Args:
            user_id: User ID
            symbol: Optional symbol filter
            limit: Maximum number of trades per portfolio
        
        Returns:
            List of trade dicts sorted by timestamp
        """
        portfolios = self.get_user_portfolios(user_id)
        all_trades = []
        
        for portfolio in portfolios:
            trades = self.get_portfolio_trades(
                portfolio['portfolio_id'],
                symbol=symbol,
                limit=limit
            )
            all_trades.extend(trades)
        
        # Sort by timestamp descending
        all_trades.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return all_trades[:limit]
    
    # =========================
    # HEALTH CHECK
    # =========================
    
    def health_check(self) -> Dict[str, str]:
        """Check if all tables are accessible"""
        status = {}
        
        try:
            self.users_table.table_status
            status['users'] = 'ok'
        except Exception as e:
            status['users'] = f'error: {str(e)}'
        
        try:
            self.portfolios_table.table_status
            status['portfolios'] = 'ok'
        except Exception as e:
            status['portfolios'] = f'error: {str(e)}'
        
        try:
            self.trades_table.table_status
            status['trades'] = 'ok'
        except Exception as e:
            status['trades'] = f'error: {str(e)}'
        
        return status


# Singleton instance
_db_service_instance = None


def get_db_service() -> DynamoDBService:
    """Get or create DynamoDB service singleton"""
    global _db_service_instance
    if _db_service_instance is None:
        _db_service_instance = DynamoDBService()
    return _db_service_instance

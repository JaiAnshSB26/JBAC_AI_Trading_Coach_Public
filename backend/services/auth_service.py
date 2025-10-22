"""
Authentication Service for JBAC AI Trading Coach
Handles user authentication via Google OAuth and email/password with bcrypt
Manages JWT token generation and validation
"""

import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import os
import logging
from pathlib import Path
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv

# Load environment variables from backend/.env FIRST
# Get the directory where this file is located (backend/services/)
current_dir = Path(__file__).resolve().parent
# Go up one level to backend/
backend_dir = current_dir.parent
# Load .env from backend/ directory
env_path = backend_dir / '.env'
load_dotenv(dotenv_path=env_path, override=True)  # Force override system env vars

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')

# Debug: Print the loaded Client ID and env file path
print(f"[AUTH_SERVICE] Loading .env from: {env_path}")
print(f"[AUTH_SERVICE] .env file exists: {env_path.exists()}")
if GOOGLE_CLIENT_ID:
    print(f"[AUTH_SERVICE] ✓ Google Client ID loaded: {GOOGLE_CLIENT_ID[:20]}...{GOOGLE_CLIENT_ID[-20:]}")
    logger.info(f"Google Client ID loaded successfully")
else:
    print(f"[AUTH_SERVICE] ✗ WARNING: GOOGLE_CLIENT_ID is empty!")
    logger.error("WARNING: GOOGLE_CLIENT_ID is empty! Check your .env file.")



class AuthService:
    """Service class for authentication operations"""
    
    def __init__(self, db_service):
        """
        Initialize authentication service
        
        Args:
            db_service: DynamoDBService instance
        """
        self.db = db_service
    
    # =========================
    # PASSWORD HASHING
    # =========================
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password string
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password: Plain text password
            password_hash: Hashed password
        
        Returns:
            True if password matches, False otherwise
        """
        try:
            password_bytes = password.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    # =========================
    # JWT TOKEN MANAGEMENT
    # =========================
    
    @staticmethod
    def create_access_token(user_id: str, email: str) -> str:
        """
        Create a JWT access token
        
        Args:
            user_id: User ID
            email: User email
        
        Returns:
            JWT token string
        """
        expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': expiration,
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict]:
        """
        Decode and validate a JWT token
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded payload dict or None if invalid
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    @staticmethod
    def extract_token_from_header(authorization: Optional[str]) -> Optional[str]:
        """
        Extract token from Authorization header
        
        Args:
            authorization: Authorization header value (e.g., 'Bearer <token>')
        
        Returns:
            Token string or None
        """
        if not authorization:
            return None
        
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        return parts[1]
    
    # =========================
    # EMAIL/PASSWORD AUTHENTICATION
    # =========================
    
    def register_user(
        self,
        email: str,
        password: str,
        display_name: Optional[str] = None
    ) -> Tuple[Dict, str]:
        """
        Register a new user with email/password
        
        Args:
            email: User email
            password: Plain text password
            display_name: Optional display name (defaults to email username)
        
        Returns:
            Tuple of (user dict, JWT token)
        
        Raises:
            ValueError: If email already exists or validation fails
        """
        # Validate email
        if not email or '@' not in email:
            raise ValueError("Invalid email address")
        
        # Validate password
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        # Check if user already exists
        existing_user = self.db.get_user_by_email(email)
        if existing_user:
            raise ValueError("Email already registered")
        
        # Set display name
        if not display_name:
            display_name = email.split('@')[0]
        
        # Hash password
        password_hash = self.hash_password(password)
        
        # Create user
        user = self.db.create_user(
            email=email,
            display_name=display_name,
            password_hash=password_hash,
            oauth_provider=None,
            oauth_id=None
        )
        
        # Generate token
        token = self.create_access_token(user['user_id'], user['email'])
        
        logger.info(f"User registered: {email}")
        return user, token
    
    def login_user(self, email: str, password: str) -> Tuple[Dict, str]:
        """
        Authenticate user with email/password
        
        Args:
            email: User email
            password: Plain text password
        
        Returns:
            Tuple of (user dict, JWT token)
        
        Raises:
            ValueError: If credentials are invalid
        """
        # Get user
        user = self.db.get_user_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")
        
        # Check if user is active
        if not user.get('is_active', True):
            raise ValueError("Account is deactivated")
        
        # Verify password
        if not user.get('password_hash'):
            raise ValueError("This account uses OAuth authentication. Please login with Google.")
        
        if not self.verify_password(password, user['password_hash']):
            raise ValueError("Invalid email or password")
        
        # Generate token
        token = self.create_access_token(user['user_id'], user['email'])
        
        logger.info(f"User logged in: {email}")
        return user, token
    
    # =========================
    # GOOGLE OAUTH AUTHENTICATION
    # =========================
    
    def authenticate_google(self, id_token_str: str) -> Tuple[Dict, str]:
        """
        Authenticate user with Google OAuth token
        
        Args:
            id_token_str: Google ID token from frontend
        
        Returns:
            Tuple of (user dict, JWT token)
        
        Raises:
            ValueError: If token is invalid or verification fails
        """
        try:
            # Verify Google token with clock skew tolerance (60 seconds)
            # This helps when client/server clocks are slightly out of sync
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                requests.Request(),
                GOOGLE_CLIENT_ID,
                clock_skew_in_seconds=60
            )
            
            # Extract user info
            google_user_id = idinfo['sub']
            email = idinfo['email']
            display_name = idinfo.get('name', email.split('@')[0])
            
            # Check if user exists
            user = self.db.get_user_by_oauth('google', google_user_id)
            
            if not user:
                # Check if email exists with different auth method
                user = self.db.get_user_by_email(email)
                if user:
                    raise ValueError("Email already registered with password authentication")
                
                # Create new user
                user = self.db.create_user(
                    email=email,
                    display_name=display_name,
                    oauth_provider='google',
                    oauth_id=google_user_id
                )
                logger.info(f"New Google user created: {email}")
            else:
                # Check if user is active
                if not user.get('is_active', True):
                    raise ValueError("Account is deactivated")
                logger.info(f"Existing Google user logged in: {email}")
            
            # Generate JWT token
            token = self.create_access_token(user['user_id'], user['email'])
            
            return user, token
            
        except ValueError as e:
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.error(f"Google authentication error: {e}")
            raise ValueError("Invalid Google token")
    
    # =========================
    # TOKEN VALIDATION
    # =========================
    
    def get_current_user(self, authorization: Optional[str]) -> Optional[Dict]:
        """
        Get current user from Authorization header
        
        Args:
            authorization: Authorization header value
        
        Returns:
            User dict or None if invalid
        """
        # Extract token
        token = self.extract_token_from_header(authorization)
        if not token:
            return None
        
        # Decode token
        payload = self.decode_token(token)
        if not payload:
            return None
        
        # Get user
        user_id = payload.get('user_id')
        if not user_id:
            return None
        
        user = self.db.get_user_by_id(user_id)
        if not user or not user.get('is_active', True):
            return None
        
        return user
    
    def require_auth(self, authorization: Optional[str]) -> Dict:
        """
        Require authentication, raise error if not authenticated
        
        Args:
            authorization: Authorization header value
        
        Returns:
            User dict
        
        Raises:
            ValueError: If not authenticated
        """
        user = self.get_current_user(authorization)
        if not user:
            raise ValueError("Authentication required")
        return user
    
    # =========================
    # PASSWORD RESET
    # =========================
    
    def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
        
        Returns:
            True if successful
        
        Raises:
            ValueError: If validation fails
        """
        # Get user
        user = self.db.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Check if user has password (not OAuth)
        if not user.get('password_hash'):
            raise ValueError("Cannot change password for OAuth users")
        
        # Verify old password
        if not self.verify_password(old_password, user['password_hash']):
            raise ValueError("Current password is incorrect")
        
        # Validate new password
        if len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters")
        
        # Hash new password
        new_password_hash = self.hash_password(new_password)
        
        # Update user
        self.db.update_user(user_id, {'password_hash': new_password_hash})
        
        logger.info(f"Password changed for user: {user_id}")
        return True


# Singleton instance
_auth_service_instance = None


def get_auth_service(db_service) -> AuthService:
    """Get or create AuthService singleton"""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService(db_service)
    return _auth_service_instance

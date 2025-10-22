"""
backend.config

Centralized configuration management for the application.

This module loads environment variables from .env file and provides validated
configuration objects for different components (app, auth, models, storage).

Usage:
    from backend.config import settings
    print(settings.app_env)
"""

import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application Settings
    app_env: str = Field(default="development", description="Application environment")
    app_name: str = Field(default="JBAC AI Trading Coach", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=True, description="Debug mode")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_prefix: str = Field(default="/api", description="API route prefix")
    
    # CORS Settings
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:4200,http://localhost:8501",
        description="Comma-separated list of allowed origins"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # Model Settings
    model_provider: str = Field(default="ollama", description="Model provider: ollama or bedrock")
    
    # Ollama Configuration
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama base URL")
    ollama_model: str = Field(default="gemma3:1b", description="Ollama model name")
    
    # AWS Bedrock Configuration
    aws_region: str = Field(default="us-east-1", description="AWS region")
    aws_access_key_id: str = Field(default="", description="AWS Access Key ID")
    aws_secret_access_key: str = Field(default="", description="AWS Secret Access Key")
    bedrock_model_id: str = Field(
        default="anthropic.claude-3-5-sonnet-20240620-v1:0",
        description="Bedrock model ID"
    )
    
    # Data & Storage
    # Use /tmp in Lambda (read-only filesystem), .data for local dev
    data_dir: str = Field(
        default_factory=lambda: "/tmp" if os.getenv("AWS_EXECUTION_ENV") else ".data",
        description="Local data directory"
    )
    s3_bucket_name: str = Field(default="", description="S3 bucket name")
    s3_prefix: str = Field(default="data/", description="S3 object prefix")
    
    # DynamoDB Tables
    dynamodb_table_users: str = Field(default="jbac-users", description="DynamoDB users table")
    dynamodb_table_plans: str = Field(default="jbac-plans", description="DynamoDB plans table")
    dynamodb_table_simulations: str = Field(default="jbac-simulations", description="DynamoDB simulations table")
    
    # Market Data
    market_data_provider: str = Field(default="yfinance", description="Market data provider")
    polygon_api_key: str = Field(default="", description="Polygon.io API key")
    alpha_vantage_key: str = Field(default="", description="Alpha Vantage API key")
    twelvedata_key: str = Field(default="", description="Twelve Data API key")
    
    # Authentication & Security
    jwt_secret: str = Field(
        default="your-secret-key-change-this-in-production",
        description="JWT signing secret"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(default=15, description="Access token expiry (minutes)")
    jwt_refresh_token_expire_days: int = Field(default=7, description="Refresh token expiry (days)")
    
    # Google OAuth2
    google_client_id: str = Field(default="", description="Google OAuth client ID")
    google_client_secret: str = Field(default="", description="Google OAuth client secret")
    google_redirect_uri: str = Field(
        default="http://localhost:3000/auth/callback",
        description="Google OAuth redirect URI"
    )
    
    # Logging & Monitoring
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json or text")
    cloudwatch_log_group: str = Field(default="/aws/jbac-trading-coach", description="CloudWatch log group")
    cloudwatch_log_stream: str = Field(default="backend", description="CloudWatch log stream")
    
    # Rate Limiting & Quotas
    rate_limit_per_user_per_minute: int = Field(default=60, description="Rate limit per user per minute")
    max_tokens_per_user_per_day: int = Field(default=100000, description="Max tokens per user per day")
    
    # Feature Flags
    enable_websockets: bool = Field(default=True, description="Enable WebSocket endpoints")
    enable_admin_endpoints: bool = Field(default=False, description="Enable admin endpoints")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")


# Global settings instance
settings = Settings()


def is_production() -> bool:
    """Check if running in production environment."""
    return settings.app_env.lower() in ("production", "prod")


def is_development() -> bool:
    """Check if running in development environment."""
    return settings.app_env.lower() in ("development", "dev", "local")
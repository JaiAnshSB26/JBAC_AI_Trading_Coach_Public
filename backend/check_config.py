"""
Configuration Validation Script
Run this to check if your .env file is properly configured
"""

import sys
import os

# Add parent directory to path so we can import backend module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings

def check_config():
    """Validate critical configuration settings"""
    print("=" * 60)
    print("JBAC AI Trading Coach - Configuration Check")
    print("=" * 60)
    print()
    
    issues = []
    warnings = []
    
    # Check AWS credentials
    print("🔍 Checking AWS Configuration...")
    if not settings.aws_access_key_id or settings.aws_access_key_id == "your-aws-access-key-id":
        issues.append("❌ AWS_ACCESS_KEY_ID is not set or using placeholder value")
    else:
        print(f"  ✅ AWS_ACCESS_KEY_ID: {settings.aws_access_key_id[:8]}... (masked)")
    
    if not settings.aws_secret_access_key or settings.aws_secret_access_key == "your-aws-secret-access-key":
        issues.append("❌ AWS_SECRET_ACCESS_KEY is not set or using placeholder value")
    else:
        print(f"  ✅ AWS_SECRET_ACCESS_KEY: ****** (masked)")
    
    print(f"  ℹ️  AWS_REGION: {settings.aws_region}")
    print()
    
    # Check JWT configuration
    print("🔍 Checking JWT Configuration...")
    if not settings.jwt_secret or settings.jwt_secret == "your-secret-key-change-this-in-production":
        warnings.append("⚠️  JWT_SECRET is using default insecure value")
        print(f"  ⚠️  JWT_SECRET: Using default (INSECURE for production!)")
    else:
        print(f"  ✅ JWT_SECRET: {settings.jwt_secret[:8]}... (masked)")
    
    print(f"  ℹ️  JWT_ALGORITHM: {settings.jwt_algorithm}")
    print(f"  ℹ️  JWT_ACCESS_TOKEN_EXPIRE_MINUTES: {settings.jwt_access_token_expire_minutes}")
    print()
    
    # Check DynamoDB tables
    print("🔍 Checking DynamoDB Configuration...")
    print(f"  ℹ️  DYNAMODB_TABLE_USERS: {settings.dynamodb_table_users}")
    print(f"  ℹ️  DYNAMODB_TABLE_PLANS: {settings.dynamodb_table_plans}")
    print(f"  ℹ️  DYNAMODB_TABLE_SIMULATIONS: {settings.dynamodb_table_simulations}")
    print()
    
    # Check market data configuration
    print("🔍 Checking Market Data Configuration...")
    print(f"  ℹ️  MARKET_DATA_PROVIDER: {settings.market_data_provider}")
    
    if settings.market_data_provider == "alpha_vantage" or settings.market_data_provider == "alpha-vantage":
        if not settings.alpha_vantage_key:
            warnings.append("⚠️  Using alpha_vantage provider but ALPHA_VANTAGE_KEY not set")
        else:
            print(f"  ✅ ALPHA_VANTAGE_KEY: {settings.alpha_vantage_key[:8]}... (masked)")
    
    if settings.market_data_provider == "twelvedata":
        if not settings.twelvedata_key:
            warnings.append("⚠️  Using twelvedata provider but TWELVEDATA_KEY not set")
        else:
            print(f"  ✅ TWELVEDATA_KEY: {settings.twelvedata_key[:8]}... (masked)")
    print()
    
    # Check application settings
    print("🔍 Checking Application Settings...")
    print(f"  ℹ️  APP_ENV: {settings.app_env}")
    print(f"  ℹ️  APP_NAME: {settings.app_name}")
    print(f"  ℹ️  DEBUG: {settings.debug}")
    print(f"  ℹ️  API_PORT: {settings.api_port}")
    print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if issues:
        print("\n🚨 CRITICAL ISSUES (will cause authentication failures):")
        for issue in issues:
            print(f"  {issue}")
        print("\nTo fix:")
        print("  1. Get AWS credentials from AWS Console → Security Credentials")
        print("  2. Update backend/.env with your actual credentials:")
        print("     AWS_ACCESS_KEY_ID=AKIA...")
        print("     AWS_SECRET_ACCESS_KEY=...")
        print("  3. Restart backend server")
    
    if warnings:
        print("\n⚠️  WARNINGS (should be addressed):")
        for warning in warnings:
            print(f"  {warning}")
        print("\nTo fix JWT secret:")
        print("  1. Run: openssl rand -hex 32")
        print("  2. Set JWT_SECRET in backend/.env")
    
    if not issues and not warnings:
        print("\n✅ All critical configurations are set!")
        print("   Your backend should be ready to run.")
    
    print("\n" + "=" * 60)
    
    # Exit with appropriate code
    if issues:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    try:
        check_config()
    except Exception as e:
        print(f"\n❌ Error checking configuration: {e}")
        print("\nMake sure you have a .env file in the backend/ directory")
        sys.exit(1)

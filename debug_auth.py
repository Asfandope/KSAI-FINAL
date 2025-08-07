#!/usr/bin/env python3
"""
Debug authentication issues
"""

import sys
sys.path.append('/Users/asfandope/ks-ai-final/ks-ai-platform/apps/api')

from app.services.auth import authenticate_user, verify_password, get_password_hash
from app.db.database import get_db
from passlib.context import CryptContext

# Test password hashing
def test_password_hashing():
    print("=== PASSWORD HASHING TEST ===")
    password = "admin123"
    
    # Test with passlib context
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hash1 = pwd_context.hash(password)
    print(f"Generated hash: {hash1}")
    
    # Verify
    verified = pwd_context.verify(password, hash1)
    print(f"Verification result: {verified}")
    
    # Test existing hash from database
    existing_hash = "$2b$12$pKF4hRo0rVPsFpqwcakpcuw1Nu0Qqn6J6arYPdf06NsmsZQkkWxnO"
    verified_existing = pwd_context.verify(password, existing_hash)
    print(f"Existing hash verification: {verified_existing}")
    
    return verified and verified_existing

def test_database_connection():
    print("\n=== DATABASE CONNECTION TEST ===")
    try:
        db = next(get_db())
        print("Database connection successful")
        
        # Test user query
        from app.models.user import User
        user = db.query(User).filter(User.email == "admin@ksai.com").first()
        if user:
            print(f"Found user: {user.email}, role: {user.role}")
            print(f"User password hash: {user.password_hash}")
            
            # Test password verification
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            verified = pwd_context.verify("admin123", user.password_hash)
            print(f"Password verification: {verified}")
            
            return user, verified
        else:
            print("Admin user not found")
            return None, False
            
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, False

def test_authenticate_user():
    print("\n=== AUTHENTICATE_USER TEST ===")
    try:
        db = next(get_db())
        user = authenticate_user(db, "admin@ksai.com", "admin123")
        
        if user:
            print(f"Authentication successful: {user.email}")
            return True
        else:
            print("Authentication failed")
            return False
            
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 DEBUGGING AUTHENTICATION SYSTEM")
    print("=" * 50)
    
    # Run tests
    hash_test = test_password_hashing()
    db_user, db_verified = test_database_connection()
    auth_test = test_authenticate_user()
    
    print(f"\n=== SUMMARY ===")
    print(f"Password hashing: {'✅' if hash_test else '❌'}")
    print(f"Database connection: {'✅' if db_user else '❌'}")
    print(f"Password verification: {'✅' if db_verified else '❌'}")
    print(f"Authentication function: {'✅' if auth_test else '❌'}")
    
    if all([hash_test, db_user, db_verified, auth_test]):
        print("🎉 All authentication components working!")
    else:
        print("❌ Authentication system has issues")
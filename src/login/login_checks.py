from datetime import datetime, timedelta, timezone
from typing import Optional
from .login_setting import *
import jwt
from supabase import create_client, Client
from .auth_models import *
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import os
from supabase import Client
from fastapi import HTTPException, status
import logging
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")  # for docs / clients [web:2][web:7]
logger = logging.getLogger(__name__)  # module-level logger


def get_supabase_client() -> Client:
    logger.debug("Creating Supabase client")
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)  # [web:12]



def create_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "type": token_type,
    }
    logger.debug("Created %s token for sub=%s exp_in=%s", token_type, subject, expires_delta)
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)  # [web:2]




def create_access_and_user_data(user_id: str , supabase:Client) -> TokenResponse:
    access_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # refresh_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_token(
        subject=user_id,
        expires_delta=access_expires,
        token_type="access",
    )
    logger.debug("Fetching user data for user_id=%s", user_id)
    res = supabase.table('users').select('*').eq('id', user_id).execute()

    if not res.data or len(res.data) == 0:
        logger.error("User not found when generating tokens user_id=%s", user_id)
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info("Generated access token and user data for user_id=%s", user_id)

    return TokenResponse(
        user=res.data[0],
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_expires.total_seconds())
    )  # [web:2][web:3][web:8]


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def authenticate_with_supabase(email: str, password: str, supabase: Client) -> str:
    """DEBUG VERSION - Remove in production"""
    print(f"🔍 Authenticating: {email}")
    logger.info("Login attempt for email=%s", email)
    try:
        # 1. Check if user exists (select *)
        res = supabase.table('users').select('*').eq('office_mail', email).execute()
        # print(f"📊 Query result: {res.data}")
        
        if not res.data or len(res.data) == 0:
            print("❌ No user found")
            logger.warning("Login failed: user not found email=%s", email)
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = res.data[0]
        # print(f"👤 User found: \n\n{user}\n\n, hash preview: {user['password'][:20]}...")
        
        # 2. Test hash verification
        stored_hash = user['password']

        is_valid = pwd_context.verify(password, stored_hash)
        # print(f"🔑 Password valid: {is_valid}")
        # print(f"   Input hash: {pwd_context.hash(password)[:20]}...")
        # print(f"   Stored hash: {stored_hash[:20]}...")
        
        if not is_valid:
            logger.warning("Login failed: invalid password email=%s", email)
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        print("✅ Authentication successful")
        logger.info("Login successful for user_id=%s email=%s", user["id"], email)
        return user['id']
        
    except Exception as e:
        print(f"💥 Error: {e}")
        logger.exception("Auth service error for email=%s: %s", email, e)
        raise HTTPException(status_code=502, detail="Auth service unavailable")


def get_current_user_id(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])  # [web:2]
    except jwt.PyJWTError as e:
        logger.warning("JWT decode failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        logger.warning("Invalid token type: %s", payload.get("type"))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    sub = payload.get("sub")
    if not sub:
        logger.warning("Token missing sub claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    logger.debug("Authenticated request for user_id=%s", sub)
    return str(sub)




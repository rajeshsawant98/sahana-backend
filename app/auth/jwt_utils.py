import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from app.utils.logger import get_logger, log_jwt_payload

# Get logger for this module
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Get secret keys from environment
SECRET_KEY = str(os.getenv("JWT_SECRET_KEY", "").strip())
REFRESH_SECRET_KEY = str(os.getenv("JWT_REFRESH_SECRET_KEY", "").strip())

ALGORITHM = "HS256"

# OAuth2PasswordBearer to extract token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Function to generate Access Token
def create_access_token(data: dict, expires_in_minutes: int = 1) -> str:
    expiration_time = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    token = jwt.encode(
        {"data": data, "exp": expiration_time},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return token

# Function to generate Refresh Token
def create_refresh_token(data: dict, expires_in_days: int = 7) -> str:
    expiration_time = datetime.utcnow() + timedelta(days=expires_in_days)
    token = jwt.encode(
        {"data": data, "exp": expiration_time},
        REFRESH_SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    return token

# Function to validate Access Token
def verify_access_token(token: str):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        log_jwt_payload(logger, decoded_token, "ACCESS_TOKEN_VERIFIED")
        if datetime.utcfromtimestamp(decoded_token["exp"]) < datetime.utcnow():
            return None
        return decoded_token
    except jwt.ExpiredSignatureError:
        logger.warning("Access token has expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid access token provided")
        return None

# Function to validate Refresh Token
def verify_refresh_token(token: str):
    try:
        decoded_token = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        log_jwt_payload(logger, decoded_token, "REFRESH_TOKEN_VERIFIED")
        if datetime.utcfromtimestamp(decoded_token["exp"]) < datetime.utcnow():
            return None
        return decoded_token
    except jwt.ExpiredSignatureError:
        logger.warning("Refresh token has expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid refresh token provided")
        return None

# Token Required Dependency
def validate_token(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

# Get Current User from Token
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload.get("data")
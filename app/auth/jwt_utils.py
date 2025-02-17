import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

# Load environment variables
load_dotenv()

# Get secret key from environment
SECRET_KEY = str(os.getenv("JWT_SECRET_KEY", "").strip())

ALGORITHM = "HS256"  # Can be adjusted if you choose a different algorithm in the future

# OAuth2PasswordBearer to extract token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Function to generate JWT token
def create_access_token(data: dict, expires_in_minutes: int = 60) -> str:
    print(f"SECRET_KEY: {SECRET_KEY} - Type: {type(SECRET_KEY)}")
    expiration_time = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    token = jwt.encode(
        {"data": data, "exp": expiration_time},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return token

# Function to validate JWT token
from datetime import datetime

def verify_access_token(token: str):
    try:
        print(f"SECRET_KEY: {SECRET_KEY} - Type: {type(SECRET_KEY)}")
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Convert the "exp" field to a datetime object
        expiration_time = datetime.utcfromtimestamp(decoded_token["exp"])
        if expiration_time < datetime.utcnow():
            return None
        return decoded_token
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Token Required Dependency to protect routes
def validate_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_access_token(token)
        return payload
    except HTTPException as e:
        raise e

# Get Current User from Token
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload.get("data")
    except HTTPException as e:
        raise e
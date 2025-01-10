from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from app.auth.firebase_config import store_user_data, store_user_with_password, verify_user_password, get_user_by_email
from app.auth.jwt_utils import create_access_token, get_current_user  # Import get_current_user from jwt_utils
from fastapi.security import OAuth2PasswordBearer

auth_router = APIRouter()

# Define the data models for incoming requests
class GoogleLoginRequest(BaseModel):
    token: str

class NormalLoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Google Login
@auth_router.post("/google")
async def google_login(request: GoogleLoginRequest):
    try:
        token = request.token
        client_id = "505025857168-olhtcsvr2pmpu84k0gb25rkh61qksbm8.apps.googleusercontent.com"

        id_info = id_token.verify_oauth2_token(token, Request(), client_id)

        user_data = {
            "uid": id_info["sub"],
            "name": id_info.get("name"),
            "email": id_info.get("email"),
            "profile_picture": id_info.get("picture")
        }

        store_user_data(user_data)
        access_token = create_access_token(data={"sub": user_data["email"]})

        return {"message": "User authenticated successfully", "access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=400, detail="Google login failed")

# Normal Login
@auth_router.post("/login")
async def normal_login(request: NormalLoginRequest):
    user = get_user_by_email(request.email)
    if not user or not verify_user_password(request.email, request.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user["email"]})
    return {"message": "User authenticated successfully", "access_token": access_token, "token_type": "bearer"}

@auth_router.post("/register")
async def register_user(request: RegisterRequest):
    if get_user_by_email(request.email):
        raise HTTPException(status_code=400, detail="Email already exists")

    store_user_with_password(request.email, request.password, request.name)
    access_token = create_access_token(data={"sub": request.email})

    
    return {
        "message": "User registered successfully",
        "access_token": access_token,
        "token_type": "bearer"
    }

# Protected route example that requires authentication
@auth_router.get("/me")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return {"message": "User profile retrieved successfully", "user": current_user}
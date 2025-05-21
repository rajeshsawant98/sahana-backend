from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from app.services.user_service import (
    store_or_update_user_data,
    store_user_with_password,
    verify_user_password,
    get_user_by_email,
    update_user_data
)
from app.auth.jwt_utils import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_current_user
)
import os

auth_router = APIRouter()

# -------------------- Models --------------------

class GoogleLoginRequest(BaseModel):
    token: str

class NormalLoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class UpdateProfileRequest(BaseModel):
    name: str
    profession: str
    bio: str
    phoneNumber: str
    location: dict
    birthdate: str

class UpdateInterestsRequest(BaseModel):
    interests: list

class RefreshRequest(BaseModel):
    refresh_token: str

# -------------------- Routes --------------------

# Google Login
@auth_router.post("/google")
async def google_login(request: GoogleLoginRequest):
    try:
        token = request.token
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        id_info = id_token.verify_oauth2_token(token, Request(), client_id)

        user_data = {
            "uid": id_info["sub"],
            "name": id_info.get("name"),
            "email": id_info.get("email"),
            "profile_picture": id_info.get("picture")
        }

        store_or_update_user_data(user_data)

        access_token = create_access_token(data={"email": user_data["email"]})
        refresh_token = create_refresh_token(data={"email": user_data["email"]})

        return {
            "message": "User authenticated successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "email": user_data["email"]
        }
    except Exception:
        raise HTTPException(status_code=400, detail="Google login failed")

# Normal Login
@auth_router.post("/login")
async def normal_login(request: NormalLoginRequest):
    user = get_user_by_email(request.email)
    if not user or not verify_user_password(request.email, request.password):
        raise HTTPException(status_code=400, detail="Invalid credentials") 

    access_token = create_access_token(data={"email": user["email"]})
    refresh_token = create_refresh_token(data={"email": user["email"]})

    return {
        "message": "User authenticated successfully",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "email": user["email"],
        "role": user.get("role", "user")
    }

# Register
@auth_router.post("/register")
async def register_user(request: RegisterRequest):
    if get_user_by_email(request.email):
        raise HTTPException(status_code=400, detail="Email already exists")

    store_user_with_password(request.email, request.password, request.name)

    access_token = create_access_token(data={"email": request.email})
    refresh_token = create_refresh_token(data={"email": request.email})

    return {
        "message": "User registered successfully",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "email": request.email,
        "role": "user"
    }

# Refresh Token
@auth_router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    if not request.refresh_token:
        raise HTTPException(status_code=400, detail="Missing refresh token")

    decoded_data = verify_refresh_token(request.refresh_token)
    if not decoded_data or "data" not in decoded_data or "email" not in decoded_data["data"]:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    new_access_token = create_access_token(data={"email": decoded_data["data"]["email"]})
    return {"access_token": new_access_token, "token_type": "bearer"}

# Get current user profile
@auth_router.get("/me")
async def get_profile(current_user: dict = Depends(get_current_user)):
    user = get_user_by_email(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.pop("password", None)

    return {
        "email": user["email"],
        "name": user["name"],
        "profile_picture": user.get("profile_picture", ""),
        "interests": user.get("interests", []),
        "profession": user.get("profession", ""),
        "bio": user.get("bio", ""),
        "phoneNumber": user.get("phoneNumber", ""),
        "location": user.get("location", {}),
        "birthdate": user.get("birthdate", ""),
        "role": user.get("role", "user")
    }

# Update user profile
@auth_router.put("/me")
async def update_profile(request: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    user = get_user_by_email(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_data = {
        "name": request.name,
        "profession": request.profession,
        "bio": request.bio,
        "phoneNumber": request.phoneNumber,
        "birthdate": request.birthdate,
        "location": {
            **(user.get("location") or {}),
            **request.location
        }
    }

    update_user_data(updated_data, current_user["email"])
    return {"message": "Profile updated successfully"}

# Update user interests
@auth_router.put("/me/interests")
async def update_interests(request: UpdateInterestsRequest, current_user: dict = Depends(get_current_user)):
    user = get_user_by_email(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_user_data({"interests": request.interests}, current_user["email"])
    return {"message": "User interests updated successfully"}
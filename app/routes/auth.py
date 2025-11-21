from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from app.models import (
    UserCreate, 
    UserUpdate, 
    UserResponse, 
    UserLoginRequest, 
    UserLoginResponse,
    GoogleUserCreate,
    Location
)
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
from app.auth.roles import user_only
from app.utils.http_exceptions import HTTPExceptionHelper
import os

auth_router = APIRouter()

# -------------------- Request Models --------------------

class GoogleLoginRequest(BaseModel):
    token: str

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

        await store_or_update_user_data(user_data)
        
        user = await get_user_by_email(user_data["email"])
        if not user:
            raise HTTPExceptionHelper.not_found("User not found")
        role = user.get("role", "user")

        access_token = create_access_token(data={"email": user_data["email"], "role": role})
        # logger.debug(f"access_token: {access_token}")  # Debug log commented out
        refresh_token = create_refresh_token(data={"email": user_data["email"], "role": role})

        return {
            "message": "User authenticated successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except Exception as e:
        print(f"Google authentication error: {e}")
        raise HTTPExceptionHelper.bad_request("Google login failed")

# Normal Login
@auth_router.post("/login", response_model=UserLoginResponse)
async def normal_login(request: UserLoginRequest):
    user = await get_user_by_email(request.email)
    if not user or not await verify_user_password(request.email, request.password):
        raise HTTPExceptionHelper.bad_request("Invalid credentials") 

    access_token = create_access_token(data={"email": user["email"], "role": user.get("role", "user")})
    refresh_token = create_refresh_token(data={"email": user["email"], "role": user.get("role", "user")})

    return UserLoginResponse(
        message="User authenticated successfully",
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        email=user.get("email", "")
    )

# Register
@auth_router.post("/register", response_model=UserLoginResponse)
async def register_user(request: UserCreate):
    if await get_user_by_email(request.email):
        raise HTTPExceptionHelper.bad_request("Email already exists")

    await store_user_with_password(request.email, request.password, request.name)

    # Get the newly created user
    user = await get_user_by_email(request.email)
    if not user:
        raise HTTPExceptionHelper.server_error("Failed to create user")

    access_token = create_access_token(data={"email": request.email, "role": "user"})
    refresh_token = create_refresh_token(data={"email": request.email, "role": "user"})

    # Remove password for security before extracting data
    user.pop("password", None)

    return UserLoginResponse(
        message="User registered successfully",
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        email=request.email
    )

# Refresh Token
@auth_router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    if not request.refresh_token:
        raise HTTPExceptionHelper.bad_request("Missing refresh token")

    decoded_data = verify_refresh_token(request.refresh_token)

    if not decoded_data or "data" not in decoded_data:
        raise HTTPExceptionHelper.unauthorized("Invalid or expired refresh token")

    user_data = decoded_data["data"]
    if "email" not in user_data or "role" not in user_data:
        raise HTTPExceptionHelper.unauthorized("Malformed refresh token")

    # Recreate access token with both email and role
    new_access_token = create_access_token(data={
        "email": user_data["email"],
        "role": user_data["role"]
    })

    return {"access_token": new_access_token,
            "token_type": "bearer",
            "message": "Access token refreshed successfully"}

# Get current user profile
@auth_router.get("/me", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(user_only)):
    user = await get_user_by_email(current_user["email"])
    if not user:
        raise HTTPExceptionHelper.not_found("User not found")

    # Remove password from user data
    user.pop("password", None)
    
    # Convert to UserResponse model
    try:
        return UserResponse(**user)
    except Exception as e:
        # If there are missing fields, provide defaults
        return UserResponse(
            name=user.get("name", ""),
            email=user["email"],
            phoneNumber=user.get("phoneNumber", ""),
            bio=user.get("bio", ""),
            birthdate=user.get("birthdate", ""),
            profession=user.get("profession", ""),
            interests=user.get("interests", []),
            role=user.get("role", "user"),
            profile_picture=user.get("profile_picture", ""),
            location=user.get("location"),
            google_uid=user.get("google_uid"),
            created_at=user.get("created_at"),
            updated_at=user.get("updated_at")
        )

# Update user profile
@auth_router.put("/me", response_model=dict)
async def update_profile(request: UserUpdate, current_user: dict = Depends(user_only)):
    user = await get_user_by_email(current_user["email"])
    if not user:
        raise HTTPExceptionHelper.not_found("User not found")

    # Convert UserUpdate model to dict, excluding None values
    update_data = {}
    for field, value in request.dict(exclude_none=True).items():
        if field == "location" and value:
            # Merge location data with existing location
            existing_location = user.get("location") or {}
            if hasattr(value, 'dict'):
                new_location = value.dict()
            else:
                new_location = value
            update_data["location"] = {**existing_location, **new_location}
        else:
            update_data[field] = value

    await update_user_data(update_data, current_user["email"])
    return {"message": "Profile updated successfully"}

# Update user interests
class UpdateInterestsRequest(BaseModel):
    interests: List[str]

@auth_router.put("/me/interests", response_model=dict)
async def update_interests(request: UpdateInterestsRequest, current_user: dict = Depends(user_only)):
    user = await get_user_by_email(current_user["email"])
    if not user:
        raise HTTPExceptionHelper.not_found("User not found")

    # Validate interests using the validator from UserUpdate
    try:
        # Basic validation - ensure it's a list of strings
        if not isinstance(request.interests, list):
            raise ValueError("Interests must be a list")
        
        # Validate each interest is a non-empty string
        for interest in request.interests:
            if not isinstance(interest, str) or not interest.strip():
                raise ValueError("Each interest must be a non-empty string")
        
        # Remove duplicates and trim whitespace
        cleaned_interests = list(set(interest.strip() for interest in request.interests))
        
        await update_user_data({"interests": cleaned_interests}, current_user["email"])
        return {"message": "User interests updated successfully"}
    except ValueError as e:
        raise HTTPExceptionHelper.bad_request(f"Invalid interests: {str(e)}")
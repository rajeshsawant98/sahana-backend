from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from app.auth.firebase_config import store_or_update_user_data, store_user_data, store_user_with_password, verify_user_password, get_user_by_email
from app.auth.jwt_utils import create_access_token, get_current_user  # Import get_current_user from jwt_utils
from fastapi.security import OAuth2PasswordBearer
from app.services.event_service import get_my_events

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

class UpdateProfileRequest(BaseModel):
    name: str
    profession: str
    bio: str
    phoneNumber: str
    location: object
    birthdate: str
    
class UpdateInterestsRequest(BaseModel):
    interests: list

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
        access_token = create_access_token(data={"email": user_data["email"]})

        return {"message": "User authenticated successfully", "access_token": access_token, "token_type": "bearer" , "email": user_data["email"]}

    except Exception as e:
        raise HTTPException(status_code=400, detail="Google login failed")

# Normal Login
@auth_router.post("/login")
async def normal_login(request: NormalLoginRequest):
    user = get_user_by_email(request.email)
    if not user or not verify_user_password(request.email, request.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"email": user["email"]})
    return {"message": "User authenticated successfully", "access_token": access_token, "token_type": "bearer", "email": user["email"]}

@auth_router.post("/register")
async def register_user(request: RegisterRequest):
    if get_user_by_email(request.email):
        raise HTTPException(status_code=400, detail="Email already exists")

    store_user_with_password(request.email, request.password, request.name)
    access_token = create_access_token(data={"email": request.email})

    
    return {
        "message": "User registered successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "email": request.email
    }

# Protected route example that requires authentication
@auth_router.get("/me")
async def get_profile(current_user: dict = Depends(get_current_user)):
    user = get_user_by_email(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "email": user["email"],
        "name": user["name"],
        "profile_picture": user.get("profile_picture", ""),
        "interests": user.get("interests", []),
        "profession": user.get("profession", ""),
        "bio": user.get("bio", ""),
        "phoneNumber": user.get("phoneNumber", ""),
        "location": user.get("location", {}),
        "birthdate": user.get("birthdate", "")
    }
    
@auth_router.put("/me")
async def update_profile(request: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    user = get_user_by_email(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update the user's profile (you can extend this for other fields like profile_picture)
    user["name"] = request.name
    user["profession"] = request.profession
    user["bio"] = request.bio
    user["phoneNumber"] = request.phoneNumber
    user["birthdate"] = request.birthdate
    user["location"] = request.location
    store_or_update_user_data(user)  # Update in Firestore or your database

    return {"message": "Profile updated successfully"}

@auth_router.put("/me/interests")
async def update_interests(request: UpdateInterestsRequest, current_user: dict = Depends(get_current_user)):
    user = get_user_by_email(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    print(user)

    # Update the user's interests
    user["interests"] = request.interests
    store_or_update_user_data(user)
    
    return {"message": "User Interests updated successfully"}

# Fetch events created by the user
@auth_router.get("/me/events/created")
async def fetch_my_events(current_user: dict = Depends(get_current_user)):
    email = current_user["email"]
    events = get_my_events(email)
    
    print(events)
    if events:
        return {"message": "Events fetched successfully", "events": events}
    else:
        raise HTTPException(status_code=404, detail="No events found for the user")

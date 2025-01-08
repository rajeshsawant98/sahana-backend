from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from app.auth.firebase_config import store_user_data, store_user_with_password, verify_user_password, get_user_by_email  # Import the functions

auth_router = APIRouter()

# Define the data models for incoming requests
class GoogleLoginRequest(BaseModel):
    token: str

class NormalLoginRequest(BaseModel):
    email: str  # Changed from username to email
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

# Google Login
@auth_router.post("/google")
async def google_login(request: GoogleLoginRequest):
    try:
        print(f"Google login request received with token: {request.token}")  # Debug print
        token = request.token
        client_id = "505025857168-olhtcsvr2pmpu84k0gb25rkh61qksbm8.apps.googleusercontent.com"

        # Verify the ID token with Google
        id_info = id_token.verify_oauth2_token(token, Request(), client_id)
        print(f"Google ID Info: {id_info}")  # Debug print

        user_data = {
            "uid": id_info["sub"],
            "name": id_info.get("name"),
            "email": id_info.get("email"),
            "profile_picture": id_info.get("picture")
        }

        # Store user data in Firestore
        print(f"Storing user data in Firestore: {user_data}")  # Debug print
        store_user_data(user_data)

        return {"message": "User authenticated successfully", "user_id": user_data["uid"], "name": user_data["name"]}

    except Exception as e:
        print(f"Error in Google login: {str(e)}")  # Debug print
        raise HTTPException(status_code=400, detail=f"Google login failed: {str(e)}")

# Normal Login
@auth_router.post("/login")
async def normal_login(request: NormalLoginRequest):
    try:
        print(f"Normal login request received for email: {request.email}")  # Debug print
        user = get_user_by_email(request.email)  # Use the updated function to get user
        
        if not user:
            print(f"User not found for email: {request.email}")
            raise HTTPException(status_code=400, detail="User not found")
        
        print(f"User found: {user}")  # Debug print
        
        # Verify password
        if not verify_user_password(request.email, request.password):  # Use the existing function for verification
            print(f"Invalid credentials for user: {request.email}")  # Debug print
            raise HTTPException(status_code=400, detail="Invalid credentials")

        return {"message": "User authenticated successfully", "email": user["email"]}

    except Exception as e:
        print(f"Error in normal login: {str(e)}")  # Debug print
        raise HTTPException(status_code=400, detail=f"Login failed: {str(e)}")

# Register New User
@auth_router.post("/register")
async def register_user(request: RegisterRequest):
    try:
        print(f"Registering new user with email: {request.email}")  # Debug print
        # Check if the user already exists
        if get_user_by_email(request.email):
            print(f"Email {request.email} already exists")  # Debug print
            raise HTTPException(status_code=400, detail="Email already exists")

        # Hash the password and store the user
        hashed_password = store_user_with_password(request.email, request.password, request.name)
        print(f"Storing new user with hashed password")  # Debug print
        return {"message": "User registered successfully"}

    except Exception as e:
        print(f"Error in registration: {str(e)}")  # Debug print
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")
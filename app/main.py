from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from app.auth.firebase_config import store_user_data  # Import the function to store user data
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware to handle cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the data model for incoming requests
class GoogleLoginRequest(BaseModel):
    token: str

# Define the route for Google login
@app.post("/api/auth/google")
async def google_login(request: GoogleLoginRequest):
    try:
        # Extract the token
        token = request.token
        client_id = "505025857168-olhtcsvr2pmpu84k0gb25rkh61qksbm8.apps.googleusercontent.com"

        # Verify the ID token with Google
        id_info = id_token.verify_oauth2_token(token, Request(), client_id)

        # Get user info from the token
        user_id = id_info["sub"]
        name = id_info.get("name")
        email = id_info.get("email")
        profile_picture = id_info.get("picture")

        # Store user data in Firestore
        user_data = {
            "uid": user_id,
            "name": name,
            "email": email,
            "profile_picture": profile_picture
        }

        # Store user data in Firestore
        store_user_data(user_data)

        # Respond with the user's information
        return {"message": "User authenticated successfully", "user_id": user_id, "name": name}

    except Exception as e:
        print(f"Error: {str(e)}")  # Log the error for debugging
        raise HTTPException(status_code=400, detail=f"Google login failed: {str(e)}")
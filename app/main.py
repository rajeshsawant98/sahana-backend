from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import auth_router  # Import the auth router
from app.routes.event_routes import event_router  # Import the event router
import uvicorn
from app import config
import os
import firebase_admin
from firebase_admin import credentials

app = FastAPI()

# Initialize Firebase
cred = credentials.Certificate(config.firebase_cred_path)
firebase_admin.initialize_app(cred)


# Add CORS middleware to handle cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the auth router with a prefix for API routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(event_router, prefix="/api/events", tags=["Events"])

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))  # Get Cloud Run PORT dynamically
    uvicorn.run(app, host="0.0.0.0", port=port)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import auth_router  # Import the auth router
from app.routes.event_routes import event_router  # Import the event router
import uvicorn

import os

app = FastAPI()

# Add CORS middleware to handle cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the auth router with a prefix for API routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(event_router, prefix="/api/events", tags=["Events"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Cloud Run requires PORT=8080
    uvicorn.run(app, host="0.0.0.0", port=port)
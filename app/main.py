from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import auth_router  # Import the auth router
from app.routes.event_routes import event_router  # Import the event router

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
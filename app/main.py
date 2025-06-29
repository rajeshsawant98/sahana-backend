from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import auth_router  # Import the auth router
from app.routes.event_routes import event_router  # Import the event router
from app.routes.admin_routes import admin_router  # Import the admin router
from app.routes.ingestion_routes import ingestion_router
from app.routes.friend_routes import friend_router  # Import the friend router
import uvicorn

app = FastAPI()

origins = [
    "https://sahana-drab.vercel.app",  # Deployed frontend
    "http://localhost:3000", # Local React frontend
    "http://localhost:5173",       # Vite local dev
]
# Add CORS middleware to handle cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the auth router with a prefix for API routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(event_router, prefix="/api/events", tags=["Events"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(ingestion_router, prefix="/api/ingest", tags=["Ingestion"])
app.include_router(friend_router, prefix="/api/friends", tags=["Friends"])

if __name__ == "__main__":
     uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
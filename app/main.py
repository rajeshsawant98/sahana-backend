from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import auth_router
from app.routes.event_routes import event_router
from contextlib import asynccontextmanager

app = FastAPI()

origins = [
    "https://sahana-drab.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(event_router, prefix="/api/events", tags=["Events"])

if __name__ == "__main__":
     uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
     


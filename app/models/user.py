from pydantic import BaseModel
from typing import Optional
from google.cloud import firestore  # Firestore library

class User(BaseModel):
    name: str
    email: str
    password: str  # Assuming you store the plain password or hashed password in Firestore
    interests: Optional[list] = None
    profession: Optional[str] = None
    bio: Optional[str] = None
    phoneNumber: Optional[str] = None
    location: Optional[dict] = None
    birthdate: Optional[str] = None
    role: Optional[str] = "user"  # Default role is 'user'
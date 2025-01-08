from pydantic import BaseModel
from typing import Optional
from google.cloud import firestore  # Firestore library

class User(BaseModel):
    email: str
    password: str  # Assuming you store the plain password or hashed password in Firestore

import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials

from app import config

load_dotenv()


def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(config.firebase_cred_path)
        firebase_admin.initialize_app(cred)

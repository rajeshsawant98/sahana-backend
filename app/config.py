import os
import json
from google.cloud import secretmanager
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv()

def get_secret():
    """Fetch secret from Google Secret Manager when running in Cloud Run"""
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):  
        # If GOOGLE_APPLICATION_CREDENTIALS is already set, we are running locally
        print("Running locally, using existing credentials.")
        return None  

    print("Running on Cloud Run, fetching secret from Secret Manager.")
    client = secretmanager.SecretManagerServiceClient()
    # secret_name = f"projects/sahana-deaf0/secrets/{os.getenv('FIREBASE_CRED_SECRET')}/versions/latest"
    secret_name = f"projects/sahana-deaf0/secrets/firebase_cred/versions/latest"
    

    response = client.access_secret_version(name=secret_name)
    secret_value = response.payload.data.decode("UTF-8")
    

    return json.loads(secret_value)  

# Determine the credential path
firebase_cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")  # Local path
if firebase_cred_path is None:  
    # Running in Cloud Run, fetch secret and write to file
    firebase_cred_path = os.getenv("FIREBASE_CRED_PATH")
    firebase_creds = get_secret()
    
    if firebase_creds and firebase_cred_path is not None:  # Only write if we fetched from Secret Manager and path is valid
        with open(firebase_cred_path, "w") as f:
            json.dump(firebase_creds, f)

# Set the environment variable for Firebase SDK
if firebase_cred_path is not None:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = firebase_cred_path
    print(f"Using Firebase credentials from: {firebase_cred_path}")
else:
    print("Firebase credentials path is not set.")
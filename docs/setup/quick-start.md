# Quick Start Guide

Get the Sahana Backend up and running in minutes.

## Prerequisites

- Python 3.10 or higher
- Git
- Firebase project (for authentication and database)

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-username/sahana-backend.git
cd sahana-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use existing one
3. Enable Authentication (Email/Password + Google)
4. Enable Firestore Database
5. Generate Firebase Admin SDK key:
   - Go to Project Settings → Service Accounts
   - Click "Generate new private key"
   - Save as `firebase_cred.json` in project root

## Step 3: Environment Configuration

Create a `.env` file in the project root:

```env
# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key_here
JWT_REFRESH_SECRET_KEY=your_refresh_secret_key_here

# Google Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Firebase
GOOGLE_APPLICATION_CREDENTIALS=firebase_cred.json

# Optional: External APIs
TICKETMASTER_API_KEY=your_ticketmaster_api_key
```

## Step 4: Run the Server

```bash
uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`

## Step 5: Verify Installation

1. **API Documentation**: Visit `http://localhost:8000/docs`
2. **Health Check**: Visit `http://localhost:8000/health` (if implemented)
3. **Test Authentication**: Use the Swagger UI to test login endpoints

## Quick Test

Using curl to test the API:

```bash
# Test if server is running
curl http://localhost:8000/events/

# Should return list of events (empty if none exist)
```

## Next Steps

- [Detailed Installation Guide](installation.md)
- [Environment Configuration](environment.md)
- [API Documentation](../api/overview.md)
- [Testing Guide](../testing/guide.md)

## Troubleshooting

### Common Issues

**ImportError**: Make sure virtual environment is activated and dependencies are installed

**Firebase Connection Error**: Verify `firebase_cred.json` is in the project root and valid

**Environment Variables**: Double-check `.env` file format and values

**Port Already in Use**: Change port with `uvicorn app.main:app --reload --port 8001`

For more help, see the [troubleshooting guide](../troubleshooting.md).

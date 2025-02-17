# Sahana-backend

source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload

docker buildx build --platform linux/amd64 -t gcr.io/sahana-deaf0/sahana-backend .


gcloud run deploy sahana-backend \  --image gcr.io/sahana-deaf0/sahana-backend \
  --platform managed \
  --region us-west1 \
  --allow-unauthenticated \
  --set-env-vars=FIREBASE_CRED_SECRET=firebase_cred \
  --set-env-vars=FIREBASE_CRED_PATH=/tmp/firebase_cred.json
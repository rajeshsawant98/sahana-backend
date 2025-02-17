# Sahana-backend

source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload

docker buildx build --platform linux/amd64 -t gcr.io/sahana-deaf0/sahana-backend .
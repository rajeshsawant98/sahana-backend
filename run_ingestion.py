import os
import asyncio
from dotenv import load_dotenv

# Load local env vars (ignored on Cloud Run if using Secret Manager)
load_dotenv()

from app.services.event_ingestion_service import ingest_events_for_all_cities

def main():
    asyncio.run(ingest_events_for_all_cities())

if __name__ == "__main__":
    main()
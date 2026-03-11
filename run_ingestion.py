import asyncio
from dotenv import load_dotenv

# Load local env vars (ignored on Cloud Run if using Secret Manager)
load_dotenv()

from app.utils.redis_client import init_redis, close_redis
from app.services.event_ingestion_service import ingest_ticketmaster_events_for_all_cities


async def main():
    await init_redis()
    try:
        result = await ingest_ticketmaster_events_for_all_cities()
        print(result)
    finally:
        await close_redis()


if __name__ == "__main__":
    asyncio.run(main())

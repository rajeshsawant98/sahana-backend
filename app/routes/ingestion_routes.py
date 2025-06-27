from fastapi import APIRouter
import asyncio
from app.services.event_ingestion_service import ingest_ticketmaster_events_for_all_cities

ingestion_router = APIRouter()

@ingestion_router.post("/daily")
async def daily_ingestion():
    result = await ingest_ticketmaster_events_for_all_cities()
    return {"status": "success", "result": result}
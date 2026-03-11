from fastapi import APIRouter
from fastapi.responses import JSONResponse
import asyncio
from app.services.event_ingestion_service import ingest_events_for_all_cities

ingestion_router = APIRouter()

@ingestion_router.post("/daily")
async def daily_ingestion():
    result = await ingest_events_for_all_cities()
    if result.get("status") == "skipped":
        return JSONResponse(
            status_code=409,
            content={"status": "skipped", "reason": result.get("reason", "ingestion_locked")}
        )
    return {"status": "success", "result": result}

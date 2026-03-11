from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.services.event_ingestion_service import (
    ingest_events_for_all_cities,
    ingest_ticketmaster_events_for_all_cities,
)

ingestion_router = APIRouter()


@ingestion_router.post("/ticketmaster")
async def ticketmaster_ingestion():
    result = await ingest_ticketmaster_events_for_all_cities()
    if result.get("status") == "skipped":
        return JSONResponse(
            status_code=409,
            content={"status": "skipped", "reason": result.get("reason", "ingestion_locked")}
        )
    return {"status": "success", "result": result}


@ingestion_router.post("/full")
async def full_ingestion():
    result = await ingest_events_for_all_cities()
    if result.get("status") == "skipped":
        return JSONResponse(
            status_code=409,
            content={"status": "skipped", "reason": result.get("reason", "ingestion_locked")}
        )
    return {"status": "success", "result": result}

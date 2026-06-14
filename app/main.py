from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, status

from app.models import EventCreate, EventResponse, MetricSummary, CustomerSummaryResponse
from app.repository import EventRepository, EventNotFoundError, DuplicateEventError
from app.services import EventService

app = FastAPI(title="Ingestion API")

# Single shared instances (in-memory repo + service)
repository = EventRepository()
service = EventService(repository)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate) -> EventResponse:
    try:
        return service.ingest_event(event)
    except DuplicateEventError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@app.get("/events/{event_id}", response_model=EventResponse)
async def read_event(event_id: UUID) -> EventResponse:
    try:
        return service.get_event(event_id)
    except EventNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@app.get("/events", response_model=List[EventResponse])
async def list_events(
    customer_id: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    metric_name: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
) -> List[EventResponse]:
    return service.list_events(
        customer_id=customer_id,
        resource_id=resource_id,
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time,
    )


@app.get("/customers/{customer_id}/summary", response_model=CustomerSummaryResponse)
async def customer_summary(customer_id: str) -> CustomerSummaryResponse:
    return service.get_customer_summary(customer_id)
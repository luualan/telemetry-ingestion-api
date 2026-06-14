from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from app.models import EventCreate, EventResponse


class EventNotFoundError(KeyError):
    pass


class DuplicateEventError(ValueError):
    pass


class EventRepository:
    def __init__(self) -> None:
        self._store: Dict[UUID, EventResponse] = {}
        self._lock = Lock()

    def create_event(self, event: EventCreate) -> EventResponse:
        with self._lock:
            if event.event_id is not None:
                if event.event_id in self._store:
                    raise DuplicateEventError(f"{event.event_id} already exists")
                event_id = event.event_id
            else:
                event_id = uuid4()
                while event_id in self._store:
                    event_id = uuid4()

            resp = EventResponse(
                event_id=event_id,
                customer_id=event.customer_id,
                resource_id=event.resource_id,
                metric_name=event.metric_name,
                value=event.value,
                timestamp=event.timestamp,
                source=event.source,
            )
            self._store[event_id] = resp
            return resp

    def get_event(self, event_id: UUID) -> EventResponse:
        with self._lock:
            try:
                return self._store[event_id]
            except KeyError as exc:
                raise EventNotFoundError(f"{event_id} not found") from exc

    def list_events(
        self,
        customer_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EventResponse]:
        with self._lock:
            results: List[EventResponse] = []
            for ev in self._store.values():
                if customer_id is not None and ev.customer_id != customer_id:
                    continue
                if resource_id is not None and ev.resource_id != resource_id:
                    continue
                if metric_name is not None and ev.metric_name != metric_name:
                    continue
                if start_time is not None and ev.timestamp < start_time:
                    continue
                if end_time is not None and ev.timestamp > end_time:
                    continue
                results.append(ev)
            return results
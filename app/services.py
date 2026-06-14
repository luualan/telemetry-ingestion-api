from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from app.models import EventCreate, EventResponse, MetricSummary, CustomerSummaryResponse
from app.repository import EventRepository


class EventService:
    """Business logic layer for events. Keeps HTTP concerns out of this module."""

    def __init__(self, repository: EventRepository) -> None:
        self.repository = repository

    def ingest_event(self, event: EventCreate) -> EventResponse:
        return self.repository.create_event(event)

    def get_event(self, event_id: UUID) -> EventResponse:
        return self.repository.get_event(event_id)

    def list_events(
        self,
        customer_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[EventResponse]:
        return self.repository.list_events(
            customer_id=customer_id,
            resource_id=resource_id,
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
        )

    def get_customer_summary(self, customer_id: str) -> CustomerSummaryResponse:
        """
        Return per-metric aggregates for a customer:
        metric_name -> {"count": int, "sum": float, "avg": float, "min": float, "max": float}
        """
        events = self.repository.list_events(customer_id=customer_id)

        accum = defaultdict(lambda: {"count": 0, "sum": 0.0, "min": float("inf"), "max": float("-inf")})
        for event in events:
            metric = event.metric_name
            value = float(event.value)

            stat = accum[metric]
            stat["count"] += 1
            stat["sum"] += value
            stat["min"] = min(stat["min"], value)
            stat["max"] = max(stat["max"], value)

        summaries: Dict[str, MetricSummary] = {}
        for metric, stat in accum.items():
            count = stat["count"]
            total = stat["sum"]

            summaries[metric] = MetricSummary(
                count=count,
                total=total,
                avg=total / count,
                min=stat["min"],
                max=stat["max"],
            )

        return CustomerSummaryResponse(
            customer_id=customer_id,
            metrics=summaries,
        )
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import UUID
import math

from pydantic import BaseModel, Field, field_validator, ConfigDict

# Non-empty string intent (min_length enforced by Pydantic)
NonEmptyStr = Annotated[str, Field(min_length=1)]


class EventCreate(BaseModel):
    event_id: Optional[UUID] = None
    customer_id: NonEmptyStr
    resource_id: NonEmptyStr
    metric_name: NonEmptyStr
    value: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: Optional[NonEmptyStr] = None

    # Strip whitespace for string fields before other validation runs.
    @field_validator("customer_id", "resource_id", "metric_name", "source", mode="before")
    @classmethod
    def _strip_strings(cls, v):
        if v is None:
            return None
        return v.strip()

    # Ensure timestamp is timezone-aware and normalized to UTC.
    @field_validator("timestamp")
    @classmethod
    def _normalize_timestamp_to_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

    # Reject NaN and Infinity for numeric values.
    @field_validator("value")
    @classmethod
    def _ensure_value_is_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("value must be a finite number")
        return float(v)


class EventResponse(BaseModel):
    event_id: UUID
    customer_id: str
    resource_id: str
    metric_name: str
    value: float
    timestamp: datetime
    source: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MetricSummary(BaseModel):
    count: int
    total: float
    avg: float
    min: float
    max: float


class CustomerSummaryResponse(BaseModel):
    customer_id: str
    metrics: dict[str, MetricSummary]
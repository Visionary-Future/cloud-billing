"""Pydantic models for AWS Cost Explorer API responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MetricValue(BaseModel):
    """A single cost metric, e.g. {"Amount": "10.5", "Unit": "USD"}."""

    Amount: str
    Unit: str


class Group(BaseModel):
    """Cost data grouped by a dimension (e.g. by SERVICE, REGION)."""

    Keys: List[str]
    Metrics: Dict[str, MetricValue]


class ResultByTime(BaseModel):
    """Cost data for a single time period (one month or one day)."""

    TimePeriod: Dict[str, str]
    Total: Optional[Dict[str, MetricValue]] = None
    Groups: Optional[List[Group]] = None
    Estimated: bool


class CostAndUsageResponse(BaseModel):
    """Wrapper for the get_cost_and_usage API response."""

    ResultsByTime: List[ResultByTime]
    NextPageToken: Optional[str] = None

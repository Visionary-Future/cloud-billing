# Copyright 2025 Visionary Future
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

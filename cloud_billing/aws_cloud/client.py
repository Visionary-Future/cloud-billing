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

"""AWS Cloud billing client using Cost Explorer API."""

import re
from typing import Any, Dict, List, Optional

import boto3

from .types import CostAndUsageResponse, ResultByTime


class AWSCloudClient:
    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        region_name: str = "us-east-1",
    ) -> None:
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region_name = region_name

        self._session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )
        self._ce_client = self._session.client("ce", region_name="us-east-1")

    def get_credentials(self) -> Dict[str, str]:
        return {
            "AccessKeyId": self.access_key_id,
            "SecretAccessKey": self.secret_access_key,
            "RegionName": self.region_name,
        }

    def _validate_time_period(self, start: str, end: str) -> None:
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(pattern, start):
            raise ValueError(f"Invalid start date format: {start}, expected YYYY-MM-DD")
        if not re.match(pattern, end):
            raise ValueError(f"Invalid end date format: {end}, expected YYYY-MM-DD")
        if start >= end:
            raise ValueError(f"start date ({start}) must be before end date ({end})")

    def _has_more_data(self, next_token: Optional[str]) -> bool:
        return bool(next_token and next_token.strip())

    def get_cost_and_usage(
        self,
        time_period: Dict[str, str],
        granularity: str = "MONTHLY",
        metrics: Optional[List[str]] = None,
        group_by: Optional[List[Dict[str, str]]] = None,
        filter_expression: Optional[Dict[str, Any]] = None,
    ) -> List[ResultByTime]:
        """Fetch cost and usage data with automatic pagination.

        Args:
            time_period: {"Start": "YYYY-MM-DD", "End": "YYYY-MM-DD"}
            granularity: "MONTHLY" or "DAILY"
            metrics: Cost metrics, defaults to ["UnblendedCost"]
            group_by: e.g. [{"Type": "DIMENSION", "Key": "SERVICE"}]
            filter_expression: AWS Cost Explorer filter dict

        Returns:
            Merged list of ResultByTime objects (all pages).
        """
        self._validate_time_period(time_period["Start"], time_period["End"])

        params: Dict[str, Any] = {
            "TimePeriod": time_period,
            "Granularity": granularity.upper(),
            "Metrics": metrics or ["UnblendedCost"],
        }
        if group_by:
            params["GroupBy"] = group_by
        if filter_expression:
            params["Filter"] = filter_expression

        results: List[ResultByTime] = []
        next_token: Optional[str] = None

        while True:
            if next_token:
                params["NextPageToken"] = next_token

            raw = self._ce_client.get_cost_and_usage(**params)
            parsed = CostAndUsageResponse.model_validate(raw)
            results.extend(parsed.ResultsByTime)

            if not self._has_more_data(parsed.NextPageToken):
                break
            next_token = parsed.NextPageToken

        return results

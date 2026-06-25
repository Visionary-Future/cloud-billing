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

"""Huawei Cloud billing client using BSS API."""

import re
from typing import Dict, List, Optional, Tuple

from huaweicloudsdkbss.v2 import BssClient, ShowCustomerMonthlySumRequest
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.http.http_config import HttpConfig

from .types import MonthlyBillItem, MonthlyBillResponse


class HuaweiCloudClient:
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        domain_id: str,
        region_id: str = "cn-east-3",
    ) -> None:
        self.access_key = access_key
        self.secret_key = secret_key
        self.domain_id = domain_id
        self.region_id = region_id

        credentials = BasicCredentials(access_key, secret_key, domain_id)
        config = HttpConfig.get_default_config()
        config.ignore_ssl_verification = False

        self._bss_client = (
            BssClient.new_builder()
            .with_http_config(config)
            .with_credentials(credentials)
            .with_endpoint("https://bss.myhuaweicloud.com")
            .build()
        )

    def get_credentials(self) -> Dict[str, str]:
        return {
            "AccessKey": self.access_key,
            "SecretKey": self.secret_key,
            "DomainId": self.domain_id,
            "RegionId": self.region_id,
        }

    def _validate_billing_cycle(self, bill_cycle: str) -> None:
        if not re.match(r"^\d{4}-\d{2}$", bill_cycle):
            raise ValueError(f"Invalid billing cycle format: {bill_cycle}, expected YYYY-MM")

    def query_monthly_bill_summary(
        self, bill_cycle: str, offset: int = 0, limit: int = 100
    ) -> Tuple[Optional[List[MonthlyBillItem]], Optional[str]]:
        """Query monthly bill summary for the given billing cycle.

        Args:
            bill_cycle: Billing cycle in YYYY-MM format.
            offset: Pagination offset.
            limit: Page size (max 1000).

        Returns:
            Tuple of (bill_items, error). One will be None.
        """
        try:
            self._validate_billing_cycle(bill_cycle)

            request = ShowCustomerMonthlySumRequest()
            request.bill_cycle = bill_cycle
            request.offset = offset
            request.limit = limit

            raw_response = self._bss_client.show_customer_monthly_sum(request)
            response_dict = self._response_to_dict(raw_response)
            response = MonthlyBillResponse.model_validate(response_dict)

            all_items = list(response.bill_sums)

            if response.total_count > offset + limit:
                remaining, error = self.query_monthly_bill_summary(bill_cycle, offset=offset + limit, limit=limit)
                if error:
                    return None, error
                if remaining:
                    all_items.extend(remaining)

            return all_items, None

        except Exception as e:
            return None, str(e)

    def _response_to_dict(self, raw_response) -> dict:
        """Convert SDK response object to a plain dict for Pydantic validation."""
        if hasattr(raw_response, "to_dict"):
            data = raw_response.to_dict()
        else:
            data = {"bill_sums": [], "total_count": 0, "currency": "CNY"}

        bill_sums = data.get("bill_sums") or []
        return {
            "bill_sums": bill_sums,
            "total_count": data.get("total_count", 0),
            "currency": data.get("currency", "CNY"),
        }

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

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from aliyunsdkcore.auth.credentials import (
    AccessKeyCredential,  # type: ignore[import-untyped]
)
from aliyunsdkcore.client import (  # type: ignore[import-untyped]
    AcsClient,
    CommonRequest,
)
from pydantic import ValidationError

from .exceptions import APIError, InvalidResponseError
from .types import (
    AmortizedItem,
    AmortizedResponse,
    QueryAccountBillItem,
    QueryAccountBillResponse,
    QueryInstanceBillItem,
    QueryInstanceBillResponse,
)

DEFAULT_MAX_PAGE_SIZE = 300


@dataclass
class PaginationParams:
    """paginator"""

    max_page_size: int = 100
    next_token: Optional[str] = None


class AlibabaCloudClient:
    def __init__(self, access_key_id: str, access_key_secret: str, region_id: str) -> None:
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.region_id = region_id
        self.credentials = AccessKeyCredential(self.access_key_id, self.access_key_secret)
        self.client = AcsClient(region_id=region_id, credential=self.credentials, timeout=3000)

    def get_credentials(self) -> Dict[str, str]:
        return {
            "AccessKeyId": self.access_key_id,
            "AccessKeySecret": self.access_key_secret,
            "RegionId": self.region_id,
        }

    def make_request(self, request: CommonRequest) -> Dict[str, Any]:
        try:
            response = self.client.do_action_with_exception(request)
            if response:
                return json.loads(response)
            raise ValueError("Empty or invalid response")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse response JSON: {e}") from e

    def fetch_instance_bill_by_billing_cycle(
        self, billing_cycle: str, billing_date: Optional[str] = None, max_page_size: int = DEFAULT_MAX_PAGE_SIZE
    ) -> List[QueryInstanceBillItem]:
        """Fetch instance bill for the given billing cycle (pagination handled automatically).

        Args:
            billing_cycle: Billing cycle in YYYY-MM format.
            billing_date: Specific billing date in YYYY-MM-DD format.
            max_page_size: Maximum number of records per page (default 100).

        Returns:
            Merged list of bill items.

        Raises:
            ValueError: When the billing cycle format is invalid.
        """
        self._validate_billing_cycle(billing_cycle)
        pagination = PaginationParams(max_page_size=max_page_size)
        result: List[QueryInstanceBillItem] = []

        while True:
            request = self._build_bill_request(
                billing_cycle=billing_cycle, billing_date=billing_date, pagination=pagination
            )

            response = self.make_request(request)
            bill_response = QueryInstanceBillResponse.model_validate(response)

            result.extend(bill_response.Data.Items)

            if not self._has_more_data(bill_response.Data.NextToken):
                break

            pagination.next_token = bill_response.Data.NextToken

        return result

    def _build_bill_request(
        self, billing_cycle: str, billing_date: Optional[str], pagination: PaginationParams
    ) -> CommonRequest:
        request: CommonRequest = CommonRequest()
        request.set_accept_format("json")
        request.set_domain("business.aliyuncs.com")
        request.set_method("POST")
        request.set_protocol_type("http")
        request.set_version("2017-12-14")
        request.set_action_name("DescribeInstanceBill")

        request.add_query_param("BillingCycle", billing_cycle)
        request.add_query_param("MaxResults", str(pagination.max_page_size))

        if billing_date:
            request.add_query_param("BillingDate", billing_date)
            request.add_query_param("Granularity", "DAILY")

        if pagination.next_token:
            request.add_query_param("NextToken", pagination.next_token)

        return request

    def _validate_billing_cycle(self, billing_cycle: str) -> None:
        if not re.match(r"^\d{4}-\d{2}$", billing_cycle):
            raise ValueError(f"Invalid billing cycle format: {billing_cycle}, expected YYYY-MM")

    def _has_more_data(self, next_token: Optional[str]) -> bool:
        return bool(next_token and next_token.strip())

    def fetch_instance_amortized_cost_by_amortization_period(self, billing_cycle: str) -> List[AmortizedItem]:
        """Fetch instance amortized cost by amortization period.

        Args:
            billing_cycle: Billing cycle in YYYY-MM format.

        Returns:
            List of amortized cost items.

        Raises:
            APIError: When the API request fails.
        """
        self._validate_billing_cycle(billing_cycle)

        items = []
        next_token = None

        while True:
            request = self._build_request(billing_cycle, next_token)
            response = self._send_request(request)
            amortized_response = self._parse_response(response)

            items.extend(amortized_response.Data.Items)
            next_token = amortized_response.Data.NextToken

            if not self._has_more_data(next_token):
                break

        return items

    def fetch_daily_account_bill_by_product(
        self,
        billing_cycle: str,
        billing_date: Optional[str] = None,
        product_code: Optional[str] = None,
        page_size: int = DEFAULT_MAX_PAGE_SIZE,
    ) -> List[QueryAccountBillItem]:
        """Fetch account bill aggregated by product.

        Uses QueryAccountBill with IsGroupByProduct=true.
        When billing_date is provided, queries DAILY granularity for that day;
        otherwise queries MONTHLY for the billing cycle.

        Args:
            billing_cycle: Billing cycle in YYYY-MM format.
            billing_date: Optional billing date in YYYY-MM-DD format for daily query.
            product_code: Optional product code filter (e.g. "ecs", "rds").
            page_size: Page size for pagination (default 300, max 300).

        Returns:
            List of account bill items grouped by product.

        Raises:
            ValueError: When billing_cycle or billing_date format is invalid.
            APIError: When the API request fails.
            InvalidResponseError: When the response cannot be parsed.
        """
        self._validate_billing_cycle(billing_cycle)
        if billing_date is not None:
            self._validate_billing_date(billing_date)

        items: List[QueryAccountBillItem] = []
        page_num = 1

        while True:
            request = self._build_account_bill_request(
                billing_cycle=billing_cycle,
                billing_date=billing_date,
                page_num=page_num,
                page_size=page_size,
                product_code=product_code,
            )
            response = self._send_account_bill_request(request)
            bill_response = self._parse_account_bill_response(response)

            items.extend(bill_response.Data.Items)

            total = bill_response.Data.TotalCount
            if page_num * page_size >= total or not bill_response.Data.Items:
                break
            page_num += 1

        return items

    def _build_account_bill_request(
        self,
        billing_cycle: str,
        billing_date: Optional[str],
        page_num: int,
        page_size: int,
        product_code: Optional[str] = None,
    ) -> CommonRequest:
        request = CommonRequest()
        request.set_accept_format("json")
        request.set_domain("business.aliyuncs.com")
        request.set_method("POST")
        request.set_protocol_type("https")
        request.set_version("2017-12-14")
        request.set_action_name("QueryAccountBill")

        request.add_query_param("BillingCycle", billing_cycle)
        request.add_query_param("IsGroupByProduct", "true")
        request.add_query_param("PageNum", str(page_num))
        request.add_query_param("PageSize", str(page_size))

        if billing_date:
            request.add_query_param("BillingDate", billing_date)
            request.add_query_param("Granularity", "DAILY")
        else:
            request.add_query_param("Granularity", "MONTHLY")

        if product_code:
            request.add_query_param("ProductCode", product_code)

        return request

    def _validate_billing_date(self, billing_date: str) -> None:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", billing_date):
            raise ValueError(f"Invalid billing date format: {billing_date}, expected YYYY-MM-DD")

    def _send_account_bill_request(self, request: CommonRequest) -> dict[str, Any]:
        try:
            return self.make_request(request=request)
        except Exception as e:
            raise APIError(f"Failed to fetch daily account bill by product: {str(e)}") from e

    def _parse_account_bill_response(self, response: dict[str, Any]) -> QueryAccountBillResponse:
        try:
            return QueryAccountBillResponse.model_validate(response)
        except ValidationError as e:
            raise InvalidResponseError(
                message=f"Invalid account bill response format: {str(e)}",
                response_data=response,
            ) from e

    def _build_request(self, billing_cycle: str, next_token: str | None = None) -> CommonRequest:
        request = CommonRequest()
        request.set_accept_format("json")
        request.set_domain("business.aliyuncs.com")
        request.set_method("POST")
        request.set_protocol_type("https")
        request.set_version("2017-12-14")
        request.set_action_name("DescribeInstanceAmortizedCostByAmortizationPeriod")

        request.add_query_param("BillingCycle", billing_cycle)
        request.add_query_param("MaxResults", DEFAULT_MAX_PAGE_SIZE)

        if next_token:
            request.add_query_param("NextToken", next_token)

        return request

    def _send_request(self, request: CommonRequest) -> dict[str, Any]:
        try:
            return self.make_request(request=request)
        except Exception as e:
            raise APIError(f"Failed to fetch amortized cost data: {str(e)}")

    def _parse_response(self, response: dict[str, Any]) -> AmortizedResponse:
        try:
            return AmortizedResponse.model_validate(response)
        except ValidationError as e:
            raise InvalidResponseError(message=f"Invalid reponse data format: {str(e)}", response_data=response)

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

"""Tencent Cloud billing client using Billing API."""

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import ValidationError
from tencentcloud.billing.v20180709 import billing_client, models
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile

from .types import (
    AccountBalanceItem,
    BillDetailItem,
    BillResourceSummaryItem,
    BillSummaryByProductItem,
    DescribeBillDetailResponse,
    DescribeBillResourceSummaryResponse,
    DescribeBillSummaryByProductResponse,
)

DEFAULT_MAX_PAGE_SIZE = 300


@dataclass
class PaginationParams:
    """Pagination parameters for offset-based Tencent Cloud APIs."""

    offset: int = 0
    limit: int = 100


class TencentCloudClient:
    """Client for retrieving billing data from Tencent Cloud.

    Uses the Billing API (v2018-07-09) with SecretId/SecretKey authentication.
    """

    def __init__(self, secret_id: str, secret_key: str, region: str = "ap-guangzhou") -> None:
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region

        cred = credential.Credential(secret_id, secret_key)

        http_profile = HttpProfile()
        http_profile.endpoint = "billing.tencentcloudapi.com"

        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile

        self._client = billing_client.BillingClient(cred, region, client_profile)

    def get_credentials(self) -> Dict[str, str]:
        return {
            "SecretId": self.secret_id,
            "SecretKey": self.secret_key,
            "Region": self.region,
        }

    def _validate_billing_cycle(self, billing_cycle: str) -> None:
        if not re.match(r"^\d{4}-\d{2}$", billing_cycle):
            raise ValueError(f"Invalid billing cycle format: {billing_cycle}, expected YYYY-MM")

    def _response_to_dict(self, response: Any) -> Dict[str, Any]:
        """Convert a Tencent Cloud SDK response object to a plain dict for Pydantic validation."""
        return json.loads(response.to_json_string())

    # ------------------------------------------------------------------
    # DescribeBillDetail — instance-level billing detail
    # ------------------------------------------------------------------

    def describe_bill_detail(
        self,
        month: str,
        pay_mode: Optional[str] = None,
        resource_id: Optional[str] = None,
        business_code: Optional[str] = None,
        max_page_size: int = DEFAULT_MAX_PAGE_SIZE,
    ) -> List[BillDetailItem]:
        """Fetch bill detail records for the given billing month.

        Automatically paginates through all available records.

        Args:
            month: Billing month in YYYY-MM format (up to 18 months back).
            pay_mode: Optional payment mode filter: "prePay" (subscription) or "postPay" (pay-as-you-go).
            resource_id: Optional specific resource ID (e.g. "ins-xxx").
            business_code: Optional product code filter (e.g. "p_cvm").
            max_page_size: Maximum records per page (default 300, max 300).

        Returns:
            List of BillDetailItem objects.

        Raises:
            ValueError: When the month format is invalid.
            TencentCloudSDKException: When the API request fails.
        """
        self._validate_billing_cycle(month)

        pagination = PaginationParams(limit=max_page_size)
        result: List[BillDetailItem] = []

        while True:
            request = self._build_bill_detail_request(
                month=month,
                pay_mode=pay_mode,
                resource_id=resource_id,
                business_code=business_code,
                pagination=pagination,
            )

            try:
                response = self._client.DescribeBillDetail(request)
                response_dict = self._response_to_dict(response)
                parsed = DescribeBillDetailResponse.model_validate(response_dict)

                result.extend(parsed.DetailSet)

                if parsed.Total is not None:
                    if len(result) >= parsed.Total:
                        break
                    pagination.offset += pagination.limit
                else:
                    if len(parsed.DetailSet) < pagination.limit:
                        break
                    pagination.offset += pagination.limit

            except TencentCloudSDKException as e:
                raise TencentCloudSDKException(
                    code=e.code,
                    message=f"Failed to fetch bill detail: {e.message}",
                    requestId=e.requestId,
                )

        return result

    def _build_bill_detail_request(
        self,
        month: str,
        pay_mode: Optional[str],
        resource_id: Optional[str],
        business_code: Optional[str],
        pagination: PaginationParams,
    ) -> models.DescribeBillDetailRequest:
        request = models.DescribeBillDetailRequest()
        request.Month = month
        request.Offset = pagination.offset
        request.Limit = pagination.limit
        request.NeedRecordNum = 0

        if pay_mode:
            request.PayMode = pay_mode
        if resource_id:
            request.ResourceId = resource_id
        if business_code:
            request.BusinessCode = business_code

        return request

    # ------------------------------------------------------------------
    # DescribeBillResourceSummary — resource-level cost summary
    # ------------------------------------------------------------------

    def describe_bill_resource_summary(
        self,
        month: str,
        pay_mode: Optional[str] = None,
        max_page_size: int = 300,
    ) -> List[BillResourceSummaryItem]:
        """Fetch resource-level cost summary for the given billing month.

        Args:
            month: Billing month in YYYY-MM format.
            pay_mode: Optional payment mode filter.
            max_page_size: Maximum records per page (max 1000).

        Returns:
            List of BillResourceSummaryItem objects.
        """
        self._validate_billing_cycle(month)

        pagination = PaginationParams(limit=max_page_size)
        result: List[BillResourceSummaryItem] = []

        while True:
            request = models.DescribeBillResourceSummaryRequest()
            request.Month = month
            request.Offset = pagination.offset
            request.Limit = pagination.limit
            request.NeedRecordNum = 0

            if pay_mode:
                request.PayMode = pay_mode

            try:
                response = self._client.DescribeBillResourceSummary(request)
                response_dict = self._response_to_dict(response)
                parsed = DescribeBillResourceSummaryResponse.model_validate(response_dict)

                result.extend(parsed.ResourceSummarySet)

                if parsed.Total is not None:
                    if len(result) >= parsed.Total:
                        break
                    pagination.offset += pagination.limit
                else:
                    if len(parsed.ResourceSummarySet) < pagination.limit:
                        break
                    pagination.offset += pagination.limit

            except TencentCloudSDKException as e:
                raise TencentCloudSDKException(
                    code=e.code,
                    message=f"Failed to fetch resource summary: {e.message}",
                    requestId=e.requestId,
                )

        return result

    # ------------------------------------------------------------------
    # DescribeBillSummaryByProduct — product-level cost summary
    # ------------------------------------------------------------------

    def describe_bill_summary_by_product(
        self,
        month: str,
    ) -> List[BillSummaryByProductItem]:
        """Fetch product-level cost summary for the given billing month.

        Args:
            month: Billing month in YYYY-MM format.

        Returns:
            List of BillSummaryByProductItem objects.
        """
        self._validate_billing_cycle(month)

        request = models.DescribeBillSummaryByProductRequest()
        request.Month = month

        try:
            response = self._client.DescribeBillSummaryByProduct(request)
            response_dict = self._response_to_dict(response)
            parsed = DescribeBillSummaryByProductResponse.model_validate(response_dict)
            return parsed.SummaryDetail
        except TencentCloudSDKException as e:
            raise TencentCloudSDKException(
                code=e.code,
                message=f"Failed to fetch product summary: {e.message}",
                requestId=e.requestId,
            )

    # ------------------------------------------------------------------
    # DescribeAccountBalance — account balance
    # ------------------------------------------------------------------

    def describe_account_balance(self) -> AccountBalanceItem:
        """Query the current account balance.

        Returns:
            AccountBalanceItem with balance details.

        Raises:
            TencentCloudSDKException: When the API request fails.
        """
        request = models.DescribeAccountBalanceRequest()

        try:
            response = self._client.DescribeAccountBalance(request)
            response_dict = self._response_to_dict(response)
            return AccountBalanceItem.model_validate(response_dict)
        except TencentCloudSDKException as e:
            raise TencentCloudSDKException(
                code=e.code,
                message=f"Failed to fetch account balance: {e.message}",
                requestId=e.requestId,
            )

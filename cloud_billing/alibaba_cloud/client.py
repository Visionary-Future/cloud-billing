import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from aliyunsdkcore.auth.credentials import AccessKeyCredential
from aliyunsdkcore.client import AcsClient, CommonRequest
from pydantic import ValidationError

from .exceptions import APIError, InvalidResponseError
from .types import (
    AmortizedItem,
    AmortizedResponse,
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
        self.client = AcsClient(region_id=region_id, credential=self.credentials)

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
            raise ValueError("响应为空或无效")
        except json.JSONDecodeError as e:
            raise ValueError(f"响应JSON解析失败: {e}") from e

    def fetch_instance_bill_by_billing_cycle(
        self, billing_cycle: str, billing_date: Optional[str] = None, max_page_size: int = DEFAULT_MAX_PAGE_SIZE
    ) -> List[QueryInstanceBillItem]:
        """获取指定账期的实例账单（自动处理分页）

        Args:
            billing_cycle: 账期（格式：YYYY-MM）
            billing_date: 具体账单日期（格式：YYYY-MM-DD）
            max_page_size: 每页最大记录数（默认100）

        Returns:
            合并后的账单项列表

        Raises:
            ValueError: 当账期格式无效时
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
        request = CommonRequest()
        request.set_accept_format("json")
        request.set_domain("business.aliyuncs.com")
        request.set_method("POST")
        request.set_protocol_type("https")
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
            raise ValueError(f"无效账期格式: {billing_cycle}，应为YYYY-MM")

    def _has_more_data(self, next_token: Optional[str]) -> bool:
        return bool(next_token and next_token.strip())

    def fetch_instance_amortized_cost_by_amortization_period(self, billing_cycle: str) -> List[AmortizedItem]:
        """
        获取按分摊周期划分的实例分摊成本

        Args:
            billing_cycle: 账期，格式为YYYY-MM

        Returns:
            AmortizedDealedResponse: 包含分摊成本数据的响应对象

        Raises:
            APIError: 当API请求失败时抛出
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

    def _parse_response(self, response: dict) -> AmortizedResponse:
        try:
            return AmortizedResponse.model_validate(response)
        except ValidationError as e:
            raise InvalidResponseError(message=f"Invalid reponse data format: {str(e)}", response_data=response)

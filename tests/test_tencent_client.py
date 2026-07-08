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

"""Unit tests for TencentCloudClient."""

import json
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from cloud_billing.tencent_cloud.client import DEFAULT_MAX_PAGE_SIZE, TencentCloudClient
from cloud_billing.tencent_cloud.types import (
    AccountBalanceItem,
    BillDetailItem,
    BillResourceSummaryItem,
    BillSummaryByProductItem,
)


class _FakeBillDetailResponse:
    """Stub for the SDK DescribeBillDetail response object."""

    def __init__(self, detail_set: list, total: int = 0, context: str | None = None) -> None:
        self._detail_set = detail_set
        self._total = total
        self._context = context
        self.RequestId = "test-request-id"

    def to_json_string(self) -> str:
        return json.dumps(
            {
                "DetailSet": self._detail_set,
                "Total": self._total,
                "Context": self._context,
                "RequestId": self.RequestId,
            }
        )


class _FakeResourceSummaryResponse:
    """Stub for the SDK DescribeBillResourceSummary response object."""

    def __init__(self, resource_summary_set: list, total: int = 0) -> None:
        self._resource_summary_set = resource_summary_set
        self._total = total
        self.RequestId = "test-request-id"

    def to_json_string(self) -> str:
        return json.dumps(
            {
                "ResourceSummarySet": self._resource_summary_set,
                "Total": self._total,
                "RequestId": self.RequestId,
            }
        )


class _FakeProductSummaryResponse:
    """Stub for the SDK DescribeBillSummaryByProduct response object."""

    def __init__(self, summary_detail: list, total: int = 0) -> None:
        self._summary_detail = summary_detail
        self._total = total
        self.RequestId = "test-request-id"

    def to_json_string(self) -> str:
        return json.dumps(
            {
                "SummaryDetail": self._summary_detail,
                "Total": self._total,
                "RequestId": self.RequestId,
            }
        )


class _FakeAccountBalanceResponse:
    """Stub for the SDK DescribeAccountBalance response object."""

    def __init__(self, balance_data: dict) -> None:
        self._data = {**balance_data, "RequestId": "test-request-id"}

    def to_json_string(self) -> str:
        return json.dumps(self._data)


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def _make_bill_detail_item(instance_id: str = "ins-test001", product: str = "云服务器 CVM") -> dict:
    return {
        "PayerAccountId": "100000123456",
        "OwnerAccountId": "100000123456",
        "ProductName": product,
        "SubProductName": "云服务器CVM-标准型S5",
        "BillingMode": "按量计费",
        "ProjectName": "默认项目",
        "Region": "华南地区（广州）",
        "AvailabilityZone": "广州六区",
        "InstanceId": instance_id,
        "InstanceName": "test-instance",
        "TransactionType": "按量计费小时结",
        "TransactionTime": "2024-06-15 10:00:00",
        "UsageStartTime": "2024-06-15 09:00:00",
        "UsageEndTime": "2024-06-15 10:00:00",
        "ComponentType": "cpu",
        "ComponentName": "CPU",
        "ComponentListPrice": "0.52",
        "ComponentPriceMeasurementUnit": "元/核/小时",
        "ComponentUsage": "2.0",
        "ComponentUsageUnit": "核",
        "UsageDuration": "3600",
        "DurationUnit": "秒",
        "OriginalCost": "0.52",
        "TotalCost": "0.42",
        "Currency": "CNY",
        "Tags": [{"TagKey": "env", "TagValue": "production"}],
    }


def _make_resource_summary_item(instance_id: str = "ins-test001") -> dict:
    return {
        "PayerAccountId": "100000123456",
        "OwnerAccountId": "100000123456",
        "ProductName": "云服务器 CVM",
        "BillingMode": "按量计费",
        "ProjectName": "默认项目",
        "Region": "华南地区（广州）",
        "AvailabilityZone": "广州六区",
        "InstanceId": instance_id,
        "InstanceName": "test-instance",
        "OriginalCost": "372.00",
        "TotalCost": "298.50",
        "Currency": "CNY",
    }


def _make_product_summary_item() -> dict:
    return {
        "ProductName": "云服务器 CVM",
        "ProductCode": "p_cvm",
        "OriginalCost": "1500.00",
        "TotalCost": "1200.50",
        "RealTotalCost": "1200.50",
        "CashPayAmount": "800.00",
        "IncentivePayAmount": "200.00",
        "VoucherPayAmount": "100.00",
        "TransferPayAmount": "100.50",
        "Currency": "CNY",
    }


@pytest.fixture
def client():
    return TencentCloudClient(
        secret_id="test_secret_id",
        secret_key="test_secret_key",
        region="ap-guangzhou",
    )


# ---------------------------------------------------------------------------
# _validate_billing_cycle
# ---------------------------------------------------------------------------
class TestValidateBillingCycle:
    def test_valid_format(self, client):
        client._validate_billing_cycle("2024-06")

    def test_valid_january(self, client):
        client._validate_billing_cycle("2024-01")

    def test_invalid_missing_hyphen(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client._validate_billing_cycle("202406")

    def test_invalid_short_year(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client._validate_billing_cycle("24-06")

    def test_invalid_empty_string(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client._validate_billing_cycle("")

    def test_invalid_single_digit_month(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client._validate_billing_cycle("2024-6")

    def test_invalid_letters(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client._validate_billing_cycle("YYYY-MM")


# ---------------------------------------------------------------------------
# get_credentials
# ---------------------------------------------------------------------------
class TestGetCredentials:
    def test_returns_credentials(self, client):
        creds = client.get_credentials()
        assert creds["SecretId"] == "test_secret_id"
        assert creds["SecretKey"] == "test_secret_key"
        assert creds["Region"] == "ap-guangzhou"


# ---------------------------------------------------------------------------
# _response_to_dict
# ---------------------------------------------------------------------------
class TestResponseToDict:
    def test_converts_response_to_dict(self, client):
        response = _FakeBillDetailResponse(
            detail_set=[_make_bill_detail_item("ins-001")],
            total=1,
        )
        result = client._response_to_dict(response)
        assert result["DetailSet"][0]["InstanceId"] == "ins-001"
        assert result["Total"] == 1


# ---------------------------------------------------------------------------
# describe_bill_detail
# ---------------------------------------------------------------------------
class TestDescribeBillDetail:
    def test_single_page(self, client):
        items = [_make_bill_detail_item("ins-001"), _make_bill_detail_item("ins-002", "云数据库 MySQL")]
        response = _FakeBillDetailResponse(detail_set=items, total=2)
        client._client.DescribeBillDetail = MagicMock(return_value=response)

        result = client.describe_bill_detail("2024-06")
        assert len(result) == 2
        assert isinstance(result[0], BillDetailItem)
        assert result[0].InstanceId == "ins-001"
        assert result[1].ProductName == "云数据库 MySQL"

    def test_multi_page(self, client):
        page1 = [_make_bill_detail_item("ins-001")]
        page2 = [_make_bill_detail_item("ins-002")]
        client._client.DescribeBillDetail = MagicMock(
            side_effect=[
                _FakeBillDetailResponse(detail_set=page1, total=2),
                _FakeBillDetailResponse(detail_set=page2, total=2),
            ]
        )

        result = client.describe_bill_detail("2024-06")
        assert len(result) == 2
        assert result[0].InstanceId == "ins-001"
        assert result[1].InstanceId == "ins-002"

    def test_empty_result(self, client):
        response = _FakeBillDetailResponse(detail_set=[])
        client._client.DescribeBillDetail = MagicMock(return_value=response)

        result = client.describe_bill_detail("2024-06")
        assert result == []

    def test_invalid_month_raises(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client.describe_bill_detail("bad-month")

    def test_with_pay_mode_filter(self, client):
        items = [_make_bill_detail_item("ins-001")]
        response = _FakeBillDetailResponse(detail_set=items, total=1)
        client._client.DescribeBillDetail = MagicMock(return_value=response)

        result = client.describe_bill_detail("2024-06", pay_mode="postPay")
        assert len(result) == 1
        call_args = client._client.DescribeBillDetail.call_args[0][0]
        assert call_args.PayMode == "postPay"

    def test_with_resource_id_filter(self, client):
        items = [_make_bill_detail_item("ins-target")]
        response = _FakeBillDetailResponse(detail_set=items, total=1)
        client._client.DescribeBillDetail = MagicMock(return_value=response)

        result = client.describe_bill_detail("2024-06", resource_id="ins-target")
        assert len(result) == 1
        call_args = client._client.DescribeBillDetail.call_args[0][0]
        assert call_args.ResourceId == "ins-target"

    def test_custom_max_page_size(self, client):
        response = _FakeBillDetailResponse(detail_set=[], total=0)
        client._client.DescribeBillDetail = MagicMock(return_value=response)

        client.describe_bill_detail("2024-06", max_page_size=50)
        call_args = client._client.DescribeBillDetail.call_args[0][0]
        assert call_args.Limit == 50


# ---------------------------------------------------------------------------
# describe_bill_resource_summary
# ---------------------------------------------------------------------------
class TestDescribeBillResourceSummary:
    def test_single_page(self, client):
        items = [_make_resource_summary_item("ins-001")]
        response = _FakeResourceSummaryResponse(resource_summary_set=items, total=1)
        client._client.DescribeBillResourceSummary = MagicMock(return_value=response)

        result = client.describe_bill_resource_summary("2024-06")
        assert len(result) == 1
        assert isinstance(result[0], BillResourceSummaryItem)
        assert result[0].InstanceId == "ins-001"

    def test_multi_page(self, client):
        page1 = [_make_resource_summary_item("ins-page1")]
        page2 = [_make_resource_summary_item("ins-page2")]
        client._client.DescribeBillResourceSummary = MagicMock(
            side_effect=[
                _FakeResourceSummaryResponse(resource_summary_set=page1, total=2),
                _FakeResourceSummaryResponse(resource_summary_set=page2, total=2),
            ]
        )

        result = client.describe_bill_resource_summary("2024-06")
        assert len(result) == 2

    def test_empty_result(self, client):
        response = _FakeResourceSummaryResponse(resource_summary_set=[])
        client._client.DescribeBillResourceSummary = MagicMock(return_value=response)

        result = client.describe_bill_resource_summary("2024-06")
        assert result == []

    def test_invalid_month_raises(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client.describe_bill_resource_summary("invalid")


# ---------------------------------------------------------------------------
# describe_bill_summary_by_product
# ---------------------------------------------------------------------------
class TestDescribeBillSummaryByProduct:
    def test_returns_product_summary(self, client):
        items = [
            _make_product_summary_item(),
            {"ProductName": "云数据库 MySQL", "ProductCode": "p_cdb", "OriginalCost": "500.00",
             "TotalCost": "420.30", "RealTotalCost": "420.30", "CashPayAmount": "300.00",
             "IncentivePayAmount": "50.00", "VoucherPayAmount": "70.30", "TransferPayAmount": "0.00",
             "Currency": "CNY"},
        ]
        response = _FakeProductSummaryResponse(summary_detail=items, total=2)
        client._client.DescribeBillSummaryByProduct = MagicMock(return_value=response)

        result = client.describe_bill_summary_by_product("2024-06")
        assert len(result) == 2
        assert isinstance(result[0], BillSummaryByProductItem)
        assert result[0].ProductName == "云服务器 CVM"
        assert result[1].ProductName == "云数据库 MySQL"

    def test_empty_result(self, client):
        response = _FakeProductSummaryResponse(summary_detail=[])
        client._client.DescribeBillSummaryByProduct = MagicMock(return_value=response)

        result = client.describe_bill_summary_by_product("2024-06")
        assert result == []

    def test_invalid_month_raises(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client.describe_bill_summary_by_product("bad-month")


# ---------------------------------------------------------------------------
# describe_account_balance
# ---------------------------------------------------------------------------
class TestDescribeAccountBalance:
    def test_returns_balance(self, client):
        balance_data = {
            "Balance": 10000.50,
            "CashAccountBalance": 8000.00,
            "CreditBalance": 2000.00,
            "RealBalance": 8500.00,
            "FrozenAmount": 1500.00,
            "AvailableAmount": 7000.00,
            "Currency": "CNY",
        }
        response = _FakeAccountBalanceResponse(balance_data)
        client._client.DescribeAccountBalance = MagicMock(return_value=response)

        result = client.describe_account_balance()
        assert isinstance(result, AccountBalanceItem)
        assert result.Balance == 10000.50
        assert result.CashAccountBalance == 8000.00
        assert result.Currency == "CNY"

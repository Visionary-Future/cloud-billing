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

"""Unit tests for AlibabaCloudClient."""

import json
from unittest.mock import MagicMock, patch

import pytest

from cloud_billing.alibaba_cloud.client import (
    DEFAULT_MAX_PAGE_SIZE,
    AlibabaCloudClient,
    PaginationParams,
)
from cloud_billing.alibaba_cloud.exceptions import APIError, InvalidResponseError
from cloud_billing.alibaba_cloud.types import AmortizedItem, QueryInstanceBillItem


def _make_bill_item(iid: str = "i-bp1234567890", product: str = "ECS") -> dict:
    return {
        "AfterDiscountAmount": 0.0,
        "InstanceSpec": "ecs.g7.xlarge",
        "ProductName": product,
        "InstanceID": iid,
        "BillAccountID": "123456",
        "DeductedByCashCoupons": 0.0,
        "BillingDate": "2025-12-01",
        "ListPriceUnit": "CNY",
        "PaymentAmount": 100.5,
        "ListPrice": "150.0",
        "DeductedByPrepaidCard": 0.0,
        "InvoiceDiscount": 0.0,
        "Item": product,
        "SubscriptionType": "PayAsYouGo",
        "PretaxGrossAmount": 100.5,
        "InstanceConfig": "4C8G",
        "Currency": "CNY",
        "CommodityCode": "ecs",
        "ItemName": product,
        "CostUnit": "",
        "ResourceGroup": "",
        "AdjustAmount": 0.0,
        "BillingType": "0",
        "DeductedByCoupons": 0.0,
        "Usage": "24",
        "ProductDetail": "",
        "ProductCode": "ecs",
        "Zone": "cn-hangzhou-i",
        "ProductType": "ecs",
        "OutstandingAmount": 0.0,
        "BizType": "",
        "BillingItem": product,
        "NickName": "",
        "PipCode": "ecs",
        "IntranetIP": "",
        "ServicePeriodUnit": "Hour",
        "ServicePeriod": "2025-12-01 00:00~2025-12-01 24:00",
        "DeductedByResourcePackage": "",
        "UsageUnit": "h",
        "InternetIP": "",
        "PretaxAmount": 100.5,
        "OwnerID": "123456",
        "BillAccountName": "test-account",
        "Region": "cn-hangzhou",
        "Tag": "",
        "CashAmount": 0.0,
    }


def _make_bill_response(items: list, next_token: str | None = None) -> dict:
    return {
        "Message": "Success",
        "RequestId": "test-request-id",
        "Data": {
            "BillingCycle": "2025-12",
            "TotalCount": len(items),
            "AccountID": "123456",
            "NextToken": next_token,
            "MaxResults": 100,
            "Items": items,
            "AccountName": "test-account",
        },
        "Code": "Success",
        "Success": True,
    }


def _make_amortized_item(instance_id: str = "i-amor-001") -> dict:
    return {
        "CurrentAmortizationPretaxAmount": 100.0,
        "RemainingAmortizationDeductedByCoupons": 0.0,
        "ProductName": "ECS",
        "PreviouslyAmortizedExpenditureAmount": 0.0,
        "InstanceID": instance_id,
        "BillAccountID": 123456,
        "ProductDetailCode": "ecs.g7",
        "PreviouslyAmortizedRoundDownDiscount": 0.0,
        "AmortizationStatus": "Amortized",
        "DeductedByPrepaidCard": 0.0,
        "SplitItemName": "",
        "SubscriptionType": "PayAsYouGo",
        "CurrentAmortizationDeductedByCashCoupons": 0.0,
        "CostUnitCode": "",
        "RemainingAmortizationDeductedByPrepaidCard": 0.0,
        "CostUnit": "",
        "DeductedByCoupons": 0.0,
        "ProductCode": "ecs",
        "BillOwnerID": 123456,
        "BizType": "",
        "PreviouslyAmortizedPretaxAmount": 0.0,
        "IntranetIP": "",
        "CurrentAmortizationPretaxGrossAmount": 100.0,
        "InternetIP": "",
        "RemainingAmortizationExpenditureAmount": 0.0,
        "Region": "cn-hangzhou",
        "RemainingAmortizationInvoiceDiscount": 0.0,
        "PreviouslyAmortizedDeductedByCashCoupons": 0.0,
        "CurrentAmortizationDeductedByCoupons": 0.0,
        "CurrentAmortizationRoundDownDiscount": 0.0,
        "CurrentAmortizationExpenditureAmount": 100.0,
        "RemainingAmortizationRoundDownDiscount": 0.0,
        "PreviouslyAmortizedInvoiceDiscount": 0.0,
        "DeductedByCashCoupons": 0.0,
        "PreviouslyAmortizedDeductedByCoupons": 0.0,
        "RemainingAmortizationDeductedByCashCoupons": 0.0,
        "InvoiceDiscount": 0.0,
        "SplitProductDetail": "",
        "CurrentAmortizationDeductedByPrepaidCard": 0.0,
        "AmortizationPeriod": "2025-12",
        "PretaxGrossAmount": 100.0,
        "PreviouslyAmortizedPretaxGrossAmount": 0.0,
        "ResourceGroup": "",
        "SplitAccountName": "",
        "RoundDownDiscount": 0.0,
        "ProductDetail": "",
        "ConsumePeriod": "2025-12",
        "Zone": "cn-hangzhou-i",
        "BillOwnerName": "",
        "SplitItemID": "",
        "RemainingAmortizationPretaxGrossAmount": 0.0,
        "PretaxAmount": 100.0,
        "CurrentAmortizationInvoiceDiscount": 0.0,
        "ExpenditureAmount": 100.0,
        "RemainingAmortizationPretaxAmount": 0.0,
        "BillAccountName": "test-account",
        "Tag": "",
        "PreviouslyAmortizedDeductedByPrepaidCard": 0.0,
    }


def _make_amortized_response(items: list, next_token: str | None = None) -> dict:
    return {
        "RequestId": "test-request-id",
        "Message": "Success",
        "Data": {
            "TotalCount": len(items),
            "AccountID": "123456",
            "NextToken": next_token,
            "MaxResults": 100,
            "Items": items,
            "AccountName": "test-account",
        },
        "Code": "Success",
        "Success": True,
    }


@pytest.fixture
def client():
    return AlibabaCloudClient(
        access_key_id="test_key_id",
        access_key_secret="test_key_secret",
        region_id="cn-hangzhou",
    )


# ---------------------------------------------------------------------------
# _validate_billing_cycle
# ---------------------------------------------------------------------------
class TestValidateBillingCycle:
    def test_valid_format(self, client):
        client._validate_billing_cycle("2025-12")

    def test_valid_january(self, client):
        client._validate_billing_cycle("2025-01")

    def test_invalid_missing_hyphen(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client._validate_billing_cycle("202512")

    def test_invalid_short_year(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client._validate_billing_cycle("25-12")

    def test_invalid_empty_string(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client._validate_billing_cycle("")

    def test_invalid_single_digit_month(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client._validate_billing_cycle("2025-1")

    def test_invalid_letters(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client._validate_billing_cycle("YYYY-MM")


# ---------------------------------------------------------------------------
# _has_more_data
# ---------------------------------------------------------------------------
class TestHasMoreData:
    def test_none_returns_false(self, client):
        assert client._has_more_data(None) is False

    def test_empty_returns_false(self, client):
        assert client._has_more_data("") is False

    def test_whitespace_returns_false(self, client):
        assert client._has_more_data("   ") is False

    def test_token_returns_true(self, client):
        assert client._has_more_data("next-page-token") is True


# ---------------------------------------------------------------------------
# make_request
# ---------------------------------------------------------------------------
class TestMakeRequest:
    def test_success(self, client):
        expected = {"Code": "Success", "Data": {"Items": []}}
        client.client = MagicMock()
        client.client.do_action_with_exception.return_value = json.dumps(expected)

        result = client.make_request(MagicMock())
        assert result == expected

    def test_json_decode_error(self, client):
        client.client = MagicMock()
        client.client.do_action_with_exception.return_value = "not json{{{"

        with pytest.raises(ValueError, match="Failed to parse response JSON"):
            client.make_request(MagicMock())

    def test_empty_response(self, client):
        client.client = MagicMock()
        client.client.do_action_with_exception.return_value = ""

        with pytest.raises(ValueError, match="Empty or invalid response"):
            client.make_request(MagicMock())


# ---------------------------------------------------------------------------
# fetch_instance_bill_by_billing_cycle
# ---------------------------------------------------------------------------
class TestFetchInstanceBill:
    def test_single_page(self, client):
        items = [_make_bill_item("i-001"), _make_bill_item("i-002", "RDS")]
        client.make_request = MagicMock(return_value=_make_bill_response(items))

        result = client.fetch_instance_bill_by_billing_cycle("2025-12")
        assert len(result) == 2
        assert isinstance(result[0], QueryInstanceBillItem)
        assert result[0].InstanceID == "i-001"
        assert result[1].ProductName == "RDS"

    def test_multi_page(self, client):
        page1 = [_make_bill_item("i-001")]
        page2 = [_make_bill_item("i-002")]
        client.make_request = MagicMock(
            side_effect=[
                _make_bill_response(page1, next_token="token-page2"),
                _make_bill_response(page2),
            ]
        )

        result = client.fetch_instance_bill_by_billing_cycle("2025-12")
        assert len(result) == 2
        assert result[0].InstanceID == "i-001"
        assert result[1].InstanceID == "i-002"

    def test_empty_result(self, client):
        client.make_request = MagicMock(return_value=_make_bill_response([]))

        result = client.fetch_instance_bill_by_billing_cycle("2025-12")
        assert result == []

    def test_invalid_billing_cycle_raises(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client.fetch_instance_bill_by_billing_cycle("bad-cycle")

    def test_with_billing_date(self, client):
        items = [_make_bill_item("i-001")]
        mock_request = MagicMock()
        client._build_bill_request = MagicMock(return_value=mock_request)
        client.make_request = MagicMock(return_value=_make_bill_response(items))

        result = client.fetch_instance_bill_by_billing_cycle("2025-12", billing_date="2025-12-15")
        assert len(result) == 1
        client._build_bill_request.assert_called_once()
        call_kwargs = client._build_bill_request.call_args[1]
        assert call_kwargs["billing_date"] == "2025-12-15"

    def test_default_max_page_size(self, client):
        client._build_bill_request = MagicMock(return_value=MagicMock())
        client.make_request = MagicMock(return_value=_make_bill_response([]))

        client.fetch_instance_bill_by_billing_cycle("2025-12")
        call_pagination = client._build_bill_request.call_args[1]["pagination"]
        assert call_pagination.max_page_size == DEFAULT_MAX_PAGE_SIZE

    def test_custom_max_page_size(self, client):
        client._build_bill_request = MagicMock(return_value=MagicMock())
        client.make_request = MagicMock(return_value=_make_bill_response([]))

        client.fetch_instance_bill_by_billing_cycle("2025-12", max_page_size=50)
        call_pagination = client._build_bill_request.call_args[1]["pagination"]
        assert call_pagination.max_page_size == 50


# ---------------------------------------------------------------------------
# _build_bill_request
# ---------------------------------------------------------------------------
class TestBuildBillRequest:
    def test_basic_request(self, client):
        pagination = PaginationParams(max_page_size=100)
        req = client._build_bill_request("2025-12", billing_date=None, pagination=pagination)

        assert req.get_action_name() == "DescribeInstanceBill"
        assert req.get_domain() == "business.aliyuncs.com"
        # BillingCycle query param is set
        params = req.get_query_params()
        assert params["BillingCycle"] == "2025-12"
        assert params["MaxResults"] == "100"

    def test_request_with_billing_date(self, client):
        pagination = PaginationParams(max_page_size=100)
        req = client._build_bill_request("2025-12", billing_date="2025-12-15", pagination=pagination)

        params = req.get_query_params()
        assert params["BillingDate"] == "2025-12-15"
        assert params["Granularity"] == "DAILY"

    def test_request_with_next_token(self, client):
        pagination = PaginationParams(max_page_size=100, next_token="token-xyz")
        req = client._build_bill_request("2025-12", billing_date=None, pagination=pagination)

        params = req.get_query_params()
        assert params["NextToken"] == "token-xyz"


# ---------------------------------------------------------------------------
# fetch_instance_amortized_cost_by_amortization_period
# ---------------------------------------------------------------------------
class TestFetchAmortizedCost:
    def test_single_page(self, client):
        items = [_make_amortized_item("i-amor-001")]
        client.make_request = MagicMock(return_value=_make_amortized_response(items))

        result = client.fetch_instance_amortized_cost_by_amortization_period("2025-12")
        assert len(result) == 1
        assert isinstance(result[0], AmortizedItem)
        assert result[0].InstanceID == "i-amor-001"
        assert result[0].PretaxAmount == 100.0

    def test_multi_page(self, client):
        page1 = [_make_amortized_item("i-page1")]
        page2 = [_make_amortized_item("i-page2")]
        client.make_request = MagicMock(
            side_effect=[
                _make_amortized_response(page1, next_token="token-next"),
                _make_amortized_response(page2),
            ]
        )

        result = client.fetch_instance_amortized_cost_by_amortization_period("2025-12")
        assert len(result) == 2

    def test_empty_result(self, client):
        client.make_request = MagicMock(return_value=_make_amortized_response([]))

        result = client.fetch_instance_amortized_cost_by_amortization_period("2025-12")
        assert result == []

    def test_invalid_billing_cycle(self, client):
        with pytest.raises(ValueError, match="Invalid billing cycle format"):
            client.fetch_instance_amortized_cost_by_amortization_period("invalid")

    def test_api_error_wraps_exception(self, client):
        client.make_request = MagicMock(side_effect=RuntimeError("connection timeout"))

        with pytest.raises(APIError, match="Failed to fetch amortized cost data"):
            client.fetch_instance_amortized_cost_by_amortization_period("2025-12")


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------
class TestParseResponse:
    def test_valid_response(self, client):
        items = [_make_amortized_item()]
        response = _make_amortized_response(items)
        result = client._parse_response(response)
        assert len(result.Data.Items) == 1

    def test_invalid_response_raises(self, client):
        with pytest.raises(InvalidResponseError):
            client._parse_response({"not": "valid"})


# ---------------------------------------------------------------------------
# get_credentials
# ---------------------------------------------------------------------------
class TestGetCredentials:
    def test_returns_credentials(self, client):
        creds = client.get_credentials()
        assert creds["AccessKeyId"] == "test_key_id"
        assert creds["AccessKeySecret"] == "test_key_secret"
        assert creds["RegionId"] == "cn-hangzhou"

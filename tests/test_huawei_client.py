"""Unit tests for HuaweiCloudClient."""

from unittest.mock import MagicMock, patch

import pytest

from cloud_billing.huawei_cloud.client import HuaweiCloudClient
from cloud_billing.huawei_cloud.types import MonthlyBillItem


def _make_bill_item(bill_cycle: str = "2025-12", consume_amount: float = 100.0) -> dict:
    return {
        "bill_cycle": bill_cycle,
        "consume_amount": consume_amount,
        "cash_amount": 50.0,
        "credit_amount": 0.0,
        "coupon_amount": 10.0,
        "debt_amount": 0.0,
        "flexipurchase_coupon_amount": 0.0,
        "stored_value_card_amount": 40.0,
        "writeoff_amount": 0.0,
        "service_type_code": "hws.service.type.ec2",
        "service_type_name": "弹性云服务器",
        "resource_type_code": "hws.resource.type.vm",
        "resource_type_name": "云主机",
        "customer_id": "cust-001",
        "account_name": "test-account",
        "bill_type": 1,
        "charging_mode": 1,
        "measure_id": 1,
        "official_amount": 200.0,
        "official_discount_amount": 100.0,
        "truncated_amount": 0.0,
    }


def _make_mock_sdk_response(items: list, total_count: int = 1, currency: str = "CNY") -> MagicMock:
    resp = MagicMock()
    resp.to_dict.return_value = {
        "bill_sums": items,
        "total_count": total_count,
        "currency": currency,
    }
    return resp


@pytest.fixture
def client():
    with patch("cloud_billing.huawei_cloud.client.BssClient") as mock_bss_cls:
        mock_bss = MagicMock()
        mock_bss_cls.new_builder.return_value.with_http_config.return_value.with_credentials.return_value.with_endpoint.return_value.build.return_value = (
            mock_bss
        )

        client = HuaweiCloudClient(
            access_key="test-ak",
            secret_key="test-sk",
            domain_id="domain-123",
            region_id="cn-east-3",
        )
        return client


# ---------------------------------------------------------------------------
# __init__ and credentials
# ---------------------------------------------------------------------------
class TestInit:
    def test_stores_credentials(self):
        with patch("cloud_billing.huawei_cloud.client.BssClient"):
            client = HuaweiCloudClient("ak", "sk", "domain-123")
            assert client.access_key == "ak"
            assert client.secret_key == "sk"
            assert client.domain_id == "domain-123"


class TestGetCredentials:
    def test_returns_credentials(self, client):
        creds = client.get_credentials()
        assert creds["AccessKey"] == "test-ak"
        assert creds["SecretKey"] == "test-sk"
        assert creds["DomainId"] == "domain-123"
        assert creds["RegionId"] == "cn-east-3"


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


# ---------------------------------------------------------------------------
# query_monthly_bill_summary
# ---------------------------------------------------------------------------
class TestQueryMonthlyBillSummary:
    def test_single_page(self, client):
        items = [_make_bill_item("2025-12", 100.0)]
        mock_resp = _make_mock_sdk_response(items, total_count=1)
        client._bss_client.show_customer_monthly_sum.return_value = mock_resp

        result, error = client.query_monthly_bill_summary("2025-12")
        assert error is None
        assert len(result) == 1
        assert isinstance(result[0], MonthlyBillItem)
        assert result[0].bill_cycle == "2025-12"
        assert result[0].consume_amount == 100.0

    def test_multi_page(self, client):
        page1_items = [_make_bill_item("2025-12", float(i)) for i in range(100)]
        page2_items = [_make_bill_item("2025-12", float(i + 100)) for i in range(100)]

        mock_resp1 = _make_mock_sdk_response(page1_items, total_count=200)
        mock_resp2 = _make_mock_sdk_response(page2_items, total_count=200)

        client._bss_client.show_customer_monthly_sum.side_effect = [
            mock_resp1,
            mock_resp2,
        ]

        result, error = client.query_monthly_bill_summary("2025-12")
        assert error is None
        assert len(result) == 200

    def test_empty_result(self, client):
        mock_resp = _make_mock_sdk_response([], total_count=0)
        client._bss_client.show_customer_monthly_sum.return_value = mock_resp

        result, error = client.query_monthly_bill_summary("2025-12")
        assert error is None
        assert result == []

    def test_invalid_billing_cycle(self, client):
        result, error = client.query_monthly_bill_summary("bad-cycle")
        assert result is None
        assert error is not None

    def test_sdk_exception(self, client):
        client._bss_client.show_customer_monthly_sum.side_effect = RuntimeError("API error")

        result, error = client.query_monthly_bill_summary("2025-12")
        assert result is None
        assert "API error" in error

    def test_zero_amounts_converted(self, client):
        item = _make_bill_item("2025-12", 0.0)
        item.update({"cash_amount": None, "coupon_amount": "", "credit_amount": None})
        mock_resp = _make_mock_sdk_response([item], total_count=1)
        client._bss_client.show_customer_monthly_sum.return_value = mock_resp

        result, error = client.query_monthly_bill_summary("2025-12")
        assert error is None
        assert result[0].cash_amount == 0.0
        assert result[0].coupon_amount == 0.0


# ---------------------------------------------------------------------------
# _response_to_dict
# ---------------------------------------------------------------------------
class TestResponseToDict:
    def test_with_to_dict_method(self, client):
        items = [_make_bill_item()]
        mock_resp = _make_mock_sdk_response(items, total_count=5, currency="USD")
        result = client._response_to_dict(mock_resp)
        assert len(result["bill_sums"]) == 1
        assert result["total_count"] == 5
        assert result["currency"] == "USD"

    def test_without_to_dict_fallback(self, client):
        mock_resp = MagicMock()
        del mock_resp.to_dict
        mock_resp.total_count = 10
        mock_resp.currency = "CNY"
        mock_resp.bill_sums = []

        result = client._response_to_dict(mock_resp)
        assert result["total_count"] == 0
        assert result["currency"] == "CNY"

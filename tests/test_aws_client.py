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

"""Unit tests for AWSCloudClient."""

from unittest.mock import MagicMock, patch

import pytest

from cloud_billing.aws_cloud.client import AWSCloudClient
from cloud_billing.aws_cloud.types import ResultByTime


def _make_result_by_time(start: str = "2025-01-01", end: str = "2025-02-01", estimated: bool = False) -> dict:
    return {
        "TimePeriod": {"Start": start, "End": end},
        "Total": {"UnblendedCost": {"Amount": "123.45", "Unit": "USD"}},
        "Groups": [],
        "Estimated": estimated,
    }


def _make_cost_response(results: list, next_token: str | None = None) -> dict:
    return {
        "ResultsByTime": results,
        "NextPageToken": next_token,
    }


@pytest.fixture
def client():
    with patch("boto3.Session"), patch("boto3.Session.client"):
        client = AWSCloudClient(
            access_key_id="AKIATEST",
            secret_access_key="test-secret",
            region_name="us-east-1",
        )
        client._ce_client = MagicMock()
        return client


# ---------------------------------------------------------------------------
# __init__ and credentials
# ---------------------------------------------------------------------------
class TestInit:
    def test_creates_boto3_session(self):
        with patch("boto3.Session") as mock_session:
            AWSCloudClient("AKIATEST", "test-secret", "us-east-1")
            mock_session.assert_called_once_with(
                aws_access_key_id="AKIATEST",
                aws_secret_access_key="test-secret",
            )

    def test_ce_client_uses_us_east_1(self):
        with patch("boto3.Session") as mock_session:
            mock_session_instance = mock_session.return_value
            AWSCloudClient("AKIATEST", "test-secret", "ap-southeast-1")
            mock_session_instance.client.assert_called_once_with("ce", region_name="us-east-1")


class TestGetCredentials:
    def test_returns_credentials(self, client):
        creds = client.get_credentials()
        assert creds["AccessKeyId"] == "AKIATEST"
        assert creds["SecretAccessKey"] == "test-secret"
        assert creds["RegionName"] == "us-east-1"


# ---------------------------------------------------------------------------
# _validate_time_period
# ---------------------------------------------------------------------------
class TestValidateTimePeriod:
    def test_valid_dates(self, client):
        client._validate_time_period("2025-01-01", "2025-01-31")

    def test_invalid_start_format(self, client):
        with pytest.raises(ValueError, match="Invalid start date format"):
            client._validate_time_period("20250101", "2025-01-31")

    def test_invalid_end_format(self, client):
        with pytest.raises(ValueError, match="Invalid end date format"):
            client._validate_time_period("2025-01-01", "20250131")

    def test_start_after_end(self, client):
        with pytest.raises(ValueError, match="must be before end date"):
            client._validate_time_period("2025-12-31", "2025-01-01")

    def test_start_equals_end(self, client):
        with pytest.raises(ValueError, match="must be before end date"):
            client._validate_time_period("2025-01-15", "2025-01-15")


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
# get_cost_and_usage
# ---------------------------------------------------------------------------
class TestGetCostAndUsage:
    def test_single_page(self, client):
        items = [_make_result_by_time("2025-01-01", "2025-02-01")]
        client._ce_client.get_cost_and_usage.return_value = _make_cost_response(items)

        result = client.get_cost_and_usage({"Start": "2025-01-01", "End": "2025-03-01"})
        assert len(result) == 1
        assert isinstance(result[0], ResultByTime)
        assert result[0].TimePeriod["Start"] == "2025-01-01"

    def test_multi_page(self, client):
        page1 = [_make_result_by_time("2025-01-01", "2025-02-01")]
        page2 = [_make_result_by_time("2025-02-01", "2025-03-01")]
        client._ce_client.get_cost_and_usage.side_effect = [
            _make_cost_response(page1, next_token="token2"),
            _make_cost_response(page2),
        ]

        result = client.get_cost_and_usage({"Start": "2025-01-01", "End": "2025-03-01"})
        assert len(result) == 2
        assert result[1].TimePeriod["Start"] == "2025-02-01"

    def test_empty_result(self, client):
        client._ce_client.get_cost_and_usage.return_value = _make_cost_response([])

        result = client.get_cost_and_usage({"Start": "2025-01-01", "End": "2025-03-01"})
        assert result == []

    def test_invalid_time_period_raises(self, client):
        with pytest.raises(ValueError, match="Invalid start date format"):
            client.get_cost_and_usage({"Start": "bad", "End": "2025-03-01"})

    def test_default_metrics(self, client):
        client._ce_client.get_cost_and_usage.return_value = _make_cost_response([])

        client.get_cost_and_usage({"Start": "2025-01-01", "End": "2025-03-01"})
        call_args = client._ce_client.get_cost_and_usage.call_args[1]
        assert call_args["Metrics"] == ["UnblendedCost"]

    def test_custom_metrics(self, client):
        client._ce_client.get_cost_and_usage.return_value = _make_cost_response([])

        client.get_cost_and_usage(
            {"Start": "2025-01-01", "End": "2025-03-01"},
            metrics=["AmortizedCost", "BlendedCost"],
        )
        call_args = client._ce_client.get_cost_and_usage.call_args[1]
        assert call_args["Metrics"] == ["AmortizedCost", "BlendedCost"]

    def test_with_group_by(self, client):
        client._ce_client.get_cost_and_usage.return_value = _make_cost_response([])
        group_by = [{"Type": "DIMENSION", "Key": "SERVICE"}]

        client.get_cost_and_usage(
            {"Start": "2025-01-01", "End": "2025-03-01"},
            group_by=group_by,
        )
        call_args = client._ce_client.get_cost_and_usage.call_args[1]
        assert call_args["GroupBy"] == group_by

    def test_with_filter(self, client):
        client._ce_client.get_cost_and_usage.return_value = _make_cost_response([])
        filter_expr = {"Dimensions": {"Key": "SERVICE", "Values": ["Amazon EC2"]}}

        client.get_cost_and_usage(
            {"Start": "2025-01-01", "End": "2025-03-01"},
            filter_expression=filter_expr,
        )
        call_args = client._ce_client.get_cost_and_usage.call_args[1]
        assert call_args["Filter"] == filter_expr

    def test_with_estimated_data(self, client):
        items = [_make_result_by_time("2025-05-01", "2025-06-01", estimated=True)]
        client._ce_client.get_cost_and_usage.return_value = _make_cost_response(items)

        result = client.get_cost_and_usage({"Start": "2025-05-01", "End": "2025-06-01"})
        assert result[0].Estimated is True

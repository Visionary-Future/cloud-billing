"""Unit tests for AzureCloudClient."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests
from requests_toolbelt.multipart import encoder

from cloud_billing.azure_cloud.client import AzureCloudClient
from cloud_billing.azure_cloud.types import BillingRecord


@pytest.fixture
def client():
    return AzureCloudClient(
        tenant_id="test-tenant",
        client_id="test-client",
        client_secret="test-secret",
    )


# ---------------------------------------------------------------------------
# _prepare_auth_form_data
# ---------------------------------------------------------------------------
class TestPrepareAuthFormData:
    def test_creates_multipart_encoder(self, client):
        form = client._prepare_auth_form_data()
        assert isinstance(form, encoder.MultipartEncoder)
        body = form.to_string()
        assert b"test-client" in body
        assert b"test-secret" in body
        assert b"client_credentials" in body


# ---------------------------------------------------------------------------
# _validate_token_response
# ---------------------------------------------------------------------------
class TestValidateTokenResponse:
    def test_success(self, client):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"access_token": "tok-abc123"}

        token, error = client._validate_token_response(resp)
        assert token == "tok-abc123"
        assert error is None

    def test_http_error(self, client):
        resp = MagicMock()
        resp.status_code = 401
        resp.json.return_value = {"error": "unauthorized"}

        token, error = client._validate_token_response(resp)
        assert token is None
        assert "401" in error

    def test_missing_token_in_response(self, client):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"no_token_here": True}

        token, error = client._validate_token_response(resp)
        assert token is None
        assert "access_token not found" in error

    def test_non_json_response(self, client):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = json.JSONDecodeError("bad", "{", 0)

        token, error = client._validate_token_response(resp)
        assert token is None
        assert "not valid JSON" in error

    def test_unexpected_exception_during_parse(self, client):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = RuntimeError("internal boom")

        token, error = client._validate_token_response(resp)
        assert token is None
        assert "Error parsing response" in error


# ---------------------------------------------------------------------------
# get_access_token
# ---------------------------------------------------------------------------
class TestGetAccessToken:
    def test_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access_token": "tok-xyz"}

        with patch("cloud_billing.azure_cloud.client.requests.post", return_value=mock_resp):
            token, error = client.get_access_token()

        assert token == "tok-xyz"
        assert error is None
        assert client._current_token == "tok-xyz"

    def test_http_error(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 403

        with patch("cloud_billing.azure_cloud.client.requests.post", return_value=mock_resp):
            token, error = client.get_access_token()

        assert token is None
        assert "403" in error
        assert client._current_token is None

    def test_request_exception(self, client):
        with patch(
            "cloud_billing.azure_cloud.client.requests.post",
            side_effect=requests.exceptions.ConnectionError("no network"),
        ):
            token, error = client.get_access_token()

        assert token is None
        assert "no network" in error


# ---------------------------------------------------------------------------
# refresh_token
# ---------------------------------------------------------------------------
class TestRefreshToken:
    def test_refresh_delegates_to_get_token(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access_token": "refreshed-tok"}

        with patch("cloud_billing.azure_cloud.client.requests.post", return_value=mock_resp):
            token, error = client.refresh_token()

        assert token == "refreshed-tok"
        assert error is None


# ---------------------------------------------------------------------------
# _build_billing_request_url
# ---------------------------------------------------------------------------
class TestBuildBillingRequestUrl:
    def test_includes_account_id_and_api_version(self, client):
        url = client._build_billing_request_url("acc-123")
        assert "acc-123" in url
        assert "api-version=2023-08-01" in url


# ---------------------------------------------------------------------------
# get_ri_location
# ---------------------------------------------------------------------------
class TestGetRiLocation:
    def test_success(self, client):
        client._current_token = "tok-location"
        mock_resp = MagicMock()
        mock_resp.status_code = 202
        mock_resp.headers = {"Location": "https://azure.cn/poll/abc"}

        with patch.object(client.session, "post", return_value=mock_resp):
            location, error = client.get_ri_location("acc-123", "2025-12-01", "2025-12-31", "ActualCost")

        assert location == "https://azure.cn/poll/abc"
        assert error is None

    def test_no_token_returns_error(self, client):
        client._current_token = None
        location, error = client.get_ri_location("acc-123", "2025-12-01", "2025-12-31", "ActualCost")
        assert location is None
        assert "No valid access token" in error

    def test_http_error(self, client):
        client._current_token = "tok-bad"
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"error": {"message": "bad request"}}

        with patch.object(client.session, "post", return_value=mock_resp):
            location, error = client.get_ri_location("acc-123", "2025-12-01", "2025-12-31", "ActualCost")

        assert location is None
        assert "400" in error

    def test_202_but_no_location_header(self, client):
        client._current_token = "tok-noloc"
        mock_resp = MagicMock()
        mock_resp.status_code = 202
        mock_resp.headers = {}

        with patch.object(client.session, "post", return_value=mock_resp):
            location, error = client.get_ri_location("acc-123", "2025-12-01", "2025-12-31", "ActualCost")

        assert location is None
        assert "Location header not found" in error

    def test_request_exception(self, client):
        client._current_token = "tok-exc"
        with patch.object(client.session, "post", side_effect=requests.exceptions.ConnectionError("timeout")):
            location, error = client.get_ri_location("acc-123", "2025-12-01", "2025-12-31", "ActualCost")

        assert location is None
        assert "timeout" in error


# ---------------------------------------------------------------------------
# check_ri_report_once
# ---------------------------------------------------------------------------
class TestCheckRiReportOnce:
    def test_no_token(self, client):
        client._current_token = None
        status, csv_url, error = client.check_ri_report_once("https://poll.url")
        assert status == "error"
        assert "No valid access token" in error

    def test_pending_202(self, client):
        client._current_token = "tok-pend"
        mock_resp = MagicMock()
        mock_resp.status_code = 202

        with patch.object(client.session, "get", return_value=mock_resp):
            status, csv_url, error = client.check_ri_report_once("https://poll.url")

        assert status == "pending"
        assert csv_url is None
        assert error is None

    def test_completed_with_csv_url(self, client):
        client._current_token = "tok-done"
        blob = json.dumps(
            {
                "status": "Completed",
                "manifest": {"blobs": [{"blobLink": "https://storage.cn/csv/123.csv"}]},
            }
        )
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = blob
        mock_resp.json.return_value = json.loads(blob)

        with patch.object(client.session, "get", return_value=mock_resp):
            status, csv_url, error = client.check_ri_report_once("https://poll.url")

        assert status == "completed"
        assert csv_url == "https://storage.cn/csv/123.csv"
        assert error is None

    def test_completed_but_no_blobs(self, client):
        client._current_token = "tok-noblob"
        blob = json.dumps({"status": "Completed", "manifest": {"blobs": []}})
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = blob
        mock_resp.json.return_value = json.loads(blob)

        with patch.object(client.session, "get", return_value=mock_resp):
            status, csv_url, error = client.check_ri_report_once("https://poll.url")

        assert status == "error"
        assert "no CSV link" in error

    def test_200_empty_body_treated_as_pending(self, client):
        client._current_token = "tok-empty"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = ""

        with patch.object(client.session, "get", return_value=mock_resp):
            status, csv_url, error = client.check_ri_report_once("https://poll.url")

        assert status == "pending"
        assert error is None

    def test_unexpected_http_status(self, client):
        client._current_token = "tok-500"
        mock_resp = MagicMock()
        mock_resp.status_code = 500

        with patch.object(client.session, "get", return_value=mock_resp):
            status, csv_url, error = client.check_ri_report_once("https://poll.url")

        assert status == "error"
        assert "500" in error

    def test_request_exception(self, client):
        client._current_token = "tok-exc"
        with patch.object(client.session, "get", side_effect=requests.exceptions.ConnectionError("refused")):
            status, csv_url, error = client.check_ri_report_once("https://poll.url")

        assert status == "error"
        assert "refused" in error


# ---------------------------------------------------------------------------
# get_ri_csv_url
# ---------------------------------------------------------------------------
class TestGetRiCsvUrl:
    def test_success_first_poll(self, client):
        client._current_token = "tok-csv"
        blob = json.dumps(
            {
                "status": "Completed",
                "manifest": {"blobs": [{"blobLink": "https://csv.url/report.csv"}]},
            }
        )
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = blob
        mock_resp.json.return_value = json.loads(blob)

        with patch.object(client.session, "get", return_value=mock_resp):
            csv_url, error = client.get_ri_csv_url("https://poll.url", max_retries=1)

        assert csv_url == "https://csv.url/report.csv"
        assert error is None

    def test_no_token(self, client):
        client._current_token = None
        csv_url, error = client.get_ri_csv_url("https://poll.url")
        assert csv_url is None
        assert "No valid access token" in error

    def test_exceeds_max_retries(self, client):
        """get_ri_csv_url only sleeps+retries on non-200; 200 with non-Completed returns immediately.
        Mock 202 to exercise the retry loop."""
        client._current_token = "tok-retry"
        mock_resp = MagicMock()
        mock_resp.status_code = 202

        with patch.object(client.session, "get", return_value=mock_resp), patch("time.sleep", return_value=None):
            csv_url, error = client.get_ri_csv_url("https://poll.url", max_retries=3)

        assert csv_url is None
        assert "Exceeded maximum retries" in error


# ---------------------------------------------------------------------------
# download_ri_csv
# ---------------------------------------------------------------------------
class TestDownloadRiCsv:
    def test_success(self, client):
        client._current_token = "tok-dl"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"col1,col2\nval1,val2"

        with patch.object(client.session, "get", return_value=mock_resp):
            content, error = client.download_ri_csv("https://csv.url/report.csv")

        assert content == b"col1,col2\nval1,val2"
        assert error is None

    def test_no_token(self, client):
        client._current_token = None
        content, error = client.download_ri_csv("https://csv.url/report.csv")
        assert content is None
        assert "No valid access token" in error

    def test_http_error(self, client):
        client._current_token = "tok-dl"
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = {}

        with patch.object(client.session, "get", return_value=mock_resp):
            content, error = client.download_ri_csv("https://csv.url/report.csv")

        assert content is None
        assert "404" in error


# ---------------------------------------------------------------------------
# _parse_blob_response
# ---------------------------------------------------------------------------
class TestParseBlobResponse:
    def test_valid(self, client):
        blob = json.dumps({"status": "Completed", "manifest": {"blobs": [{"blobLink": "link"}]}})
        info = client._parse_blob_response(blob)
        assert info.status == "Completed"
        assert info.manifest["blobs"][0]["blobLink"] == "link"

    def test_invalid_json(self, client):
        with pytest.raises(ValueError, match="Failed to parse JSON response"):
            client._parse_blob_response("not json")

    def test_missing_fields(self, client):
        info = client._parse_blob_response("{}")
        assert info.status == ""
        assert info.manifest == {}


# ---------------------------------------------------------------------------
# get_ri_csv_as_json
# ---------------------------------------------------------------------------
def _build_csv_row(**overrides) -> str:
    """Build a valid CSV with all BillingRecord required fields populated."""
    fields = BillingRecord.model_fields
    defaults = {}
    for name, f in fields.items():
        if f.is_required():
            annotation = f.annotation
            if annotation is str:
                defaults[name] = "-"
            elif annotation is float:
                defaults[name] = "0.0"
            else:
                defaults[name] = "-"
        else:
            defaults[name] = ""
    # Override key fields for recognisable values
    defaults.update(
        invoiceId="INV001",
        billingAccountId="ACC001",
        billingAccountName="Test Account",
        billingProfileId="BP001",
        billingProfileName="Test Profile",
        invoiceSectionId="IS001",
        invoiceSectionName="Test Section",
        billingPeriodEndDate="12/31/2025",
        billingPeriodStartDate="12/01/2025",
        date="12/15/2025",
        chargeType="Usage",
        billingCurrency="CNY",
        pricingCurrency="USD",
        costInBillingCurrency="1050.0",
        costInUsd="1050.0",
        paygCostInBillingCurrency="0.0",
        paygCostInUsd="0.0",
        provider="Azure",
    )
    defaults.update(overrides)

    header = ",".join(defaults.keys())
    row = ",".join(str(defaults[k]) for k in defaults.keys())
    return f"{header}\n{row}\n"


class TestGetRiCsvAsJson:
    def test_yields_parsed_records(self, client):
        client._current_token = "tok-json"
        blob = json.dumps(
            {
                "status": "Completed",
                "manifest": {"blobs": [{"blobLink": "https://csv.url/r.csv"}]},
            }
        )
        mock_blob = MagicMock()
        mock_blob.status_code = 200
        mock_blob.text = blob
        mock_blob.json.return_value = json.loads(blob)

        csv_bytes = _build_csv_row().encode("utf-8")
        mock_csv = MagicMock()
        mock_csv.status_code = 200
        mock_csv.content = csv_bytes

        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = [mock_blob, mock_csv]
            results = list(client.get_ri_csv_as_json("https://poll.url"))

        assert len(results) == 1
        record, error = results[0]
        assert error is None
        assert isinstance(record, BillingRecord)
        assert record.invoiceId == "INV001"

    def test_csv_url_failure_yields_error(self, client):
        client._current_token = "tok-fail"

        with patch.object(client.session, "get") as mock_get:
            mock_get.return_value.status_code = 500
            mock_get.return_value.text = "error"
            # Mock the polling endpoint to fail too
            mock_get.return_value.json.return_value = {}

            # Override get_ri_csv_url to return an error
            with patch.object(client, "get_ri_csv_url", return_value=(None, "Failed")):
                results = list(client.get_ri_csv_as_json("https://poll.url"))

        assert len(results) == 1
        _, error = results[0]
        assert "Failed" in error


# ---------------------------------------------------------------------------
# get_ri_report
# ---------------------------------------------------------------------------
class TestGetRiReport:
    def test_success(self, client):
        client._current_token = "tok-report"
        expected = {"status": "Completed", "manifest": {}}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = expected

        with patch.object(client.session, "get", return_value=mock_resp):
            data, error = client.get_ri_report("https://poll.url")

        assert data == expected
        assert error is None

    def test_202_still_generating(self, client):
        client._current_token = "tok-202"
        mock_resp = MagicMock()
        mock_resp.status_code = 202

        with patch.object(client.session, "get", return_value=mock_resp):
            data, error = client.get_ri_report("https://poll.url")

        assert data is None
        assert "still being generated" in error

    def test_non_json_200(self, client):
        client._current_token = "tok-badjson"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = json.JSONDecodeError("bad", "{", 0)

        with patch.object(client.session, "get", return_value=mock_resp):
            data, error = client.get_ri_report("https://poll.url")

        assert data is None
        assert "Failed to parse" in error

    def test_no_token(self, client):
        client._current_token = None
        data, error = client.get_ri_report("https://poll.url")
        assert data is None
        assert "No valid access token" in error

    def test_http_error_with_details(self, client):
        client._current_token = "tok-err"
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"error": {"message": "bad"}}

        with patch.object(client.session, "get", return_value=mock_resp):
            data, error = client.get_ri_report("https://poll.url")

        assert data is None
        assert "400" in error

    def test_request_exception(self, client):
        client._current_token = "tok-exc"
        with patch.object(client.session, "get", side_effect=requests.exceptions.ConnectionError("refused")):
            data, error = client.get_ri_report("https://poll.url")

        assert data is None
        assert "refused" in error


# ---------------------------------------------------------------------------
# Additional error-path tests for get_ri_csv_url
# ---------------------------------------------------------------------------
class TestGetRiCsvUrl:
    def test_no_token(self, client):
        client._current_token = None
        csv_url, error = client.get_ri_csv_url("https://poll.url")
        assert csv_url is None
        assert "No valid access token" in error

    def test_request_exception(self, client):
        client._current_token = "tok-exc"
        with patch.object(client.session, "get", side_effect=requests.exceptions.ConnectionError("timeout")):
            csv_url, error = client.get_ri_csv_url("https://poll.url", max_retries=1)

        assert csv_url is None
        assert "timeout" in error

    def test_parse_error_from_blob(self, client):
        client._current_token = "tok-parse"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "not json"

        with patch.object(client.session, "get", return_value=mock_resp):
            csv_url, error = client.get_ri_csv_url("https://poll.url", max_retries=1)

        assert csv_url is None
        assert "Error parsing response" in error

    def test_completed_but_no_blobs(self, client):
        client._current_token = "tok-noblob"
        blob = json.dumps({"status": "Completed", "manifest": {"blobs": []}})
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = blob
        mock_resp.json.return_value = json.loads(blob)

        with patch.object(client.session, "get", return_value=mock_resp):
            csv_url, error = client.get_ri_csv_url("https://poll.url", max_retries=1)

        assert csv_url is None
        assert "No valid CSV download link" in error


# ---------------------------------------------------------------------------
# Additional error-path tests for download_ri_csv
# ---------------------------------------------------------------------------
class TestDownloadRiCsvErrors:
    def test_request_exception(self, client):
        client._current_token = "tok-exc"
        with patch.object(client.session, "get", side_effect=requests.exceptions.ConnectionError("timeout")):
            content, error = client.download_ri_csv("https://csv.url")

        assert content is None
        assert "timeout" in error

    def test_generic_exception(self, client):
        client._current_token = "tok-exc"
        with patch.object(client.session, "get", side_effect=RuntimeError("unexpected")):
            content, error = client.download_ri_csv("https://csv.url")

        assert content is None
        assert "unexpected" in error

    def test_http_error_with_json_details(self, client):
        client._current_token = "tok-err"
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.json.return_value = {"error": "forbidden"}

        with patch.object(client.session, "get", return_value=mock_resp):
            content, error = client.download_ri_csv("https://csv.url")

        assert content is None
        assert "403" in error


# ---------------------------------------------------------------------------
# Additional error-path tests for get_ri_location
# ---------------------------------------------------------------------------
class TestGetRiLocationErrors:
    def test_request_exception(self, client):
        client._current_token = "tok-exc"
        with patch.object(client.session, "post", side_effect=requests.exceptions.ConnectionError("no conn")):
            location, error = client.get_ri_location("acc", "2025-12-01", "2025-12-31", "ActualCost")

        assert location is None
        assert "no conn" in error

    def test_generic_exception(self, client):
        client._current_token = "tok-exc"
        with patch.object(client.session, "post", side_effect=RuntimeError("internal")):
            location, error = client.get_ri_location("acc", "2025-12-01", "2025-12-31", "ActualCost")

        assert location is None
        assert "internal" in error

    def test_http_error_drops_json_parse(self, client):
        """When error response is not valid JSON, the code still reports the status code."""
        client._current_token = "tok-err"
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.side_effect = json.JSONDecodeError("bad", "{", 0)

        with patch.object(client.session, "post", return_value=mock_resp):
            location, error = client.get_ri_location("acc", "2025-12-01", "2025-12-31", "ActualCost")

        assert location is None
        assert "400" in error


# ---------------------------------------------------------------------------
# Additional error-path for get_access_token
# ---------------------------------------------------------------------------
class TestGetAccessTokenErrors:
    def test_generic_exception(self, client):
        """Cover the try/except Exception in get_access_token."""
        with patch("cloud_billing.azure_cloud.client.requests.post") as mock_post:
            mock_post.side_effect = RuntimeError("something unexpected")

            token, error = client.get_access_token()

        assert token is None
        assert "Unknown error" in error or "unexpected" in error


# ---------------------------------------------------------------------------
# Additional edge cases for check_ri_report_once
# ---------------------------------------------------------------------------
class TestCheckRiReportOnceErrors:
    def test_generic_exception(self, client):
        client._current_token = "tok-exc"
        with patch.object(client.session, "get", side_effect=RuntimeError("boom")):
            status, csv_url, error = client.check_ri_report_once("https://poll.url")

        assert status == "error"
        assert "boom" in error or "Unknown error" in error


# ---------------------------------------------------------------------------
# Additional edge cases for get_ri_csv_as_json
# ---------------------------------------------------------------------------
class TestGetRiCsvAsJsonErrors:
    def test_decode_error(self, client):
        client._current_token = "tok-decode"
        with patch.object(client, "get_ri_csv_url", return_value=("https://fake.url", None)):
            with patch.object(client, "download_ri_csv", return_value=(b"\x80\x81invalid-utf8", None)):
                results = list(client.get_ri_csv_as_json("https://poll.url"))
                assert len(results) == 1
                _, error = results[0]
                assert "CSV decoding failed" in error

    def test_download_error(self, client):
        client._current_token = "tok-dl"
        with patch.object(client, "get_ri_csv_url", return_value=("https://fake.url", None)):
            with patch.object(client, "download_ri_csv", return_value=(None, "Download error")):
                results = list(client.get_ri_csv_as_json("https://poll.url"))
                assert len(results) == 1
                _, error = results[0]
                assert "Download error" in error

    def test_empty_csv_content(self, client):
        client._current_token = "tok-empty"
        with patch.object(client, "get_ri_csv_url", return_value=("https://fake.url", None)):
            with patch.object(client, "download_ri_csv", return_value=(b"", None)):
                results = list(client.get_ri_csv_as_json("https://poll.url"))
                assert len(results) == 1
                _, error = results[0]
                assert "empty" in error.lower()

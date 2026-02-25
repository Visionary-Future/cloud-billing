import csv
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import requests
from requests_toolbelt.multipart import encoder

from .types import BillingRecord


@dataclass
class BlobInfo:
    """Blob info data structure."""

    status: str
    manifest: Dict[str, Any]


@dataclass
class RiUrlRequest:
    """Request parameters for the RI billing URL."""

    metric: str
    time_period: Dict[str, str]


class AzureCloudClient:

    TOKEN_URL_TEMPLATE = "https://login.partner.microsoftonline.cn/{tenant_id}/oauth2/token?api-version=1.0"
    AUTH_RESOURCE = "https://management.chinacloudapi.cn"

    BILLING_API_VERSION = "2023-08-01"
    BILLING_BASE_URL = "https://management.chinacloudapi.cn/providers/Microsoft.Billing/billingAccounts/{}/providers/Microsoft.CostManagement/generateCostDetailsReport"
    POLLING_INTERVAL = 30

    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        """
        Initialize the Azure Cloud client.

        :param tenant_id: Azure tenant ID.
        :param client_id: Application (client) ID.
        :param client_secret: Client secret.
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = requests.Session()
        self._current_token = None

    def _prepare_auth_form_data(self) -> encoder.MultipartEncoder:
        """Prepare the multipart form data required for authentication."""
        return encoder.MultipartEncoder(
            fields={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "Resource": self.AUTH_RESOURCE,
            }
        )

    def _validate_token_response(self, response: requests.Response) -> Tuple[Optional[str], Optional[str]]:
        """Validate and parse the token response."""
        if response.status_code != 200:
            error_msg = f"HTTP request failed with status code: {response.status_code}"
            return None, error_msg

        try:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                return None, "access_token not found in response"
            return access_token, None
        except json.JSONDecodeError:
            return None, "Response is not valid JSON"
        except Exception as e:
            return None, f"Error parsing response: {str(e)}"

    def get_access_token(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Retrieve an Azure access token.

        :return: Tuple (access_token, error).
                 Returns (token, None) on success.
                 Returns (None, error_message) on failure.
        """
        try:
            token_url = self.TOKEN_URL_TEMPLATE.format(tenant_id=self.tenant_id)
            form = self._prepare_auth_form_data()

            headers = {"Content-Type": form.content_type}
            response = requests.post(token_url, data=form, headers=headers)

            token, error = self._validate_token_response(response)
            if not error:
                self._current_token = token
            return token, error
        except requests.exceptions.RequestException as e:
            return None, f"Request failed: {str(e)}"
        except Exception as e:
            return None, f"Unknown error: {str(e)}"

    def refresh_token(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Refresh the access token.

        :return: Tuple (access_token, error).
        """
        return self.get_access_token()

    def _build_billing_request_url(self, billing_account_id: str) -> str:
        """Build the billing report request URL."""
        return self.BILLING_BASE_URL.format(billing_account_id) + f"?api-version={self.BILLING_API_VERSION}"

    def _prepare_billing_request_params(self, start_date: str, end_date: str, metric: str) -> Dict[str, Any]:
        """Prepare the billing report request parameters."""
        return {"metric": metric, "timePeriod": {"start": start_date, "end": end_date}}

    def get_ri_location(
        self, billing_account_id: str, start_date: str, end_date: str, metric: str, token: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Request the RI billing report and return the polling location URL.

        :param billing_account_id: Billing account ID.
        :param start_date: Start date (YYYY-MM-DD).
        :param end_date: End date (YYYY-MM-DD).
        :param metric: Cost metric (e.g. ActualCost).
        :param token: Access token (optional; cached token is used if not provided).
        :return: Tuple (location_url, error).
        """
        use_token = token if token else self._current_token
        if not use_token:
            return None, "No valid access token provided"

        try:
            url = self._build_billing_request_url(billing_account_id)
            params = self._prepare_billing_request_params(start_date, end_date, metric)

            headers = {"Authorization": f"Bearer {use_token}", "Content-Type": "application/json"}

            response = self.session.post(url, headers=headers, json=params)

            if response.status_code == 202:
                location = response.headers.get("Location")
                if location:
                    return location, None
                return None, "Location header not found in response"
            else:
                error_msg = f"Request failed with status code: {response.status_code}"
                try:
                    error_details = response.json()
                    error_msg += f", details: {error_details}"
                except:
                    pass
                return None, error_msg

        except requests.exceptions.RequestException as e:
            print(e)
            return None, f"Request exception: {str(e)}"
        except Exception as e:
            return None, f"Error processing request: {str(e)}"

    def get_ri_report(self, location_url: str, token: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Fetch the RI billing report data.

        :param location_url: Polling location URL obtained from get_ri_location.
        :param token: Access token (optional).
        :return: Tuple (report_data, error).
        """
        use_token = token if token else self._current_token
        if not use_token:
            return None, "No valid access token provided"

        try:
            headers = {"Authorization": f"Bearer {use_token}"}
            response = self.session.get(location_url, headers=headers, timeout=20)

            if response.status_code == 200:
                try:
                    return response.json(), None
                except json.JSONDecodeError:
                    return None, "Failed to parse response JSON"
            elif response.status_code == 202:
                return None, "Report is still being generated, please retry later"
            else:
                error_msg = f"Failed to fetch report, status code: {response.status_code}"
                try:
                    error_details = response.json()
                    error_msg += f", details: {error_details}"
                except:
                    pass
                return None, error_msg

        except requests.exceptions.RequestException as e:
            return None, f"Request exception: {str(e)}"
        except Exception as e:
            return None, f"Error processing request: {str(e)}"

    def check_ri_report_once(
        self, location_url: str, token: Optional[str] = None
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Single non-blocking poll of the RI billing report status.

        Unlike get_ri_csv_url which blocks for up to 300 seconds internally,
        this method makes exactly one HTTP request and returns immediately.
        Intended to be called repeatedly by the client (e.g., a browser polling
        every 10 seconds) rather than looping server-side.

        :param location_url: Polling location URL obtained from get_ri_location.
        :param token: Access token (optional; cached token is used if not provided).
        :return: Tuple (status, csv_url_or_None, error_or_None).
                 status is one of: "pending", "completed", "error".
                 csv_url is set only when status == "completed".
        """
        use_token = token if token else self._current_token
        if not use_token:
            return "error", None, "No valid access token provided"

        try:
            headers = {"Authorization": f"Bearer {use_token}"}
            response = self.session.get(location_url, headers=headers, timeout=20)

            if response.status_code == 202:
                return "pending", None, None

            if response.status_code == 200:
                if not response.text.strip():
                    # Azure occasionally returns 200 with empty body during interim states;
                    # treat as still-pending rather than a fatal error.
                    return "pending", None, None
                try:
                    blob_info = self._parse_blob_response(response.text)
                    if blob_info.status == "Completed" and blob_info.manifest.get("blobs"):
                        csv_url = blob_info.manifest["blobs"][0].get("blobLink")
                        return "completed", csv_url, None
                    elif blob_info.status == "Completed":
                        return "error", None, "Report completed but no CSV link found"
                    else:
                        return "pending", None, None
                except Exception as e:
                    return "error", None, f"Error parsing response: {str(e)}"

            return "error", None, f"Unexpected status code: {response.status_code}"

        except requests.exceptions.RequestException as e:
            return "error", None, f"Request exception: {str(e)}"
        except Exception as e:
            return "error", None, f"Unknown error: {str(e)}"

    def get_ri_csv_url(
        self, location_url: str, token: Optional[str] = None, max_retries: int = 10
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Retrieve the CSV download URL for the RI billing report.

        :param location_url: Polling location URL obtained from get_ri_location.
        :param token: Access token (optional).
        :param max_retries: Maximum number of polling retries (default 10).
        :return: Tuple (csv_url, error).
        """
        use_token = token if token else self._current_token
        if not use_token:
            return None, "No valid access token provided"
        print(f"Using access token: {use_token}")
        try:
            headers = {"Authorization": f"Bearer {use_token}"}
            retry_count = 0

            while retry_count < max_retries:
                response = self.session.get(location_url, headers=headers, timeout=20)
                if response.status_code == 200:
                    try:
                        blob_info = self._parse_blob_response(response.text)

                        if blob_info.status == "Completed" and blob_info.manifest.get("blobs"):
                            return blob_info.manifest["blobs"][0].get("blobLink"), None
                        elif blob_info.status != "Completed":
                            return None, f"Report generation not finished, current status: {blob_info.status}"
                        else:
                            return None, "No valid CSV download link found in response"
                    except Exception as e:
                        return None, f"Error parsing response: {str(e)}"

                time.sleep(self.POLLING_INTERVAL)
                retry_count += 1

            return None, f"Exceeded maximum retries ({max_retries}), CSV download link not yet available"
        except requests.exceptions.RequestException as e:
            return None, f"Request exception: {str(e)}"
        except Exception as e:
            return None, f"Error processing request: {str(e)}"

    def _parse_blob_response(self, response_text: str) -> BlobInfo:
        """Parse the blob status response."""
        try:
            data = json.loads(response_text)
            return BlobInfo(status=data.get("status", ""), manifest=data.get("manifest", {}))
        except json.JSONDecodeError:
            raise ValueError("Failed to parse JSON response")
        except Exception as e:
            raise ValueError(f"Error parsing blob info: {str(e)}")

    def download_ri_csv(self, csv_url: str, token: Optional[str] = None) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Download the RI billing CSV file.
        :param csv_url: CSV download URL obtained from get_ri_csv_url.
        :param token: Access token (optional).
        :return: Tuple (csv_content, error).
        """
        use_token = token if token else self._current_token
        if not use_token:
            return None, "No valid access token provided"
        try:
            response = self.session.get(csv_url, timeout=60)
            if response.status_code == 200:
                return response.content, None
            else:
                error_msg = f"Failed to download CSV, status code: {response.status_code}"
                try:
                    error_details = response.json()
                    error_msg += f", details: {error_details}"
                except:
                    pass
                return None, error_msg
        except requests.exceptions.RequestException as e:
            return None, f"Request exception: {str(e)}"
        except Exception as e:
            return None, f"Error processing request: {str(e)}"

    def get_ri_csv_as_json(self, location_url: str, token: Optional[str] = None, max_retries: int = 10):
        """
        Fetch the RI billing CSV content and yield rows as parsed BillingRecord objects.
        :param location_url: Polling location URL obtained from get_ri_location.
        :param token: Access token (optional).
        :param max_retries: Maximum number of polling retries (default 10).
        :yield: Tuple (row_data, error); (BillingRecord, None) on success, (None, error_message) on failure.
        """
        csv_url, error = self.get_ri_csv_url(location_url, token, max_retries)
        if error:
            yield None, f"Failed to get CSV download URL: {error}"
            return
        if not csv_url:
            yield None, "Unable to obtain a valid CSV download URL"
            return

        csv_content, error = self.download_ri_csv(csv_url, token)
        if error:
            yield None, f"Failed to download CSV content: {error}"
            return
        if not csv_content:
            yield None, "Downloaded CSV content is empty"
            return

        try:
            csv_str = csv_content.decode("utf-8-sig")
            csv_reader = csv.DictReader(csv_str.splitlines())
            for row in csv_reader:
                yield BillingRecord.model_validate(row), None
        except UnicodeDecodeError as e:
            yield None, f"CSV decoding failed: {str(e)}"
        except Exception as e:
            yield None, f"Error converting CSV to records: {str(e)}"

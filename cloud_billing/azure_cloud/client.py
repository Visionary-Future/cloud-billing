from typing import Any, Dict

import requests


class AzureCloudClient:
    def __init__(self, client_id: str, client_secret: str, tenant_id: str, is_china: bool = False) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.is_china = is_china

        if is_china:
            self.auth_endpoint = "https://login.chinacloudapi.cn"
            self.management_endpoint = "https://management.chinacloudapi.cn"
            self.cost_management_endpoint = "https://management.chinacloudapi.cn"
        else:
            self.auth_endpoint = "https://login.microsoftonline.com"
            self.management_endpoint = "https://management.azure.com"
            self.cost_management_endpoint = "https://management.azure.com"

        self.access_token = None

    def get_credentials(self):
        return {"client_id": self.client_id, "client_secret": self.client_secret, "tenant_id": self.tenant_id}

    def authenticate(self) -> str:
        """Get access token for Azure API authentication"""
        auth_url = f"{self.auth_endpoint}/{self.tenant_id}/oauth2/v2.0/token"

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": f"{self.management_endpoint}/.default",
        }

        response = requests.post(auth_url, headers=headers, data=data)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        return self.access_token

    def get_reserved_instance_charges(self, enrollment_id: str, billing_period: str) -> Dict[str, Any]:
        """Get Reserved Instance charges for Enterprise Agreement customers"""
        if not self.access_token:
            self.authenticate()

        url = f"{self.cost_management_endpoint}/providers/Microsoft.Billing/billingAccounts/{enrollment_id}/providers/Microsoft.Billing/billingPeriods/{billing_period}/providers/Microsoft.Consumption/reservationCharges"

        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_reserved_instance_utilization(
        self, reservation_order_id: str, reservation_id: str, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """Get Reserved Instance utilization data"""
        if not self.access_token:
            self.authenticate()

        url = f"{self.cost_management_endpoint}/providers/Microsoft.Capacity/reservationorders/{reservation_order_id}/reservations/{reservation_id}/providers/Microsoft.Consumption/reservationSummaries"

        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

        params = {
            "api-version": "2019-10-01",
            "grain": "daily",
            "$filter": f"properties/UsageDate ge {start_date} and properties/UsageDate le {end_date}",
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_reserved_instance_recommendations(self, subscription_id: str, scope: str = "Single") -> Dict[str, Any]:
        """Get Reserved Instance purchase recommendations"""
        if not self.access_token:
            self.authenticate()

        url = f"{self.cost_management_endpoint}/subscriptions/{subscription_id}/providers/Microsoft.Consumption/reservationRecommendations"

        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

        params = {"api-version": "2019-10-01", "$filter": f"properties/scope eq '{scope}'"}

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_usage_details(
        self, billing_account_id: str, billing_period: str, metric: str = "ActualCost"
    ) -> Dict[str, Any]:
        """Get detailed usage and billing information including RI data"""
        if not self.access_token:
            self.authenticate()

        url = f"{self.cost_management_endpoint}/providers/Microsoft.Billing/billingAccounts/{billing_account_id}/providers/Microsoft.Billing/billingPeriods/{billing_period}/providers/Microsoft.Consumption/usagedetails"

        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

        params = {"api-version": "2019-05-01", "metric": metric}

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_subscriptions(self) -> Dict[str, Any]:
        """Get list of Azure subscriptions"""
        if not self.access_token:
            self.authenticate()

        url = f"{self.management_endpoint}/subscriptions"

        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

        params = {"api-version": "2020-01-01"}

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_billing_accounts(self) -> Dict[str, Any]:
        """Get billing accounts"""
        if not self.access_token:
            self.authenticate()

        url = f"{self.cost_management_endpoint}/providers/Microsoft.Billing/billingAccounts"

        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

        params = {"api-version": "2020-05-01"}

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def make_request(self, service, action, params=None):
        """Generic method to make Azure API requests"""
        if not self.access_token:
            self.authenticate()

        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

        # Implementation depends on specific service and action
        # This is a placeholder for custom API calls
        pass

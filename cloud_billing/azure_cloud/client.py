import os
from typing import Optional

from azure.identity import ClientSecretCredential

os.environ["AZURE_CLOUD"] = "AZURE_CHINA_CLOUD"


class AzureCloudClient:
    def __init__(
        self, client_id: str, client_secret: str, tenant_id: str, subscription_id: Optional[str] = None
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.subscription_id = subscription_id
        self.authority = "https://login.chinacloudapi.cn"
        self.base_url = "https://management.chinacloudapi.cn"
        self.credential = ClientSecretCredential(
            tenant_id=tenant_id, client_id=client_id, client_secret=client_secret, authority=self.authority
        )

        self.token = self.credential.get_token("https://management.chinacloudapi.cn/.default").token

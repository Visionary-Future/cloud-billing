class AzureCloudClient:
    def __init__(self, client_id, client_secret, tenant_id) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id

    def get_credentials(self):
        return {"client_id": self.client_id, "client_secret": self.client_secret, "tenant_id": self.tenant_id}

    def make_request(self, service, action, params=None):
        # This method would contain logic to make a request to the Azure Cloud API
        pass

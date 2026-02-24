# Quick Start Guide

This guide will help you get started with the Cloud Billing package quickly.

## Basic Setup

### Alibaba Cloud

```python
from cloud_billing.alibaba_cloud import AlibabaCloudClient

client = AlibabaCloudClient(
    access_key_id="your_access_key_id",
    access_key_secret="your_access_key_secret",
    region_id="cn-hangzhou"  # or your preferred region
)

# Get billing data for a date range
billing_data = client.fetch_instance_bill_by_billing_cycle(
    billing_cycle="2024-01",
)

# Iterate through results
for record in billing_data:
    print(f"Product: {record.ProductName}")
    print(f"Cost: {record.PreTaxAmount}")
```

### AWS (Stub)

```python
from cloud_billing.aws_cloud import AWSCloudClient

# Initialize the client
client = AWSCloudClient()

# Available methods (limited - stub implementation)
region = client.get_region()
client.set_region("us-east-1")
error = client.connect()

# Note: Full Cost Explorer integration is not yet implemented
print("AWS billing support is under development")
```

### Azure

```python
from cloud_billing.azure_cloud import AzureCloudClient

# Initialize the client (RI billing reports)
client = AzureCloudClient(
    tenant_id="your_tenant_id",
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Get access token
token, error = client.get_access_token()

# Request RI billing report
location_url, error = client.get_ri_location(
    billing_account_id="123456789",
    start_date="2024-01-01",
    end_date="2024-01-31",
    metric="ActualCost"
)

# Download and parse RI data
for billing_record, error in client.get_ri_csv_as_json(location_url):
    if not error:
        print(f"Service: {billing_record.ProductName}")
        print(f"Cost: {billing_record.PreTaxAmount}")
```

### Huawei Cloud (Stub)

```python
from cloud_billing.huawei_cloud import HuaweiCloudClient

# Initialize the client
client = HuaweiCloudClient(
    access_key_id="your_access_key_id",
    secret_access_key="your_secret_access_key",
    region="cn-north-1"
)

# Available methods (limited - stub implementation)
error = client.connect()
project_id = client.get_project_id()

# Note: Full billing data support is under development
print("Huawei Cloud billing support is under development")
```

## Environment Variables

For better security, use environment variables for sensitive information:

```bash
# Alibaba Cloud
export ALIBABA_ACCESS_KEY_ID="your_access_key_id"
export ALIBABA_ACCESS_KEY_SECRET="your_access_key_secret"

# AWS (standard AWS environment variables)
export AWS_ACCESS_KEY_ID="your_access_key_id"
export AWS_SECRET_ACCESS_KEY="your_secret_access_key"
export AWS_DEFAULT_REGION="us-east-1"

# Azure
export AZURE_SUBSCRIPTION_ID="your_subscription_id"
export AZURE_TENANT_ID="your_tenant_id"
export AZURE_CLIENT_ID="your_client_id"
export AZURE_CLIENT_SECRET="your_client_secret"

# Huawei Cloud
export HUAWEI_ACCESS_KEY_ID="your_access_key_id"
export HUAWEI_SECRET_ACCESS_KEY="your_secret_access_key"
```

Then initialize clients without explicit credentials:

```python
from cloud_billing.alibaba_cloud import AlibabaCloudClient

# Will automatically use environment variables
client = AlibabaCloudClient()
```

## Error Handling

### Alibaba Cloud

```python
from cloud_billing.alibaba_cloud import AlibabaCloudClient
from cloud_billing.alibaba_cloud.exceptions import (
    AlibabaBillingException,
    AuthenticationException,
    RateLimitException
)

try:
    client = AlibabaCloudClient()
    billing_data = client.fetch_instance_bill_by_billing_cycle("2024-01")
except AuthenticationException as e:
    print(f"Authentication failed: {e}")
except RateLimitException as e:
    print(f"Rate limit exceeded: {e}")
except AlibabaBillingException as e:
    print(f"Billing API error: {e}")
```

### Azure

```python
from cloud_billing.azure_cloud import AzureCloudClient

client = AzureCloudClient(
    tenant_id="your_tenant_id",
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Check for errors in return tuples
token, error = client.get_access_token()
if error:
    print(f"Authentication error: {error}")

# Handle CSV parsing errors
for billing_record, error in client.get_ri_csv_as_json(location_url):
    if error:
        print(f"CSV parsing error: {error}")
        continue
    # Process record
```

### General Pattern

Most methods return tuples of (result, error):

```python
result, error = client.some_method()
if error:
    print(f"Error: {error}")
else:
    # Process result
    print(result)
```

## Next Steps

- Explore [Cloud Provider Guides](../providers/alibaba-cloud.md) for detailed usage
- Check the [API Reference](../api/alibaba-cloud.md) for complete method documentation
- See [Examples](../examples.md) for more complex use cases

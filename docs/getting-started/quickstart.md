# Quick Start Guide

This guide will help you get started with the Cloud Billing package quickly.

## Basic Setup

### Alibaba Cloud

```python
client = AlibabaCloudClient(
    access_key_id="your_access_key_id",
    access_key_secret="your_access_key_secret",
    region_id="cn-hangzhou"  # or your preferred region
)

# Get billing data for a date range
billing_data = client.fetch_instance_bill_by_billing_cycle(
    billing_cycle="2024-01",
)

```

### AWS

```python
from cloud_billing.aws_cloud import AWSCloudClient

# Initialize the client (uses AWS credentials from environment or AWS config)
client = AWSCloudClient(
    region_name="us-east-1"
)

# Get cost and usage data
cost_data = client.get_cost_and_usage(
    start_date="2024-01-01",
    end_date="2024-01-31",
    granularity="MONTHLY"
)
```

### Azure

```python
from cloud_billing.azure_cloud import AzureCloudClient

# Initialize the client
client = AzureCloudClient(
    subscription_id="your_subscription_id",
    tenant_id="your_tenant_id",
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Get billing data
billing_data = client.get_billing_data(
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

### Huawei Cloud

```python
from cloud_billing.huawei_cloud import HuaweiCloudClient

# Initialize the client
client = HuaweiCloudClient(
    access_key_id="your_access_key_id",
    secret_access_key="your_secret_access_key",
    region="cn-north-1"
)

# Get billing data
billing_data = client.get_billing_data(
    start_date="2024-01-01",
    end_date="2024-01-31"
)
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

The package includes custom exceptions for better error handling:

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

## Next Steps

- Explore [Cloud Provider Guides](../providers/alibaba-cloud.md) for detailed usage
- Check the [API Reference](../api/alibaba-cloud.md) for complete method documentation
- See [Examples](../examples.md) for more complex use cases

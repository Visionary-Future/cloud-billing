# Alibaba Cloud

The Alibaba Cloud billing client provides comprehensive access to billing and cost management data from Alibaba Cloud services.

## Features

- Standard billing data retrieval
- Kubernetes cluster billing with namespace-level details
- Multi-region support
- Rate limiting and error handling
- Comprehensive cost analysis

## Basic Usage

### Client Initialization

```python
from cloud_billing.alibaba_cloud import AlibabaBillingClient

# Using explicit credentials
client = AlibabaBillingClient(
    access_key_id="your_access_key_id",
    access_key_secret="your_access_key_secret",
    region_id="cn-hangzhou"
)

# Using environment variables
# Set ALIBABA_ACCESS_KEY_ID and ALIBABA_ACCESS_KEY_SECRET
client = AlibabaBillingClient()
```

### Getting Billing Data

```python
# Get billing data for a date range
billing_data = client.get_billing_data(
    start_date="2024-01-01",
    end_date="2024-01-31",
    granularity="DAILY"  # DAILY, MONTHLY
)

print(f"Total cost: {billing_data.total_cost}")
print(f"Currency: {billing_data.currency}")
print(f"Number of billing items: {len(billing_data.billing_items)}")

# Iterate through billing items
for item in billing_data.billing_items:
    print(f"Service: {item.product_name}")
    print(f"Cost: {item.cost}")
    print(f"Usage: {item.usage_amount} {item.usage_unit}")
```

## Kubernetes Billing

Alibaba Cloud provides detailed billing information for Kubernetes clusters:

```python
from cloud_billing.alibaba_cloud import K8sBillingClient

# Initialize Kubernetes billing client
k8s_client = K8sBillingClient(
    access_key_id="your_access_key_id",
    access_key_secret="your_access_key_secret",
    region_id="cn-hangzhou"
)

# Get cluster billing data
cluster_billing = k8s_client.get_cluster_billing(
    cluster_id="c-123abc456def",
    start_date="2024-01-01",
    end_date="2024-01-31"
)

print(f"Cluster total cost: {cluster_billing.total_cost}")
print(f"Node count: {cluster_billing.node_count}")

# Analyze by namespace
for item in cluster_billing.billing_items:
    print(f"Namespace: {item.namespace}")
    print(f"Pod: {item.pod_name}")
    print(f"Cost: {item.cost}")
```

## Configuration Options

### Region Support

Alibaba Cloud operates in multiple regions. Specify the appropriate region:

```python
# Common regions
regions = [
    "cn-hangzhou",    # China (Hangzhou)
    "cn-shanghai",    # China (Shanghai)
    "cn-beijing",     # China (Beijing)
    "ap-southeast-1", # Singapore
    "us-west-1",      # US (Silicon Valley)
    "eu-central-1"    # Germany (Frankfurt)
]

client = AlibabaBillingClient(region_id="cn-hangzhou")
```

### Authentication

Multiple authentication methods are supported:

#### 1. Direct Credentials
```python
client = AlibabaBillingClient(
    access_key_id="LTAI...",
    access_key_secret="your_secret"
)
```

#### 2. Environment Variables
```bash
export ALIBABA_ACCESS_KEY_ID="LTAI..."
export ALIBABA_ACCESS_KEY_SECRET="your_secret"
export ALIBABA_REGION_ID="cn-hangzhou"
```

```python
client = AlibabaBillingClient()  # Automatically uses env vars
```

#### 3. Configuration File
Create `~/.alibaba/credentials`:
```ini
[default]
access_key_id = LTAI...
access_key_secret = your_secret
region_id = cn-hangzhou
```

## Error Handling

The client provides specific exceptions for different error scenarios:

```python
from cloud_billing.alibaba_cloud.exceptions import (
    AlibabaBillingException,
    AuthenticationException,
    RateLimitException,
    RegionNotSupportedException
)

try:
    billing_data = client.get_billing_data("2024-01-01", "2024-01-31")
except AuthenticationException as e:
    print(f"Authentication failed: {e}")
    # Check credentials
except RateLimitException as e:
    print(f"Rate limit exceeded: {e}")
    # Implement retry with backoff
except RegionNotSupportedException as e:
    print(f"Region not supported: {e}")
    # Use a different region
except AlibabaBillingException as e:
    print(f"General billing error: {e}")
```

## Advanced Features

### Filtering and Grouping

```python
# Get billing data with filters
billing_data = client.get_billing_data(
    start_date="2024-01-01",
    end_date="2024-01-31",
    product_code="ecs",  # Filter by service
    billing_cycle="2024-01"  # Specific billing cycle
)

# Group by product
from collections import defaultdict

product_costs = defaultdict(float)
for item in billing_data.billing_items:
    product_costs[item.product_name] += item.cost

for product, cost in sorted(product_costs.items(), key=lambda x: x[1], reverse=True):
    print(f"{product}: ¥{cost:.2f}")
```

### Pagination for Large Datasets

```python
# Handle large datasets with pagination
def get_all_billing_data(client, start_date, end_date):
    all_items = []
    page_num = 1
    page_size = 100

    while True:
        billing_data = client.get_billing_data(
            start_date=start_date,
            end_date=end_date,
            page_num=page_num,
            page_size=page_size
        )

        all_items.extend(billing_data.billing_items)

        if len(billing_data.billing_items) < page_size:
            break

        page_num += 1

    return all_items
```

## Best Practices

1. **Rate Limiting**: Implement proper rate limiting to avoid API throttling
2. **Caching**: Cache billing data for frequently accessed date ranges
3. **Error Handling**: Always handle specific exceptions appropriately
4. **Credentials Security**: Never hardcode credentials in source code
5. **Resource Cleanup**: Properly close client connections when done

## Troubleshooting

### Common Issues

**Authentication Errors**
- Verify access key ID and secret are correct
- Check if keys have billing API permissions
- Ensure region is correctly specified

**Rate Limiting**
- Implement exponential backoff
- Reduce request frequency
- Use pagination for large datasets

**Empty Results**
- Verify date range format (YYYY-MM-DD)
- Check if billing data exists for the specified period
- Ensure correct product codes and filters

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
client = AlibabaBillingClient()
```

## See Also

- [API Reference](../api/alibaba-cloud.md) - Detailed API documentation
- [Examples](../examples.md) - More usage examples
- [Common Utilities](../api/common.md) - Shared utilities and helpers

# Alibaba Cloud

The Alibaba Cloud billing client provides comprehensive access to billing and cost management data from Alibaba Cloud services.

## Features

- Instance billing data retrieval
- Amortized cost analysis
- Automatic pagination handling
- Instance-level cost details
- Multi-period data fetching

## Basic Usage

### Client Initialization

```python
from cloud_billing.alibaba_cloud import AlibabaCloudClient

# Using explicit credentials
client = AlibabaCloudClient(
    access_key_id="your_access_key_id",
    access_key_secret="your_access_key_secret",
    region_id="cn-hangzhou"
)

# Using environment variables
# Set ALIBABA_ACCESS_KEY_ID and ALIBABA_ACCESS_KEY_SECRET
client = AlibabaCloudClient()
```

### Getting Instance Billing Data

```python
# Get billing data for a billing cycle (YYYY-MM format)
billing_items = client.fetch_instance_bill_by_billing_cycle(
    billing_cycle="2024-01"
)

print(f"Number of billing items: {len(billing_items)}")

# Iterate through billing items
for item in billing_items:
    print(f"Service: {item.ProductName}")
    print(f"Instance ID: {item.InstanceID}")
    print(f"Cost: {item.PretaxAmount} {item.Currency}")
    print(f"Usage: {item.Usage}")
    print(f"Billing Date: {item.BillingDate}")
```

### Getting Amortized Costs

```python
# Get amortized costs by amortization period
amortized_items = client.fetch_instance_amortized_cost_by_amortization_period(
    billing_cycle="2024-01"
)

for item in amortized_items:
    print(f"Service: {item.ProductName}")
    print(f"Amortized Amount: {item.CurrentAmortizationPretaxAmount}")
    print(f"Amortization Period: {item.AmortizationPeriod}")
    print(f"Status: {item.AmortizationStatus}")
```

## Pagination

The client automatically handles pagination for large datasets:

```python
# Fetch with custom pagination parameters
billing_items = client.fetch_instance_bill_by_billing_cycle(
    billing_cycle="2024-01",
    max_page_size=100  # Results per page (default: 100)
)

# The client automatically fetches all pages and returns combined results
```

## Configuration

### Region Selection

Specify the region when initializing the client:

```python
# Common regions
client = AlibabaCloudClient(
    access_key_id="your_key",
    access_key_secret="your_secret",
    region_id="cn-hangzhou"  # Required parameter
)
```

### Authentication

Multiple authentication methods are supported:

#### 1. Direct Credentials
```python
client = AlibabaCloudClient(
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
client = AlibabaCloudClient()  # Automatically uses env vars
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

The client raises exceptions for various error scenarios:

```python
from cloud_billing.alibaba_cloud.exceptions import (
    APIError,
    InvalidResponseError
)

try:
    billing_items = client.fetch_instance_bill_by_billing_cycle("2024-01")
except APIError as e:
    print(f"API error: {e}")
    # Handle API failures
except InvalidResponseError as e:
    print(f"Invalid response format: {e}")
    # Handle malformed responses
except ValueError as e:
    print(f"Invalid billing cycle format: {e}")
    # Ensure billing_cycle is in YYYY-MM format
```

## Advanced Features

### Filtering and Analysis

```python
# Group billing items by product
from collections import defaultdict

billing_items = client.fetch_instance_bill_by_billing_cycle(billing_cycle="2024-01")

product_costs = defaultdict(float)
for item in billing_items:
    product_costs[item.ProductName] += item.PretaxAmount

for product, cost in sorted(product_costs.items(), key=lambda x: x[1], reverse=True):
    print(f"{product}: ¥{cost:.2f}")

# Analyze by region
region_costs = defaultdict(float)
for item in billing_items:
    region_costs[item.Region] += item.PretaxAmount

for region, cost in sorted(region_costs.items(), key=lambda x: x[1], reverse=True):
    print(f"{region}: ¥{cost:.2f}")
```

## Best Practices

1. **Credentials Security**: Never hardcode credentials in source code
2. **Error Handling**: Always handle APIError and InvalidResponseError
3. **Caching**: Cache billing data for frequently accessed billing cycles
4. **Pagination**: Let the client handle pagination automatically
5. **Billing Cycle Format**: Always validate billing_cycle format before requests

## Troubleshooting

### Common Issues

**Authentication Errors**
- Verify access key ID and secret are correct
- Check if keys have billing API permissions
- Ensure region is correctly specified

**Invalid Billing Cycle Format**
- Use YYYY-MM format (e.g., "2024-01")
- Do not include day component
- Ensure hyphen is included

**Empty Results**
- Verify billing cycle exists and contains data
- Check that credentials have permission to access billing data
- Note that billing data may have a 1-2 day delay

### Billing Cycle Format

Always use YYYY-MM format for billing cycles:

```python
# Correct format
billing_items = client.fetch_instance_bill_by_billing_cycle("2024-01")

# Incorrect formats will raise ValueError
# client.fetch_instance_bill_by_billing_cycle("2024-01-01")  # ❌ Too detailed
# client.fetch_instance_bill_by_billing_cycle("202401")      # ❌ No hyphen
```

## See Also

- [API Reference](../api/alibaba-cloud.md) - Detailed API documentation
- [Examples](../examples.md) - More usage examples
- [Common Utilities](../api/common.md) - Shared utilities and helpers

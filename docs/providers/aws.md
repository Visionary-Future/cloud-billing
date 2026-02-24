# AWS

> ⚠️ **Implementation Status**: The AWS client is currently a **stub implementation** with limited functionality. Core billing methods are not yet implemented.

The AWS billing client provides basic connection management and region configuration.

## Features

- Region configuration
- Connection testing
- Client state management

## Basic Usage

### Client Initialization

```python
from cloud_billing.aws_cloud import AWSCloudClient

# Create client with region
client = AWSCloudClient(region_name="us-east-1")

# Get current region
region = client.get_region()
print(f"Region: {region}")

# Set different region
client.set_region("us-west-2")

# Test connection
connection_status = client.connect()
print(f"Connection status: {connection_status}")
```


## Available Methods

### get_region()

Retrieves the currently configured AWS region.

```python
region = client.get_region()
```

### set_region(region_name)

Sets the AWS region for the client.

```python
client.set_region("us-west-2")
```

### connect()

Tests and establishes connection with AWS.

```python
status = client.connect()
```

## Future Development

The following methods are planned for future implementation:

- `get_cost_and_usage()` - Retrieve cost and usage data
- `get_cost_forecast()` - Get cost forecasts
- `get_dimension_values()` - List available dimensions for filtering

For now, consider using the AWS SDK (boto3) directly:

```python
import boto3

client = boto3.client('ce', region_name='us-east-1')
response = client.get_cost_and_usage(
    TimePeriod={'Start': '2024-01-01', 'End': '2024-01-31'},
    Granularity='MONTHLY',
    Metrics=['UnblendedCost']
)
```

## See Also

- [AWS Cost Explorer API Docs](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/)
- [Boto3 Cost Explorer Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce.html)

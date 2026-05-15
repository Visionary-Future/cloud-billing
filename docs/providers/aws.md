# AWS

The AWS billing client provides access to cost and usage data through the AWS Cost Explorer API.

## Features

- Cost and usage data retrieval with `get_cost_and_usage()`
- Automatic pagination via NextPageToken
- Multi-dimensional grouping (SERVICE, REGION, LINKED_ACCOUNT, etc.)
- Custom metric selection (UnblendedCost, AmortizedCost, BlendedCost, UsageQuantity)
- Filter support for targeted cost analysis
- Monthly and daily granularity

## Basic Usage

### Client Initialization

```python
from cloud_billing.aws_cloud import AWSCloudClient

client = AWSCloudClient(
    access_key_id="your_access_key_id",
    secret_access_key="your_secret_access_key",
    region_name="us-east-1",  # Optional, defaults to us-east-1
)
```

Note: Cost Explorer is only available in `us-east-1`. The client always uses `us-east-1`
for the Cost Explorer endpoint regardless of the `region_name` parameter.

### Getting Cost and Usage Data

```python
cost_data = client.get_cost_and_usage(
    time_period={"Start": "2024-01-01", "End": "2024-02-01"},
    granularity="MONTHLY",
    metrics=["UnblendedCost", "UsageQuantity"],
    group_by=[{"Type": "DIMENSION", "Key": "SERVICE"}],
)

for period in cost_data:
    print(f"Period: {period.TimePeriod['Start']} → {period.TimePeriod['End']}")
    for group in (period.Groups or []):
        service = group.Keys[0]
        cost = group.Metrics["UnblendedCost"].Amount
        print(f"  {service}: ${cost}")
```

### Daily Granularity

```python
cost_data = client.get_cost_and_usage(
    time_period={"Start": "2024-01-01", "End": "2024-01-08"},
    granularity="DAILY",
    metrics=["UnblendedCost"],
)

for period in cost_data:
    date = period.TimePeriod["Start"]
    total = period.Total.get("UnblendedCost", {}).get("Amount", "0")
    print(f"{date}: ${total}")
```

### Filtering by Service

```python
cost_data = client.get_cost_and_usage(
    time_period={"Start": "2024-01-01", "End": "2024-02-01"},
    granularity="MONTHLY",
    group_by=[{"Type": "DIMENSION", "Key": "REGION"}],
    filter_expression={
        "Dimensions": {
            "Key": "SERVICE",
            "Values": ["Amazon EC2", "Amazon RDS"],
        }
    },
)
```

## Pagination

The client automatically handles pagination via `NextPageToken`:

```python
# All pages are fetched and merged automatically
cost_data = client.get_cost_and_usage(
    time_period={"Start": "2024-01-01", "End": "2024-07-01"},
    group_by=[{"Type": "DIMENSION", "Key": "SERVICE"}],
)
# Returns complete dataset across all pages
```

## Configuration

### Authentication

The client accepts explicit AWS credentials:

```python
client = AWSCloudClient(
    access_key_id="AKIA...",
    secret_access_key="your_secret_key",
)
```

Or use the standard boto3 credential chain (environment variables, ~/.aws/credentials, IAM roles):

```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="your_secret_key"
```

```python
# boto3 will pick up credentials from the environment
import os
client = AWSCloudClient(
    access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
)
```

### Required IAM Permissions

Your AWS IAM user/role must have the `ce:GetCostAndUsage` permission:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "ce:GetCostAndUsage",
            "Resource": "*"
        }
    ]
}
```

## Error Handling

```python
cost_data = client.get_cost_and_usage(
    time_period={"Start": "2024-01-01", "End": "2024-02-01"},
)

try:
    client.get_cost_and_usage(
        time_period={"Start": "bad-date", "End": "2024-02-01"},
    )
except ValueError as e:
    print(f"Invalid date format: {e}")
```

## Available GroupBy Dimensions

| Dimension | Description |
|-----------|-------------|
| `SERVICE` | AWS service (e.g., Amazon EC2, Amazon S3) |
| `REGION` | AWS region |
| `LINKED_ACCOUNT` | Linked account ID |
| `INSTANCE_TYPE` | EC2 instance type |
| `USAGE_TYPE` | Usage type |
| `OPERATION` | API operation |
| `AZ` | Availability Zone |
| `PLATFORM` | Platform |

## Available Metrics

| Metric | Description |
|--------|-------------|
| `UnblendedCost` | Raw cost before discounts (default) |
| `AmortizedCost` | Cost with reservation amortization |
| `BlendedCost` | Blended rates for consolidated billing |
| `NetAmortizedCost` | Amortized cost net of discounts |
| `NetUnblendedCost` | Unblended cost net of discounts |
| `UsageQuantity` | Usage quantity |
| `NormalizedUsageAmount` | Normalized usage |

## See Also

- [API Reference](../api/aws.md) - Auto-generated API documentation
- [Examples](../examples.md) - More usage examples
- [AWS Cost Explorer API Docs](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/)
- [Boto3 Cost Explorer Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce.html)

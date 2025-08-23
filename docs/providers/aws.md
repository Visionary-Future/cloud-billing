# AWS

The AWS billing client provides access to cost and usage data through AWS Cost Explorer API.

## Features

- Cost and usage data retrieval
- Multiple granularity options (DAILY, MONTHLY, HOURLY)
- Service-level cost breakdown
- Dimension and metric filtering
- Cost forecasting support

## Basic Usage

### Client Initialization

```python
from cloud_billing.aws_cloud import AWSBillingClient

# Using explicit credentials
client = AWSBillingClient(
    aws_access_key_id="your_access_key_id",
    aws_secret_access_key="your_secret_access_key",
    region_name="us-east-1"
)

# Using AWS credentials file or environment variables
client = AWSBillingClient(region_name="us-east-1")

# Using IAM roles (when running on EC2)
client = AWSBillingClient()
```

### Getting Cost and Usage Data

```python
# Get cost and usage data
cost_data = client.get_cost_and_usage(
    start_date="2024-01-01",
    end_date="2024-01-31",
    granularity="MONTHLY"  # DAILY, MONTHLY, HOURLY
)

print(f"Total cost: ${cost_data.total_cost:.2f}")
print(f"Currency: {cost_data.currency}")

# Iterate through time periods
for period in cost_data.results_by_time:
    print(f"Period: {period.time_period.start} to {period.time_period.end}")
    print(f"Cost: ${period.total.unblended_cost.amount:.2f}")
```

### Service-Level Cost Analysis

```python
# Get costs grouped by service
cost_data = client.get_cost_and_usage(
    start_date="2024-01-01",
    end_date="2024-01-31",
    granularity="MONTHLY",
    group_by=[{"Type": "DIMENSION", "Key": "SERVICE"}]
)

for period in cost_data.results_by_time:
    print(f"Period: {period.time_period.start}")
    for group in period.groups:
        service_name = group.keys[0]
        cost = float(group.metrics["UnblendedCost"]["Amount"])
        print(f"  {service_name}: ${cost:.2f}")
```

## Configuration Options

### Authentication

AWS credentials can be configured in several ways:

#### 1. Environment Variables
```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="us-east-1"
```

#### 2. AWS Credentials File
`~/.aws/credentials`:
```ini
[default]
aws_access_key_id = AKIA...
aws_secret_access_key = your_secret_key

[profile_name]
aws_access_key_id = AKIA...
aws_secret_access_key = your_secret_key
region = us-west-2
```

#### 3. IAM Roles
When running on EC2, the client can automatically use IAM instance profiles.

### Regions

AWS Cost Explorer is available in specific regions:

```python
# Cost Explorer is primarily available in us-east-1
client = AWSBillingClient(region_name="us-east-1")
```

## Advanced Features

### Filtering

Apply filters to narrow down cost data:

```python
# Filter by specific services
cost_data = client.get_cost_and_usage(
    start_date="2024-01-01",
    end_date="2024-01-31",
    filters={
        "Dimensions": {
            "Key": "SERVICE",
            "Values": ["Amazon Elastic Compute Cloud - Compute", "Amazon Simple Storage Service"]
        }
    }
)

# Filter by tags
cost_data = client.get_cost_and_usage(
    start_date="2024-01-01",
    end_date="2024-01-31",
    filters={
        "Tags": {
            "Key": "Environment",
            "Values": ["Production"]
        }
    }
)
```

### Cost Forecasting

```python
# Get cost forecasts
forecast = client.get_cost_forecast(
    start_date="2024-02-01",
    end_date="2024-02-28",
    granularity="MONTHLY",
    metric="UNBLENDED_COST"
)

print(f"Forecasted cost: ${forecast.total.amount:.2f}")
print(f"Prediction interval: ${forecast.prediction_interval_lower_bound:.2f} - ${forecast.prediction_interval_upper_bound:.2f}")
```

### Usage Data

```python
# Get usage data instead of cost data
usage_data = client.get_cost_and_usage(
    start_date="2024-01-01",
    end_date="2024-01-31",
    granularity="DAILY",
    metrics=["UsageQuantity"]
)

for period in usage_data.results_by_time:
    usage = period.total.usage_quantity
    print(f"Date: {period.time_period.start}")
    print(f"Usage: {usage.amount} {usage.unit}")
```

## Error Handling

```python
from cloud_billing.aws_cloud.exceptions import (
    AWSBillingException,
    AWSAuthenticationException,
    AWSRateLimitException
)
from botocore.exceptions import ClientError

try:
    cost_data = client.get_cost_and_usage("2024-01-01", "2024-01-31")
except AWSAuthenticationException as e:
    print(f"AWS authentication failed: {e}")
except AWSRateLimitException as e:
    print(f"AWS rate limit exceeded: {e}")
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'InvalidParameterValue':
        print(f"Invalid parameter: {e}")
    elif error_code == 'LimitExceededException':
        print(f"Service limit exceeded: {e}")
except AWSBillingException as e:
    print(f"AWS billing error: {e}")
```

## Cost Analysis Examples

### Monthly Spend Trend

```python
from datetime import datetime, timedelta

def get_monthly_trend(client, months=12):
    trends = []

    for i in range(months):
        end_date = datetime.now().replace(day=1) - timedelta(days=i*30)
        start_date = end_date.replace(day=1)

        cost_data = client.get_cost_and_usage(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            granularity="MONTHLY"
        )

        if cost_data.results_by_time:
            total_cost = float(cost_data.results_by_time[0].total.unblended_cost.amount)
            trends.append({
                'month': start_date.strftime("%Y-%m"),
                'cost': total_cost
            })

    return sorted(trends, key=lambda x: x['month'])

# Usage
trends = get_monthly_trend(client)
for trend in trends:
    print(f"{trend['month']}: ${trend['cost']:.2f}")
```

### Top Services by Cost

```python
def get_top_services(client, start_date, end_date, limit=10):
    cost_data = client.get_cost_and_usage(
        start_date=start_date,
        end_date=end_date,
        granularity="MONTHLY",
        group_by=[{"Type": "DIMENSION", "Key": "SERVICE"}]
    )

    service_costs = []
    for period in cost_data.results_by_time:
        for group in period.groups:
            service_name = group.keys[0]
            cost = float(group.metrics["UnblendedCost"]["Amount"])
            service_costs.append({
                'service': service_name,
                'cost': cost
            })

    # Sort by cost and return top services
    return sorted(service_costs, key=lambda x: x['cost'], reverse=True)[:limit]

# Usage
top_services = get_top_services(client, "2024-01-01", "2024-01-31")
for i, service in enumerate(top_services, 1):
    print(f"{i}. {service['service']}: ${service['cost']:.2f}")
```

## Best Practices

1. **Use us-east-1**: Cost Explorer APIs work best in the us-east-1 region
2. **Implement Caching**: Cache cost data to reduce API calls
3. **Handle Rate Limits**: AWS has rate limits on Cost Explorer APIs
4. **Use Appropriate Granularity**: Choose the right granularity for your use case
5. **Filter Early**: Use filters to reduce data transfer and processing

## Troubleshooting

### Common Issues

**Authentication Errors**
- Verify AWS credentials are configured correctly
- Check IAM permissions for Cost Explorer APIs
- Ensure correct region configuration

**Empty Results**
- Verify date range format
- Check if Cost Explorer is enabled for your account
- Ensure billing data exists for the specified period

**Rate Limiting**
- Implement retry logic with exponential backoff
- Reduce request frequency
- Use appropriate pagination

### Required IAM Permissions

Your AWS user/role needs these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ce:GetDimensionValues",
                "ce:GetForecast",
                "ce:GetUsageForecast"
            ],
            "Resource": "*"
        }
    ]
}
```

## See Also

- [API Reference](../api/aws.md) - Detailed API documentation
- [Examples](../examples.md) - More usage examples
- [AWS Cost Explorer Documentation](https://docs.aws.amazon.com/cost-explorer/)

# Huawei Cloud

The Huawei Cloud billing client provides access to billing and usage data through Huawei Cloud's billing APIs.

## Features

- Billing data retrieval for multiple services
- Resource-level usage tracking
- Cost analysis by product and region
- Multi-project support
- Detailed usage metrics

## Basic Usage

### Client Initialization

```python
from cloud_billing.huawei_cloud import HuaweiCloudClient

# Using explicit credentials
client = HuaweiCloudClient(
    access_key_id="your_access_key_id",
    secret_access_key="your_secret_access_key",
    region="cn-north-1",
    project_id="your_project_id"
)

# Using environment variables
client = HuaweiCloudClient()
```

### Getting Billing Data

```python
# Get billing data for a date range
billing_data = client.get_billing_data(
    start_date="2024-01-01",
    end_date="2024-01-31",
    cycle_type="MONTHLY"  # MONTHLY, DAILY
)

print(f"Total cost: {billing_data.total_cost}")
print(f"Currency: {billing_data.currency}")
print(f"Number of billing items: {len(billing_data.billing_items)}")

# Iterate through billing items
for item in billing_data.billing_items:
    print(f"Product: {item.product_name}")
    print(f"Resource: {item.resource_name}")
    print(f"Cost: {item.cost}")
    print(f"Usage: {item.usage_amount} {item.usage_unit}")
```

### Service-Level Analysis

```python
# Get detailed service usage
service_usage = client.get_service_usage(
    start_date="2024-01-01",
    end_date="2024-01-31",
    service_type="ECS"  # ECS, OBS, RDS, etc.
)

for usage in service_usage.usage_records:
    print(f"Instance: {usage.instance_id}")
    print(f"Specification: {usage.instance_spec}")
    print(f"Usage duration: {usage.duration} hours")
    print(f"Cost: {usage.cost}")
```

## Configuration Options

### Authentication

#### 1. Environment Variables
```bash
export HUAWEI_ACCESS_KEY_ID="your_access_key_id"
export HUAWEI_SECRET_ACCESS_KEY="your_secret_access_key"
export HUAWEI_REGION="cn-north-1"
export HUAWEI_PROJECT_ID="your_project_id"
```

#### 2. Configuration File
Create `~/.huawei/credentials`:
```ini
[default]
access_key_id = your_access_key_id
secret_access_key = your_secret_access_key
region = cn-north-1
project_id = your_project_id
```

### Regions

Huawei Cloud operates in multiple regions:

```python
# Common regions
regions = [
    "cn-north-1",     # Beijing 1
    "cn-north-4",     # Beijing 4
    "cn-east-2",      # Shanghai 2
    "cn-east-3",      # Shanghai 1
    "cn-south-1",     # Guangzhou
    "ap-southeast-1", # Hong Kong
    "ap-southeast-3", # Singapore
]

client = HuaweiCloudClient(region="cn-north-1")
```

## Advanced Features

### Multi-Project Billing

```python
# Get billing data across multiple projects
projects = ["project-1", "project-2", "project-3"]
consolidated_data = []

for project_id in projects:
    client = HuaweiCloudClient(project_id=project_id)
    billing_data = client.get_billing_data("2024-01-01", "2024-01-31")

    consolidated_data.append({
        'project_id': project_id,
        'total_cost': billing_data.total_cost,
        'billing_items': billing_data.billing_items
    })

# Calculate total across all projects
total_cost = sum(data['total_cost'] for data in consolidated_data)
print(f"Total cost across all projects: ¥{total_cost:.2f}")
```

### Resource Usage Analysis

```python
# Analyze ECS instance usage
def analyze_ecs_usage(client, start_date, end_date):
    ecs_usage = client.get_service_usage(
        start_date=start_date,
        end_date=end_date,
        service_type="ECS"
    )

    # Group by instance specification
    spec_usage = {}
    for usage in ecs_usage.usage_records:
        spec = usage.instance_spec
        if spec not in spec_usage:
            spec_usage[spec] = {
                'count': 0,
                'total_duration': 0,
                'total_cost': 0
            }

        spec_usage[spec]['count'] += 1
        spec_usage[spec]['total_duration'] += usage.duration
        spec_usage[spec]['total_cost'] += usage.cost

    return spec_usage

# Usage
ecs_analysis = analyze_ecs_usage(client, "2024-01-01", "2024-01-31")
for spec, data in ecs_analysis.items():
    avg_duration = data['total_duration'] / data['count']
    print(f"Spec: {spec}")
    print(f"  Instances: {data['count']}")
    print(f"  Avg duration: {avg_duration:.1f} hours")
    print(f"  Total cost: ¥{data['total_cost']:.2f}")
```

### Cost Optimization

```python
def identify_optimization_opportunities(client, start_date, end_date):
    billing_data = client.get_billing_data(start_date, end_date)
    opportunities = []

    # Group costs by product
    product_costs = {}
    for item in billing_data.billing_items:
        product = item.product_name
        if product not in product_costs:
            product_costs[product] = []
        product_costs[product].append(item)

    # Analyze each product
    for product, items in product_costs.items():
        total_cost = sum(item.cost for item in items)

        # Check for high-cost, low-utilization resources
        if product == "ECS" and total_cost > 1000:  # Example threshold
            low_utilization = [
                item for item in items
                if item.usage_amount < 50  # Less than 50% utilization
            ]

            if low_utilization:
                potential_savings = sum(item.cost * 0.5 for item in low_utilization)
                opportunities.append({
                    'product': product,
                    'type': 'Right-sizing',
                    'description': f'{len(low_utilization)} under-utilized instances',
                    'potential_savings': potential_savings
                })

    return opportunities

# Usage
opportunities = identify_optimization_opportunities(client, "2024-01-01", "2024-01-31")
for opp in opportunities:
    print(f"{opp['product']} - {opp['type']}")
    print(f"  {opp['description']}")
    print(f"  Potential savings: ¥{opp['potential_savings']:.2f}")
```

## Error Handling

```python
from cloud_billing.huawei_cloud.exceptions import (
    HuaweiBillingException,
    HuaweiAuthenticationException,
    HuaweiRateLimitException,
    HuaweiRegionNotSupportedException
)

try:
    billing_data = client.get_billing_data("2024-01-01", "2024-01-31")
except HuaweiAuthenticationException as e:
    print(f"Huawei authentication failed: {e}")
    # Check access keys and project ID
except HuaweiRateLimitException as e:
    print(f"Rate limit exceeded: {e}")
    # Implement retry with backoff
except HuaweiRegionNotSupportedException as e:
    print(f"Region not supported: {e}")
    # Use a supported region
except HuaweiBillingException as e:
    print(f"Huawei billing error: {e}")
```

## Service-Specific Features

### Object Storage Service (OBS)

```python
# Get OBS usage details
obs_usage = client.get_obs_usage(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

for bucket in obs_usage.buckets:
    print(f"Bucket: {bucket.name}")
    print(f"  Storage usage: {bucket.storage_usage_gb:.2f} GB")
    print(f"  Requests: {bucket.request_count}")
    print(f"  Cost: ¥{bucket.cost:.2f}")
```

### Relational Database Service (RDS)

```python
# Get RDS usage details
rds_usage = client.get_rds_usage(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

for instance in rds_usage.instances:
    print(f"RDS Instance: {instance.instance_id}")
    print(f"  Engine: {instance.engine_type}")
    print(f"  Specification: {instance.instance_spec}")
    print(f"  Runtime: {instance.runtime_hours} hours")
    print(f"  Cost: ¥{instance.cost:.2f}")
```

### Cloud Container Engine (CCE)

```python
# Get CCE cluster usage
cce_usage = client.get_cce_usage(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

for cluster in cce_usage.clusters:
    print(f"CCE Cluster: {cluster.cluster_id}")
    print(f"  Node count: {cluster.node_count}")
    print(f"  Runtime: {cluster.runtime_hours} hours")
    print(f"  Cost: ¥{cluster.cost:.2f}")

    # Analyze node usage
    for node in cluster.nodes:
        print(f"    Node: {node.node_id}")
        print(f"      CPU utilization: {node.cpu_utilization:.1f}%")
        print(f"      Memory utilization: {node.memory_utilization:.1f}%")
```

## Best Practices

1. **Project Organization**: Use separate projects for different environments
2. **Region Selection**: Choose regions close to your users for better performance
3. **Resource Tagging**: Use consistent tagging for better cost allocation
4. **Regular Monitoring**: Set up regular billing data collection and analysis
5. **Cost Alerts**: Implement cost monitoring and alerting mechanisms

## Troubleshooting

### Common Issues

**Authentication Errors**
- Verify access key ID and secret access key
- Check project ID and region configuration
- Ensure IAM permissions are correctly set

**Empty Results**
- Verify date range format (YYYY-MM-DD)
- Check if billing data exists for the specified period
- Ensure correct project ID is used

**Service-Specific Errors**
- Some services may not be available in all regions
- Check service activation status in the console

### Required Permissions

Your Huawei Cloud user needs these permissions:

- **BSS Administrator**: For full billing data access
- **BSS Operator**: For read-only billing data access
- **Project-specific roles**: For accessing specific projects

## Performance Tips

1. **Use Appropriate Date Ranges**: Avoid querying large date ranges unnecessarily
2. **Implement Caching**: Cache billing data for frequently accessed periods
3. **Batch Requests**: Group multiple requests when possible
4. **Use Filters**: Apply service and resource filters to reduce data transfer

## See Also

- [API Reference](../api/huawei-cloud.md) - Detailed API documentation
- [Examples](../examples.md) - More usage examples
- [Huawei Cloud Documentation](https://support.huaweicloud.com/)

# Azure

The Azure billing client provides access to cost management and billing data through Azure Cost Management APIs.

## Features

- Cost and usage data retrieval
- Resource-level cost breakdown
- Budget and cost alert integration
- Multiple scope support (subscription, resource group, management group)
- Export functionality for large datasets

## Basic Usage

### Client Initialization

```python
from cloud_billing.azure_cloud import AzureBillingClient

# Using service principal credentials
client = AzureBillingClient(
    subscription_id="your_subscription_id",
    tenant_id="your_tenant_id",
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Using Azure CLI authentication
client = AzureBillingClient(
    subscription_id="your_subscription_id"
)

# Using managed identity (when running on Azure)
client = AzureBillingClient(
    subscription_id="your_subscription_id",
    use_managed_identity=True
)
```

### Getting Billing Data

```python
# Get billing data for a date range
billing_data = client.get_billing_data(
    start_date="2024-01-01",
    end_date="2024-01-31",
    granularity="Daily"  # Daily, Monthly
)

print(f"Total cost: {billing_data.total_cost}")
print(f"Currency: {billing_data.currency}")
print(f"Number of billing items: {len(billing_data.billing_items)}")

# Iterate through billing items
for item in billing_data.billing_items:
    print(f"Resource: {item.resource_name}")
    print(f"Service: {item.service_name}")
    print(f"Cost: {item.cost}")
    print(f"Usage: {item.usage_quantity}")
```

### Resource Group Scoping

```python
# Get costs for a specific resource group
billing_data = client.get_billing_data(
    start_date="2024-01-01",
    end_date="2024-01-31",
    scope="resource_group",
    resource_group_name="my-resource-group"
)

print(f"Resource group cost: {billing_data.total_cost}")
```

## Configuration Options

### Authentication Methods

#### 1. Service Principal
```python
client = AzureBillingClient(
    subscription_id="12345678-1234-1234-1234-123456789012",
    tenant_id="87654321-4321-4321-4321-210987654321",
    client_id="abcd1234-ab12-cd34-ef56-1234567890ab",
    client_secret="your_client_secret"
)
```

#### 2. Environment Variables
```bash
export AZURE_SUBSCRIPTION_ID="12345678-1234-1234-1234-123456789012"
export AZURE_TENANT_ID="87654321-4321-4321-4321-210987654321"
export AZURE_CLIENT_ID="abcd1234-ab12-cd34-ef56-1234567890ab"
export AZURE_CLIENT_SECRET="your_client_secret"
```

```python
client = AzureBillingClient()  # Automatically uses env vars
```

#### 3. Azure CLI
```bash
az login
```

```python
client = AzureBillingClient(
    subscription_id="your_subscription_id",
    use_cli_auth=True
)
```

#### 4. Managed Identity
```python
# When running on Azure VM/Container/Function
client = AzureBillingClient(
    subscription_id="your_subscription_id",
    use_managed_identity=True
)
```

## Advanced Features

### Cost Analysis by Service

```python
# Get costs grouped by service
cost_analysis = client.get_cost_analysis(
    start_date="2024-01-01",
    end_date="2024-01-31",
    group_by="ServiceName",
    granularity="Monthly"
)

for service_cost in cost_analysis.groups:
    print(f"Service: {service_cost.service_name}")
    print(f"Cost: {service_cost.cost}")
```

### Budget Management

```python
# Get budget information
budgets = client.get_budgets()

for budget in budgets:
    print(f"Budget: {budget.name}")
    print(f"Amount: {budget.amount}")
    print(f"Current spend: {budget.current_spend}")
    print(f"Forecasted spend: {budget.forecasted_spend}")

    # Check if budget is exceeded
    if budget.current_spend > budget.amount:
        print(f"⚠️  Budget exceeded by {budget.current_spend - budget.amount}")
```

### Cost Exports

```python
# Create a cost export for large datasets
export_config = {
    "name": "monthly-costs",
    "schedule": "Monthly",
    "format": "Csv",
    "delivery_info": {
        "destination": {
            "resource_id": "/subscriptions/{subscription_id}/resourceGroups/{rg}/providers/Microsoft.Storage/storageAccounts/{storage_account}",
            "container": "cost-exports",
            "root_folder_path": "exports"
        }
    }
}

export_result = client.create_export(export_config)
print(f"Export created: {export_result.name}")
```

## Error Handling

```python
from cloud_billing.azure_cloud.exceptions import (
    AzureBillingException,
    AzureAuthenticationException,
    AzureRateLimitException,
    AzureResourceNotFoundException
)

try:
    billing_data = client.get_billing_data("2024-01-01", "2024-01-31")
except AzureAuthenticationException as e:
    print(f"Azure authentication failed: {e}")
    # Check service principal credentials
except AzureRateLimitException as e:
    print(f"Azure rate limit exceeded: {e}")
    # Implement retry logic
except AzureResourceNotFoundException as e:
    print(f"Resource not found: {e}")
    # Verify subscription ID and resource names
except AzureBillingException as e:
    print(f"Azure billing error: {e}")
```

## Cost Optimization Examples

### Identify Unused Resources

```python
def find_unused_resources(client, start_date, end_date):
    billing_data = client.get_billing_data(start_date, end_date)

    # Resources with zero usage
    unused_resources = []

    for item in billing_data.billing_items:
        if item.usage_quantity == 0 and item.cost > 0:
            unused_resources.append({
                'resource_name': item.resource_name,
                'service': item.service_name,
                'cost': item.cost
            })

    return sorted(unused_resources, key=lambda x: x['cost'], reverse=True)

# Usage
unused = find_unused_resources(client, "2024-01-01", "2024-01-31")
total_waste = sum(resource['cost'] for resource in unused)

print(f"Potentially unused resources costing ${total_waste:.2f}:")
for resource in unused[:10]:  # Top 10
    print(f"  {resource['resource_name']} ({resource['service']}): ${resource['cost']:.2f}")
```

### Cost Trend Analysis

```python
from datetime import datetime, timedelta

def analyze_cost_trends(client, months=6):
    trends = []

    for i in range(months):
        end_date = datetime.now().replace(day=1) - timedelta(days=i*30)
        start_date = end_date.replace(day=1)

        billing_data = client.get_billing_data(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )

        trends.append({
            'month': start_date.strftime("%Y-%m"),
            'cost': billing_data.total_cost
        })

    # Calculate month-over-month growth
    for i in range(1, len(trends)):
        prev_cost = trends[i-1]['cost']
        curr_cost = trends[i]['cost']
        growth = ((curr_cost - prev_cost) / prev_cost) * 100 if prev_cost > 0 else 0
        trends[i]['growth'] = growth

    return sorted(trends, key=lambda x: x['month'])

# Usage
trends = analyze_cost_trends(client)
for trend in trends:
    growth_str = f" ({trend['growth']:+.1f}%)" if 'growth' in trend else ""
    print(f"{trend['month']}: ${trend['cost']:.2f}{growth_str}")
```

### Resource Optimization Recommendations

```python
def get_optimization_recommendations(client, start_date, end_date):
    billing_data = client.get_billing_data(start_date, end_date)
    recommendations = []

    # Group by resource type
    resource_costs = {}
    for item in billing_data.billing_items:
        resource_type = item.service_name
        if resource_type not in resource_costs:
            resource_costs[resource_type] = []
        resource_costs[resource_type].append(item)

    # Analyze each resource type
    for resource_type, items in resource_costs.items():
        total_cost = sum(item.cost for item in items)
        avg_utilization = sum(item.usage_quantity for item in items) / len(items)

        # Low utilization recommendation
        if avg_utilization < 20 and total_cost > 100:  # Thresholds
            recommendations.append({
                'type': 'Right-sizing',
                'resource_type': resource_type,
                'current_cost': total_cost,
                'potential_savings': total_cost * 0.3,  # Estimated 30% savings
                'recommendation': f'Consider right-sizing {resource_type} resources due to low utilization'
            })

    return sorted(recommendations, key=lambda x: x['potential_savings'], reverse=True)

# Usage
recommendations = get_optimization_recommendations(client, "2024-01-01", "2024-01-31")
total_potential_savings = sum(rec['potential_savings'] for rec in recommendations)

print(f"Potential monthly savings: ${total_potential_savings:.2f}")
for rec in recommendations:
    print(f"  {rec['type']}: {rec['recommendation']}")
    print(f"    Potential savings: ${rec['potential_savings']:.2f}")
```

## Best Practices

1. **Use Appropriate Scopes**: Choose the right scope (subscription, resource group) for your analysis
2. **Cache Data**: Implement caching for frequently accessed billing data
3. **Handle Rate Limits**: Azure has rate limits on Cost Management APIs
4. **Use Service Principal**: For automated scenarios, use service principal authentication
5. **Monitor Budgets**: Set up budgets and alerts for cost control

## Troubleshooting

### Common Issues

**Authentication Errors**
- Verify service principal credentials
- Check Azure AD permissions
- Ensure correct tenant and subscription IDs

**Permission Errors**
- Grant "Cost Management Reader" role at appropriate scope
- For budget operations, grant "Cost Management Contributor" role

**Empty Results**
- Verify date range format (YYYY-MM-DD)
- Check if Cost Management is enabled
- Ensure subscription has billing data

### Required Azure Permissions

Your service principal needs these roles:

- **Cost Management Reader**: For reading cost data
- **Cost Management Contributor**: For managing budgets and exports
- **Reader**: For accessing resource metadata

```bash
# Assign Cost Management Reader role
az role assignment create \
  --assignee <service-principal-id> \
  --role "Cost Management Reader" \
  --scope "/subscriptions/<subscription-id>"
```

## See Also

- [API Reference](../api/azure.md) - Detailed API documentation
- [Examples](../examples.md) - More usage examples
- [Azure Cost Management Documentation](https://docs.microsoft.com/en-us/azure/cost-management-billing/)

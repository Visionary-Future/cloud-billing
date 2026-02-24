# Examples

This page provides practical examples of using the Cloud Billing package.

## Alibaba Cloud Billing Analysis

Get and analyze Alibaba Cloud billing data:

```python
from cloud_billing.alibaba_cloud import AlibabaCloudClient

def analyze_alibaba_billing(billing_cycle: str):
    """
    Analyze Alibaba Cloud billing data for a specific month

    Args:
        billing_cycle: Format YYYY-MM (e.g., "2024-01")
    """
    client = AlibabaCloudClient(
        access_key_id="your_access_key_id",
        access_key_secret="your_access_key_secret"
    )

    # Get billing data
    billing_data = client.fetch_instance_bill_by_billing_cycle(
        billing_cycle=billing_cycle
    )

    # Analyze costs by service
    service_costs = {}
    for record in billing_data:
        service = record.ProductName
        cost = float(record.PreTaxAmount)

        if service in service_costs:
            service_costs[service] += cost
        else:
            service_costs[service] = cost

    # Sort by cost
    sorted_services = sorted(
        service_costs.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return sorted_services

# Usage
services = analyze_alibaba_billing("2024-01")
print("Services by cost:")
for service, cost in services:
    print(f"  {service}: ¥{cost:.2f}")
```

## Azure Reserved Instance Reporting

Retrieve and process Azure RI billing reports:

```python
from cloud_billing.azure_cloud import AzureCloudClient

def get_azure_ri_report(billing_account_id: str, start_date: str, end_date: str):
    """
    Get Azure Reserved Instance billing report

    Args:
        billing_account_id: Azure billing account ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    client = AzureCloudClient(
        tenant_id="your_tenant_id",
        client_id="your_client_id",
        client_secret="your_client_secret"
    )

    # Get access token
    token, error = client.get_access_token()
    if error:
        print(f"Authentication failed: {error}")
        return None

    # Request report generation
    location_url, error = client.get_ri_location(
        billing_account_id=billing_account_id,
        start_date=start_date,
        end_date=end_date,
        metric="ActualCost"
    )

    if error:
        print(f"Report request failed: {error}")
        return None

    # Poll for CSV download URL
    csv_url, error = client.get_ri_csv_url(
        location_url=location_url,
        max_retries=20
    )

    if error:
        print(f"CSV generation failed: {error}")
        return None

    # Download and parse CSV
    total_cost = 0.0
    service_costs = {}

    for billing_record, error in client.get_ri_csv_as_json(location_url):
        if error:
            print(f"CSV parsing error: {error}")
            continue

        service = billing_record.ProductName
        cost = float(billing_record.PreTaxAmount)
        total_cost += cost

        if service in service_costs:
            service_costs[service] += cost
        else:
            service_costs[service] = cost

    return {
        'total_cost': total_cost,
        'service_breakdown': service_costs,
        'period': f"{start_date} to {end_date}"
    }

# Usage
report = get_azure_ri_report(
    "123456789",
    "2024-01-01",
    "2024-01-31"
)

if report:
    print(f"Total RI Cost: ${report['total_cost']:.2f}")
    print(f"Period: {report['period']}")
    print("\nCost by service:")
    for service, cost in report['service_breakdown'].items():
        print(f"  {service}: ${cost:.2f}")
```

## Monthly Cost Trend Analysis

Track costs over multiple months with Alibaba Cloud:

```python
from datetime import datetime, timedelta
from cloud_billing.alibaba_cloud import AlibabaCloudClient

def track_monthly_costs(months: int = 6):
    """Track Alibaba Cloud costs for the last N months"""
    client = AlibabaCloudClient()
    monthly_costs = []

    for i in range(months):
        # Calculate billing cycle (YYYY-MM format)
        current_date = datetime.now()
        target_month = current_date - timedelta(days=i*30)
        billing_cycle = target_month.strftime("%Y-%m")

        # Get billing data
        billing_data = client.fetch_instance_bill_by_billing_cycle(
            billing_cycle=billing_cycle
        )

        # Sum costs
        total_cost = sum(float(record.PreTaxAmount) for record in billing_data)

        monthly_costs.append({
            'month': billing_cycle,
            'cost': total_cost,
            'record_count': len(billing_data)
        })

    return monthly_costs

# Usage
costs = track_monthly_costs(6)
for month_data in costs:
    print(f"{month_data['month']}: ¥{month_data['cost']:.2f} ({month_data['record_count']} records)")
```

## Cost Alerting System

Monitor Alibaba Cloud costs with threshold-based alerting:

```python
from cloud_billing.alibaba_cloud import AlibabaCloudClient
from datetime import datetime

def check_monthly_cost_threshold(threshold: float):
    """Check if current month costs exceed threshold"""
    client = AlibabaCloudClient()

    # Get current month billing cycle
    now = datetime.now()
    billing_cycle = now.strftime("%Y-%m")

    # Get billing data
    billing_data = client.fetch_instance_bill_by_billing_cycle(
        billing_cycle=billing_cycle
    )

    # Calculate total cost
    total_cost = sum(float(record.PreTaxAmount) for record in billing_data)

    if total_cost > threshold:
        return {
            'alert': True,
            'current_cost': total_cost,
            'threshold': threshold,
            'overage': total_cost - threshold
        }

    return {
        'alert': False,
        'current_cost': total_cost,
        'threshold': threshold
    }

# Usage
alert_status = check_monthly_cost_threshold(1000.0)
if alert_status['alert']:
    print(f"⚠️  ALERT: Cost ¥{alert_status['current_cost']:.2f} exceeds threshold ¥{alert_status['threshold']:.2f}")
    print(f"   Overage: ¥{alert_status['overage']:.2f}")
else:
    print(f"✓ Cost within threshold: ¥{alert_status['current_cost']:.2f} / ¥{alert_status['threshold']:.2f}")
```

## Batch Processing Multiple Accounts

Process billing data for multiple Alibaba Cloud accounts:

```python
from cloud_billing.alibaba_cloud import AlibabaCloudClient
import concurrent.futures
from typing import List, Dict

def process_account_billing(account_config: Dict) -> Dict:
    """Process billing for a single Alibaba Cloud account"""
    client = AlibabaCloudClient(
        access_key_id=account_config['access_key_id'],
        access_key_secret=account_config['access_key_secret'],
        region_id=account_config.get('region_id', 'cn-hangzhou')
    )

    billing_data = client.fetch_instance_bill_by_billing_cycle(
        billing_cycle=account_config['billing_cycle']
    )

    total_cost = sum(float(record.PreTaxAmount) for record in billing_data)

    return {
        'account_name': account_config['name'],
        'total_cost': total_cost,
        'record_count': len(billing_data),
        'billing_cycle': account_config['billing_cycle']
    }

def process_multiple_accounts(accounts: List[Dict]) -> List[Dict]:
    """Process billing for multiple accounts in parallel"""
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_account = {
            executor.submit(process_account_billing, account): account
            for account in accounts
        }

        for future in concurrent.futures.as_completed(future_to_account):
            account = future_to_account[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing account {account['name']}: {e}")

    return results

# Usage
accounts = [
    {
        'name': 'Production',
        'access_key_id': 'prod_key',
        'access_key_secret': 'prod_secret',
        'billing_cycle': '2024-01'
    },
    {
        'name': 'Development',
        'access_key_id': 'dev_key',
        'access_key_secret': 'dev_secret',
        'billing_cycle': '2024-01'
    }
]

results = process_multiple_accounts(accounts)
total_cost = sum(result['total_cost'] for result in results)

print(f"Total cost across all accounts: ¥{total_cost:.2f}")
for result in results:
    print(f"  {result['account_name']}: ¥{result['total_cost']:.2f} ({result['record_count']} records)")
```

## Kubecost Integration

Retrieve Kubernetes cost allocation data using Kubecost:

```python
from cloud_billing.kubecost import KubecostClient

def get_k8s_cost_allocation(kubecost_url: str, namespace: str = None):
    """
    Get Kubernetes cost allocation data from Kubecost

    Args:
        kubecost_url: URL to Kubecost instance (e.g., http://kubecost:9090)
        namespace: Optional namespace filter
    """
    client = KubecostClient(kubecost_url=kubecost_url)

    # Get allocation data
    allocation_data = client.get_allocation()

    if not allocation_data:
        print("Failed to retrieve allocation data")
        return None

    # Filter by namespace if specified
    if namespace:
        allocation_data = [
            item for item in allocation_data
            if item.get('namespace') == namespace
        ]

    # Calculate costs
    total_cost = sum(item.get('totalCost', 0) for item in allocation_data)

    return {
        'total_cost': total_cost,
        'item_count': len(allocation_data),
        'items': allocation_data
    }

# Usage
kubecost_data = get_k8s_cost_allocation(
    "http://kubecost.monitoring:9090",
    namespace="production"
)

if kubecost_data:
    print(f"Kubernetes costs in 'production' namespace: ${kubecost_data['total_cost']:.2f}")
    print(f"Number of cost items: {kubecost_data['item_count']}")
```

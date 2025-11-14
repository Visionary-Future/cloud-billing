# Examples

This page provides practical examples of using the Cloud Billing package.

## Multi-Cloud Cost Comparison

Compare costs across different cloud providers:

```python
from cloud_billing.alibaba_cloud import AlibabaCloudClient
from cloud_billing.aws_cloud import AWSCloudClient
from cloud_billing.azure_cloud import AzureCloudClient

async def compare_cloud_costs(start_date: str, end_date: str):
    # Initialize clients
    alibaba_client = AlibabaCloudClient()
    aws_client = AWSCloudClient()
    azure_client = AzureCloudClient()

    # Get billing data from all providers
    alibaba_data = alibaba_client.get_billing_data(start_date, end_date)
    aws_data = aws_client.get_cost_and_usage(start_date, end_date)
    azure_data = azure_client.get_billing_data(start_date, end_date)

    # Compare costs
    costs = {
        'Alibaba Cloud': alibaba_data.total_cost,
        'AWS': aws_data.total_cost,
        'Azure': azure_data.total_cost
    }

    return costs

# Usage
costs = compare_cloud_costs("2024-01-01", "2024-01-31")
for provider, cost in costs.items():
    print(f"{provider}: ${cost:.2f}")
```

## Monthly Cost Tracking

Track costs over multiple months:

```python
from datetime import datetime, timedelta
from cloud_billing.alibaba_cloud import AlibabaCloudClient

def track_monthly_costs(months: int = 6):
    client = AlibabaCloudClient()
    monthly_costs = []

    for i in range(months):
        # Calculate month start and end dates
        end_date = datetime.now().replace(day=1) - timedelta(days=i*30)
        start_date = end_date.replace(day=1)

        # Get billing data
        billing_data = client.get_billing_data(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )

        monthly_costs.append({
            'month': start_date.strftime("%Y-%m"),
            'cost': billing_data.total_cost,
            'services': len(billing_data.services)
        })

    return monthly_costs

# Usage
costs = track_monthly_costs(6)
for month_data in costs:
    print(f"{month_data['month']}: ${month_data['cost']:.2f} ({month_data['services']} services)")
```

## Service-Level Cost Analysis

Analyze costs by service for Alibaba Cloud:

```python
from cloud_billing.alibaba_cloud import AlibabaCloudClient

def analyze_service_costs(start_date: str, end_date: str):
    client = AlibabaCloudClient()
    billing_data = client.get_billing_data(start_date, end_date)

    # Group costs by service
    service_costs = {}
    for item in billing_data.billing_items:
        service = item.product_name
        cost = item.cost

        if service in service_costs:
            service_costs[service] += cost
        else:
            service_costs[service] = cost

    # Sort by cost (highest first)
    sorted_services = sorted(
        service_costs.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return sorted_services

# Usage
services = analyze_service_costs("2024-01-01", "2024-01-31")
print("Top 5 most expensive services:")
for service, cost in services[:5]:
    print(f"{service}: ${cost:.2f}")
```

## Kubernetes Billing with Alibaba Cloud

Get detailed Kubernetes billing information:

```python
from cloud_billing.alibaba_cloud import K8sBillingClient

def get_k8s_cluster_costs(cluster_id: str, start_date: str, end_date: str):
    client = K8sBillingClient()

    # Get cluster billing details
    cluster_billing = client.get_cluster_billing(
        cluster_id=cluster_id,
        start_date=start_date,
        end_date=end_date
    )

    # Analyze by namespace
    namespace_costs = {}
    for item in cluster_billing.billing_items:
        namespace = item.namespace
        cost = item.cost

        if namespace in namespace_costs:
            namespace_costs[namespace] += cost
        else:
            namespace_costs[namespace] = cost

    return {
        'total_cost': cluster_billing.total_cost,
        'namespace_breakdown': namespace_costs,
        'node_count': cluster_billing.node_count,
        'billing_period': f"{start_date} to {end_date}"
    }

# Usage
cluster_costs = get_k8s_cluster_costs(
    "c-123abc456def",
    "2024-01-01",
    "2024-01-31"
)

print(f"Total cluster cost: ${cluster_costs['total_cost']:.2f}")
print(f"Nodes: {cluster_costs['node_count']}")
print("\nCost by namespace:")
for namespace, cost in cluster_costs['namespace_breakdown'].items():
    print(f"  {namespace}: ${cost:.2f}")
```

## Cost Alerting System

Simple cost alerting based on thresholds:

```python
from cloud_billing.alibaba_cloud import AlibabaCloudClient
import smtplib
from email.mime.text import MIMEText

def check_cost_alerts(threshold: float, email_to: str):
    client = AlibabaCloudClient()

    # Get current month costs
    from datetime import datetime
    now = datetime.now()
    start_date = now.replace(day=1).strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")

    billing_data = client.get_billing_data(start_date, end_date)
    current_cost = billing_data.total_cost

    if current_cost > threshold:
        send_cost_alert(current_cost, threshold, email_to)
        return True

    return False

def send_cost_alert(current_cost: float, threshold: float, email_to: str):
    subject = "Cloud Cost Alert"
    body = f"""
    Your cloud costs have exceeded the threshold!

    Current month cost: ${current_cost:.2f}
    Threshold: ${threshold:.2f}
    Overage: ${current_cost - threshold:.2f}

    Please review your resource usage.
    """

    # Configure your SMTP settings
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = "alerts@yourcompany.com"
    msg['To'] = email_to

    # Send email (configure SMTP server details)
    # with smtplib.SMTP('smtp.yourserver.com', 587) as server:
    #     server.send_message(msg)

    print(f"Alert sent: Cost ${current_cost:.2f} exceeds threshold ${threshold:.2f}")

# Usage
alert_triggered = check_cost_alerts(1000.0, "admin@yourcompany.com")
```

## Batch Processing Multiple Accounts

Process billing data for multiple accounts:

```python
from cloud_billing.alibaba_cloud import AlibabaCloudClient
import concurrent.futures
from typing import List, Dict

def process_account_billing(account_config: Dict) -> Dict:
    """Process billing for a single account"""
    client = AlibabaCloudClient(
        access_key_id=account_config['access_key_id'],
        access_key_secret=account_config['access_key_secret'],
        region_id=account_config.get('region_id', 'cn-hangzhou')
    )

    billing_data = client.get_billing_data(
        account_config['start_date'],
        account_config['end_date']
    )

    return {
        'account_name': account_config['name'],
        'total_cost': billing_data.total_cost,
        'service_count': len(billing_data.services),
        'billing_items': len(billing_data.billing_items)
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
        'start_date': '2024-01-01',
        'end_date': '2024-01-31'
    },
    {
        'name': 'Development',
        'access_key_id': 'dev_key',
        'access_key_secret': 'dev_secret',
        'start_date': '2024-01-01',
        'end_date': '2024-01-31'
    }
]

results = process_multiple_accounts(accounts)
total_cost = sum(result['total_cost'] for result in results)

print(f"Total cost across all accounts: ${total_cost:.2f}")
for result in results:
    print(f"{result['account_name']}: ${result['total_cost']:.2f}")
```

# Huawei Cloud

The Huawei Cloud billing client provides access to monthly bill summary data through the Huawei BSS (Business Support System) API.

## Features

- Monthly bill summary retrieval with `query_monthly_bill_summary()`
- Automatic pagination via offset/limit
- Detailed cost breakdown (cash, coupon, credit, stored-value card)
- Service-level cost analysis
- SDK-based authentication with AK/SK

## Basic Usage

### Client Initialization

```python
from cloud_billing.huawei_cloud import HuaweiCloudClient

client = HuaweiCloudClient(
    access_key="your_access_key",
    secret_key="your_secret_key",
    domain_id="your_domain_id",
    region_id="cn-east-3",  # Optional, defaults to cn-east-3
)
```

### Getting Monthly Bill Summary

```python
bill_items, error = client.query_monthly_bill_summary(bill_cycle="2024-01")

if error:
    print(f"Error: {error}")
else:
    print(f"Found {len(bill_items)} bill entries")

    for item in bill_items:
        print(f"Service: {item.service_type_name or 'Unknown'}")
        print(f"  Consume: ¥{item.consume_amount}")
        print(f"  Cash: ¥{item.cash_amount}")
        print(f"  Coupon: ¥{item.coupon_amount}")
```

### Cost Analysis by Service

```python
from collections import defaultdict

bill_items, error = client.query_monthly_bill_summary(bill_cycle="2024-01")

if not error:
    service_costs = defaultdict(float)
    for item in bill_items:
        name = item.service_type_name or item.service_type_code or "Unknown"
        total = item.consume_amount + item.cash_amount + item.stored_value_card_amount
        service_costs[name] += total

    for service, cost in sorted(service_costs.items(), key=lambda x: x[1], reverse=True):
        print(f"{service}: ¥{cost:.2f}")
```

## Pagination

The client automatically handles pagination using the `offset`/`limit` parameters:

```python
# All pages are fetched via recursive pagination
bill_items, error = client.query_monthly_bill_summary(bill_cycle="2024-01")
print(f"Total entries: {len(bill_items)}")

# Custom page size
bill_items, error = client.query_monthly_bill_summary(
    bill_cycle="2024-01",
    limit=200,  # Max 1000 per page
)
```

## Configuration

### Authentication

The client requires AK/SK credentials and a domain ID:

```python
client = HuaweiCloudClient(
    access_key="your_access_key",
    secret_key="your_secret_key",
    domain_id="your_domain_id",
)
```

Credentials can also be provided via environment variables:

```bash
export HUAWEI_ACCESS_KEY="your_access_key"
export HUAWEI_SECRET_KEY="your_secret_key"
export HUAWEI_DOMAIN_ID="your_domain_id"
```

### Supported Regions

The BSS API is global and not region-specific, but the `region_id` parameter can be set for logging purposes:

- `cn-east-3` - Shanghai 1 (default)
- `cn-north-1` - Beijing 1
- `cn-north-4` - Beijing 4
- `cn-east-2` - Shanghai 2
- `cn-south-1` - Guangzhou

### Required IAM Permissions

The user must have the `billing:bill:view` permission.

## Error Handling

The client uses the `(data, error)` tuple pattern:

```python
bill_items, error = client.query_monthly_bill_summary(bill_cycle="2024-01")

if error:
    print(f"Billing query failed: {error}")
    return

if not bill_items:
    print("No billing data found for this cycle.")
    return

for item in bill_items:
    print(f"{item.service_type_name}: ¥{item.consume_amount}")
```

Invalid billing cycle format raises a `ValueError`:

```python
try:
    client.query_monthly_bill_summary(bill_cycle="bad-format")
except ValueError as e:
    print(f"Invalid format: {e}")
```

## Bill Item Fields

Each `MonthlyBillItem` contains:

| Field | Type | Description |
|-------|------|-------------|
| `bill_cycle` | str | Billing cycle (YYYY-MM) |
| `consume_amount` | float | Total consumed amount |
| `cash_amount` | float | Cash payment amount |
| `credit_amount` | float | Credit amount |
| `coupon_amount` | float | Coupon discount amount |
| `debt_amount` | float | Outstanding debt |
| `stored_value_card_amount` | float | Stored-value card amount |
| `flexipurchase_coupon_amount` | float | Flexible purchase coupon |
| `writeoff_amount` | float | Write-off amount |
| `service_type_code` | str | Service type code (e.g., `hws.service.type.ec2`) |
| `service_type_name` | str | Service type display name |
| `resource_type_code` | str | Resource type code |
| `resource_type_name` | str | Resource type display name |
| `official_amount` | float | Official (list) price |
| `official_discount_amount` | float | Discount from official price |

## Troubleshooting

### Common Issues

**Authentication Errors**
- Verify access key and secret key
- Ensure the domain ID is correct
- Check that the account has BSS API permissions

**Empty Results**
- Verify billing cycle format is YYYY-MM
- Billing data may have a 1-2 day delay
- Ensure the account has actual usage in the billing cycle

**SDK Import Errors**
- Ensure `huaweicloudsdkbss` and `huaweicloudsdkcore` are installed:
  ```bash
  pip install huaweicloudsdkbss huaweicloudsdkcore
  ```

## See Also

- [API Reference](../api/aws.md) - Auto-generated API documentation
- [Examples](../examples.md) - More usage examples
- [Huawei Cloud BSS API Documentation](https://support.huaweicloud.com/intl/en-us/api-oce/mac_00001.html)

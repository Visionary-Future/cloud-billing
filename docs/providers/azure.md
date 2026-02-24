# Azure

> ⚠️ **Implementation Focus**: This Azure client is specifically designed for **Reserved Instance (RI) billing reports** from Azure Cost Management. It's optimized for Azure China environments.

The Azure billing client provides access to Reserved Instance billing data through Azure Cost Management APIs.

## Features

- Reserved Instance billing report retrieval
- Automated report generation and polling
- CSV download and parsing
- Service principal authentication
- Support for Azure China endpoints

## Basic Usage

### Client Initialization

```python
from cloud_billing.azure_cloud import AzureCloudClient

# Create client with service principal credentials
client = AzureCloudClient(
    tenant_id="your_tenant_id",
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Get access token
token, error = client.get_access_token()
if error:
    print(f"Authentication failed: {error}")
else:
    print(f"Token acquired successfully")
```

### Retrieving RI Billing Reports

```python
# Step 1: Request RI billing report generation
location_url, error = client.get_ri_location(
    billing_account_id="your_billing_account_id",
    start_date="2024-01-01",
    end_date="2024-01-31",
    metric="ActualCost"
)

if error:
    print(f"Error requesting report: {error}")
    exit(1)

# Step 2: Poll for report CSV download URL
csv_url, error = client.get_ri_csv_url(
    location_url=location_url,
    max_retries=10  # Retry up to 10 times
)

if error:
    print(f"Error getting CSV URL: {error}")
    exit(1)

# Step 3: Download and parse CSV
for billing_record, error in client.get_ri_csv_as_json(
    location_url=location_url
):
    if error:
        print(f"Error processing record: {error}")
        continue

    print(f"Service: {billing_record.ProductName}")
    print(f"Cost: {billing_record.PreTaxAmount}")
```

## API Methods

### get_access_token()

Retrieves an Azure access token for API authentication.

```python
token, error = client.get_access_token()
if not error:
    print(f"Access token obtained")
```

### refresh_token()

Refreshes the current access token.

```python
token, error = client.refresh_token()
```

### get_ri_location(billing_account_id, start_date, end_date, metric)

Requests a Reserved Instance billing report and returns the polling URL.

```python
location_url, error = client.get_ri_location(
    billing_account_id="123456789",
    start_date="2024-01-01",
    end_date="2024-01-31",
    metric="ActualCost"
)
```

### get_ri_csv_url(location_url, max_retries)

Polls for report generation and returns the CSV download URL.

```python
csv_url, error = client.get_ri_csv_url(
    location_url=location_url,
    max_retries=10
)
```

### get_ri_csv_as_json(location_url, max_retries)

Downloads and parses the RI billing CSV, yielding BillingRecord objects.

```python
for record, error in client.get_ri_csv_as_json(location_url=location_url):
    if not error:
        print(f"Cost: {record.PreTaxAmount}")
```

### download_ri_csv(csv_url)

Downloads the raw CSV file content.

```python
csv_content, error = client.download_ri_csv(csv_url=csv_url)
if not error:
    with open("billing_report.csv", "wb") as f:
        f.write(csv_content)
```

## Error Handling

The client returns error messages through tuple returns:

```python
token, error = client.get_access_token()
if error:
    print(f"Error: {error}")
    # Handle authentication failure

try:
    for billing_record, error in client.get_ri_csv_as_json(location_url):
        if error:
            print(f"CSV parsing error: {error}")
            continue
        # Process record
except Exception as e:
    print(f"Request failed: {e}")
```

## Best Practices

1. **Handle Errors**: Check return values for error tuples
2. **Polling**: Use reasonable retry limits for CSV generation (typically 10-30 retries)
3. **Rate Limiting**: Azure has rate limits on Cost Management APIs
4. **Credential Security**: Use environment variables for sensitive credentials
5. **DateTime Formatting**: Always use YYYY-MM-DD format for dates

## Troubleshooting

### Common Issues

**Authentication Errors**
- Verify service principal credentials (tenant_id, client_id, client_secret)
- Ensure the service principal has access to Azure resources
- Check if tokens are being refreshed properly

**Report Generation Timeout**
- Azure may take time to generate RI reports
- Increase max_retries in get_ri_csv_url()
- Consider implementing exponential backoff for retries

**CSV Parsing Errors**
- Verify the report structure matches expected schema
- Check for encoding issues in CSV content
- Ensure date ranges have actual billing data

### Required Azure Permissions

Your service principal needs these roles:

- **Cost Management Reader**: For reading billing data
- **Co-Administrator**: For accessing Cost Management APIs (Azure China)

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

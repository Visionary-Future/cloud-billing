# Export Billing Data to CSV

The `scripts/export_billing_to_csv.py` script allows you to export billing data from Alibaba Cloud or Azure to CSV format for a specified month.

## Features

- **Multi-cloud support** - Export from Alibaba Cloud or Azure
- **Monthly exports** - Specify any month in YYYY-MM format
- **Environment variable support** - Use credentials from environment variables for security
- **Flexible output** - Save to custom file paths

## Prerequisites

1. Install the cloud-billing package with dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Have valid cloud provider credentials:
   - **Alibaba Cloud**: Access Key ID and Secret
   - **Azure**: Tenant ID, Client ID, Client Secret, and Billing Account ID

## Usage

### Export Alibaba Cloud Billing Data

#### Using command-line arguments:
```bash
python scripts/export_billing_to_csv.py \
  --provider alibaba \
  --month 2025-10 \
  --access-key-id YOUR_KEY_ID \
  --access-key-secret YOUR_SECRET \
  --region-id cn-hangzhou \
  --output alibaba_billing.csv
```

#### Using environment variables (recommended):
```bash
export ALIBABA_ACCESS_KEY_ID="your_key_id"
export ALIBABA_ACCESS_KEY_SECRET="your_secret"

python scripts/export_billing_to_csv.py \
  --provider alibaba \
  --month 2025-10 \
  --region-id cn-hangzhou
```

The output file will default to `alibaba_billing_2025-10.csv` if not specified.

### Export Azure Billing Data

#### Using command-line arguments:
```bash
python scripts/export_billing_to_csv.py \
  --provider azure \
  --month 2025-10 \
  --tenant-id YOUR_TENANT_ID \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_SECRET \
  --billing-account-id YOUR_BILLING_ACCOUNT_ID \
  --output azure_billing.csv
```

#### Using environment variables (recommended):
```bash
export AZURE_TENANT_ID="your_tenant_id"
export AZURE_CLIENT_ID="your_client_id"
export AZURE_CLIENT_SECRET="your_secret"

python scripts/export_billing_to_csv.py \
  --provider azure \
  --month 2025-10 \
  --billing-account-id YOUR_BILLING_ACCOUNT_ID
```

The output file will default to `azure_billing_2025-10.csv` if not specified.

## Command Options

### Common Options
- `--provider`: Cloud provider - `alibaba` or `azure` (required)
- `--month`: Billing month in YYYY-MM format (required, e.g., 2025-10)
- `--output`: Output CSV file path (optional, defaults to `{provider}_billing_{month}.csv`)

### Alibaba Cloud Options
- `--access-key-id`: Alibaba Cloud Access Key ID (or set `ALIBABA_ACCESS_KEY_ID` env var)
- `--access-key-secret`: Alibaba Cloud Access Key Secret (or set `ALIBABA_ACCESS_KEY_SECRET` env var)
- `--region-id`: Alibaba Cloud region ID (default: cn-hangzhou)

### Azure Options
- `--tenant-id`: Azure Tenant ID (or set `AZURE_TENANT_ID` env var)
- `--client-id`: Azure Client ID (or set `AZURE_CLIENT_ID` env var)
- `--client-secret`: Azure Client Secret (or set `AZURE_CLIENT_SECRET` env var)
- `--billing-account-id`: Azure Billing Account ID (required)

## Examples

### Export multiple months of Alibaba Cloud data
```bash
for month in 2025-08 2025-09 2025-10; do
  python scripts/export_billing_to_csv.py \
    --provider alibaba \
    --month $month \
    --region-id cn-hangzhou
done
```

### Export Azure data with custom output location
```bash
python scripts/export_billing_to_csv.py \
  --provider azure \
  --month 2025-10 \
  --billing-account-id "00000000-0000-0000-0000-000000000000" \
  --output /path/to/exports/azure_oct_2025.csv
```

## Output Format

### Alibaba Cloud CSV

The CSV contains the following columns from `QueryInstanceBillItem`:
- Invoice ID
- Billing Cycle
- Billing Date
- Product Name
- Instance ID
- Instance Name
- Usage Amount
- Usage Unit
- Currency
- Cost (in billing currency)
- And other related fields

### Azure CSV

The CSV contains detailed billing records with:
- Invoice ID
- Billing Period
- Service Name
- Resource Group
- Resource ID
- Quantity
- Unit Price
- Cost in Billing Currency
- And other cost details

## Error Handling

The script will log errors to the console. Common issues:

1. **Missing credentials**: Ensure all required credentials are provided either via arguments or environment variables
2. **Invalid month format**: Use YYYY-MM format (e.g., 2025-10)
3. **Missing dependencies**: Install requirements: `pip install -r requirements.txt`
4. **Authentication failures**: Verify your cloud provider credentials are correct and have appropriate permissions

## Performance Notes

- **Alibaba Cloud**: Large months may take a few seconds to fetch and process
- **Azure**: CSV download time depends on data size; the script polls for report generation

## Security Best Practices

1. **Use environment variables** instead of command-line arguments to avoid exposing credentials in shell history
2. **Rotate credentials regularly** with your cloud provider
3. **Store CSV files securely** as they contain cost/billing information
4. **Use `--output`** to save files in a secure directory with appropriate permissions

## Troubleshooting

### "ModuleNotFoundError: No module named 'cloud_billing'"
Install the package: `pip install -e .` or `pip install -r requirements.txt`

### "No billing data found for {month}"
- Verify the month is in YYYY-MM format
- Ensure there is actual billing data for that month in your cloud account
- Check that credentials have access to billing APIs

### Azure "Failed to download CSV"
- Verify the Billing Account ID is correct
- Check that your service principal has access to the billing account
- Ensure the date range includes valid billing data

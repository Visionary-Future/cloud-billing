#!/usr/bin/env python3
"""
Export billing data from Alibaba Cloud or Azure to CSV file.

Supports exporting billing data for a specified month to CSV format.

Usage examples:
  # Export Alibaba Cloud data for 2025-10
  python scripts/export_billing_to_csv.py --provider alibaba --month 2025-10 \
    --access-key-id YOUR_KEY_ID --access-key-secret YOUR_SECRET --region-id cn-hangzhou

  # Export Alibaba Cloud data (using environment variables)
  export ALIBABA_ACCESS_KEY_ID=YOUR_KEY_ID
  export ALIBABA_ACCESS_KEY_SECRET=YOUR_SECRET
  python scripts/export_billing_to_csv.py --provider alibaba --month 2025-10 --region-id cn-hangzhou

  # Export Azure data for 2025-10
  python scripts/export_billing_to_csv.py --provider azure --month 2025-10 \
    --tenant-id YOUR_TENANT --client-id YOUR_CLIENT_ID --client-secret YOUR_SECRET \
    --billing-account-id YOUR_BILLING_ACCOUNT_ID

  # Export Azure data (using environment variables)
  export AZURE_TENANT_ID=YOUR_TENANT
  export AZURE_CLIENT_ID=YOUR_CLIENT_ID
  export AZURE_CLIENT_SECRET=YOUR_SECRET
  python scripts/export_billing_to_csv.py --provider azure --month 2025-10 \
    --billing-account-id YOUR_BILLING_ACCOUNT_ID
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def export_alibaba_cloud(
    month: str,
    access_key_id: Optional[str] = None,
    access_key_secret: Optional[str] = None,
    region_id: str = "cn-hangzhou",
    output_file: Optional[str] = None,
) -> bool:
    """
    Export Alibaba Cloud billing data for specified month to CSV.

    Args:
        month: Billing month in format YYYY-MM (e.g., 2025-10)
        access_key_id: Alibaba Cloud Access Key ID (or read from ALIBABA_ACCESS_KEY_ID env)
        access_key_secret: Alibaba Cloud Access Key Secret (or read from ALIBABA_ACCESS_KEY_SECRET env)
        region_id: Alibaba Cloud region ID (default: cn-hangzhou)
        output_file: Output CSV file path (default: alibaba_billing_{month}.csv)

    Returns:
        bool: True if successful, False if error
    """
    try:
        from cloud_billing.alibaba_cloud import AlibabaCloudClient
    except ImportError as e:
        logger.error(f"Failed to import Alibaba Cloud client: {e}")
        logger.error("Make sure to install dependencies: pip install -r requirements.txt")
        return False

    # Get credentials from arguments or environment
    key_id = access_key_id or os.environ.get("ALIBABA_ACCESS_KEY_ID")
    key_secret = access_key_secret or os.environ.get("ALIBABA_ACCESS_KEY_SECRET")

    if not key_id or not key_secret:
        logger.error("Missing Alibaba Cloud credentials (--access-key-id and --access-key-secret or env vars)")
        return False

    # Validate month format
    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        logger.error(f"Invalid month format: {month}. Use YYYY-MM format (e.g., 2025-10)")
        return False

    # Set output file
    if not output_file:
        output_file = f"alibaba_billing_{month}.csv"

    logger.info(f"Exporting Alibaba Cloud billing data for {month} to {output_file}")

    try:
        client = AlibabaCloudClient(
            access_key_id=key_id,
            access_key_secret=key_secret,
            region_id=region_id,
        )

        # Fetch billing data
        logger.info(f"Fetching billing data for {month}...")
        bills = client.fetch_instance_bill_by_billing_cycle(billing_cycle=month)

        if not bills:
            logger.warning(f"No billing data found for {month}")
            return True

        # Convert to CSV
        logger.info(f"Writing {len(bills)} billing items to CSV...")
        _write_alibaba_csv(output_file, bills)

        logger.info(f"Successfully exported {len(bills)} billing items to {output_file}")
        return True

    except Exception as e:
        logger.error(f"Error exporting Alibaba Cloud billing data: {e}")
        return False


def _write_alibaba_csv(output_file: str, bills: list) -> None:
    """Write Alibaba Cloud billing data to CSV file."""
    if not bills:
        logger.warning("No billing items to write")
        return

    # Get field names from first item
    first_item = bills[0]
    if hasattr(first_item, "__dict__"):
        fieldnames = first_item.__dict__.keys()
    elif isinstance(first_item, dict):
        fieldnames = first_item.keys()
    else:
        logger.error(f"Unsupported billing item type: {type(first_item)}")
        return

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for item in bills:
            if hasattr(item, "__dict__"):
                row = item.__dict__
            elif isinstance(item, dict):
                row = item
            else:
                row = vars(item)

            writer.writerow(row)


def export_azure(
    month: str,
    tenant_id: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    billing_account_id: Optional[str] = None,
    output_file: Optional[str] = None,
) -> bool:
    """
    Export Azure billing data for specified month to CSV.

    Args:
        month: Billing month in format YYYY-MM (e.g., 2025-10)
        tenant_id: Azure Tenant ID (or read from AZURE_TENANT_ID env)
        client_id: Azure Client ID (or read from AZURE_CLIENT_ID env)
        client_secret: Azure Client Secret (or read from AZURE_CLIENT_SECRET env)
        billing_account_id: Azure Billing Account ID
        output_file: Output CSV file path (default: azure_billing_{month}.csv)

    Returns:
        bool: True if successful, False if error
    """
    try:
        from cloud_billing.azure_cloud import AzureCloudClient
    except ImportError as e:
        logger.error(f"Failed to import Azure client: {e}")
        logger.error("Make sure to install dependencies: pip install -r requirements.txt")
        return False

    # Get credentials from arguments or environment
    tenant = tenant_id or os.environ.get("AZURE_TENANT_ID")
    client = client_id or os.environ.get("AZURE_CLIENT_ID")
    secret = client_secret or os.environ.get("AZURE_CLIENT_SECRET")
    billing_account = billing_account_id

    if not tenant or not client or not secret:
        logger.error("Missing Azure credentials (--tenant-id, --client-id, --client-secret or env vars)")
        return False

    if not billing_account:
        logger.error("Missing --billing-account-id")
        return False

    # Validate month format
    try:
        month_date = datetime.strptime(month, "%Y-%m")
    except ValueError:
        logger.error(f"Invalid month format: {month}. Use YYYY-MM format (e.g., 2025-10)")
        return False

    # Set output file
    if not output_file:
        output_file = f"azure_billing_{month}.csv"

    logger.info(f"Exporting Azure billing data for {month} to {output_file}")

    try:
        azure_client = AzureCloudClient(tenant_id=tenant, client_id=client, client_secret=secret)

        # Get access token
        token, error = azure_client.get_access_token()
        if error:
            logger.error(f"Failed to get Azure access token: {error}")
            return False

        # Fetch billing location
        logger.info("Fetching Azure billing location...")
        location_url, error = azure_client.get_ri_location(
            billing_account_id=billing_account,
            metric="ActualCost",
            start_date=f"{month_date.year}-{month_date.month:02d}-01",
            end_date=f"{month_date.year}-{month_date.month:02d}-{_get_last_day_of_month(month_date)}",
            token=token,
        )

        if error:
            logger.error(f"Failed to get billing location: {error}")
            return False

        if not location_url:
            logger.warning(f"No billing location returned for {month}")
            return True

        # Get CSV URL
        logger.info("Fetching Azure CSV URL...")
        csv_url, error = azure_client.get_ri_csv_url(location_url=location_url, token=token)

        if error:
            logger.error(f"Failed to get CSV URL: {error}")
            return False

        if not csv_url:
            logger.warning(f"No CSV URL returned for {month}")
            return True

        # Download CSV
        logger.info("Downloading Azure billing data...")
        csv_data, error = azure_client.download_ri_csv(csv_url=csv_url, token=token)

        if error:
            logger.error(f"Failed to download CSV: {error}")
            return False

        if not csv_data:
            logger.warning(f"No CSV data returned for {month}")
            return True

        # Save to file
        with open(output_file, "wb") as f:
            f.write(csv_data)

        logger.info(f"Successfully exported Azure billing data to {output_file}")
        return True

    except Exception as e:
        logger.error(f"Error exporting Azure billing data: {e}")
        return False


def _get_last_day_of_month(date_obj: datetime) -> int:
    """Get the last day of the month for a given date."""
    if date_obj.month == 12:
        next_month = date_obj.replace(year=date_obj.year + 1, month=1, day=1)
    else:
        next_month = date_obj.replace(month=date_obj.month + 1, day=1)

    last_day = (next_month - __import__("datetime").timedelta(days=1)).day
    return last_day


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export cloud billing data to CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--provider",
        required=True,
        choices=["alibaba", "azure"],
        help="Cloud provider (alibaba or azure)",
    )

    parser.add_argument(
        "--month",
        required=True,
        help="Billing month in YYYY-MM format (e.g., 2025-10)",
    )

    parser.add_argument(
        "--output",
        help="Output CSV file path (default: {provider}_billing_{month}.csv)",
    )

    # Alibaba Cloud arguments
    alibaba_group = parser.add_argument_group("Alibaba Cloud Options")
    alibaba_group.add_argument(
        "--access-key-id",
        help="Alibaba Cloud Access Key ID (or set ALIBABA_ACCESS_KEY_ID env var)",
    )
    alibaba_group.add_argument(
        "--access-key-secret",
        help="Alibaba Cloud Access Key Secret (or set ALIBABA_ACCESS_KEY_SECRET env var)",
    )
    alibaba_group.add_argument(
        "--region-id",
        default="cn-hangzhou",
        help="Alibaba Cloud region ID (default: cn-hangzhou)",
    )

    # Azure arguments
    azure_group = parser.add_argument_group("Azure Options")
    azure_group.add_argument(
        "--tenant-id",
        help="Azure Tenant ID (or set AZURE_TENANT_ID env var)",
    )
    azure_group.add_argument(
        "--client-id",
        help="Azure Client ID (or set AZURE_CLIENT_ID env var)",
    )
    azure_group.add_argument(
        "--client-secret",
        help="Azure Client Secret (or set AZURE_CLIENT_SECRET env var)",
    )
    azure_group.add_argument(
        "--billing-account-id",
        help="Azure Billing Account ID",
    )

    args = parser.parse_args()

    # Route to appropriate provider
    if args.provider == "alibaba":
        success = export_alibaba_cloud(
            month=args.month,
            access_key_id=args.access_key_id,
            access_key_secret=args.access_key_secret,
            region_id=args.region_id,
            output_file=args.output,
        )
    else:  # azure
        success = export_azure(
            month=args.month,
            tenant_id=args.tenant_id,
            client_id=args.client_id,
            client_secret=args.client_secret,
            billing_account_id=args.billing_account_id,
            output_file=args.output,
        )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

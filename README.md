# Cloud Billing

![Python Version](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)
![Tests](https://github.com/Visionary-Future/cloud-billing/actions/workflows/pytest.yml/badge.svg)

A comprehensive Python package for fetching billing information from Alibaba Cloud, AWS, Azure, and Huawei Cloud.

## Supported Cloud Providers

- **Alibaba Cloud** - Complete billing data retrieval with Kubernetes billing support
- **AWS** - Cost and usage data from AWS Cost Explorer
- **Azure** - Billing information from Azure Cost Management
- **Huawei Cloud** - Monthly bill summary from Huawei BSS API

## Key Features

- 🌐 **Multi-cloud support** - Unified interface for multiple cloud providers
- 📊 **Comprehensive billing data** - Detailed cost and usage information
- 🔧 **Easy integration** - Simple Python API for all cloud providers
- 📝 **Type safety** - Full type hints with Pydantic models
- 🧪 **Well tested** - Comprehensive test suite

## Quick Start

Install the package:

```bash
pip install cloud-billing
```

Get billing data from Alibaba Cloud:

```python
from cloud_billing.alibaba_cloud import AlibabaCloudClient

client = AlibabaCloudClient(
    access_key_id="your_access_key",
    access_key_secret="your_secret_key",
    region_id="cn-hangzhou"
)

billing_data = client.fetch_instance_bill_by_billing_cycle(
    billing_cycle="2024-01"
)
```

Get cost data from AWS:

```python
from cloud_billing.aws_cloud import AWSCloudClient

client = AWSCloudClient(
    access_key_id="your_access_key",
    secret_access_key="your_secret_key",
)

cost_data = client.get_cost_and_usage(
    time_period={"Start": "2024-01-01", "End": "2024-02-01"},
    granularity="MONTHLY",
    group_by=[{"Type": "DIMENSION", "Key": "SERVICE"}],
)
```

Get monthly bill from Huawei Cloud:

```python
from cloud_billing.huawei_cloud import HuaweiCloudClient

client = HuaweiCloudClient(
    access_key="your_access_key",
    secret_key="your_secret_key",
    domain_id="your_domain_id",
)

bill_items, error = client.query_monthly_bill_summary(bill_cycle="2024-01")
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](https://github.com/visionary-future/cloud-billing/blob/main/LICENSE) file for details.

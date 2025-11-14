# Cloud Billing

![Python Version](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)
![Tests](https://github.com/Visionary-Future/cloud-billing/actions/workflows/pytest.yml/badge.svg)

A comprehensive Python package for fetching billing information from multiple cloud providers.

## Supported Cloud Providers

- **Alibaba Cloud** - Complete billing data retrieval with Kubernetes billing support
- **AWS** - Cost and usage data from AWS Cost Explorer
- **Azure** - Billing information from Azure Cost Management
- **Huawei Cloud** - Usage and billing data retrieval

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
    start_date="2024-01"
)
```

## Documentation Structure

- **[Getting Started](getting-started/installation.md)** - Installation and basic setup
- **[Cloud Providers](providers/alibaba-cloud.md)** - Provider-specific guides
- **[API Reference](api/alibaba-cloud.md)** - Detailed API documentation
- **[Examples](examples.md)** - Code examples and use cases
 - **[Examples](examples.md)** - Code examples and use cases
 - **[Kubecost Allocation Example](examples_kubecost.md)** - Quick script to fetch Kubecost allocation data

## License

This project is licensed under the GPL-3.0-or-later License - see the [LICENSE](https://github.com/visionary-future/cloud-billing/blob/main/LICENSE) file for details.

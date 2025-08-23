# Installation

## Requirements

- Python 3.10 or higher
- pip or poetry for package management

## Install from PyPI

```bash
pip install cloud-billing
```

## Install with Poetry

If you're using Poetry in your project:

```bash
poetry add cloud-billing
```

## Development Installation

For development or contributing to the project:

1. Clone the repository:
```bash
git clone https://github.com/visionary-future/cloud-billing.git
cd cloud-billing
```

2. Install with Poetry:
```bash
poetry install
```

3. Activate the virtual environment:
```bash
poetry shell
```

## Verify Installation

Test your installation by importing the package:

```python
import cloud_billing
print(cloud_billing.__version__)
```

## Dependencies

The package automatically installs the following dependencies:

- `aliyun-python-sdk-core` - For Alibaba Cloud API integration
- `pydantic` - For data validation and type safety
- `requests` - For HTTP requests
- `requests-toolbelt` - Additional utilities for requests
- `python-dateutil` - For date parsing and manipulation

## Next Steps

Once installed, proceed to the [Quick Start](quickstart.md) guide to begin using the package.

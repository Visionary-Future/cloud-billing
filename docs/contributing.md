# Contributing to Cloud Billing

We welcome contributions to the Cloud Billing project! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Poetry for dependency management
- Git

### Setting up the Development Environment

1. Fork the repository on GitHub
2. Clone your fork:
```bash
git clone https://github.com/your-username/cloud-billing.git
cd cloud-billing
```

3. Install dependencies with Poetry:
```bash
poetry install
```

4. Set up pre-commit hooks:
```bash
poetry run pre-commit install
```

### Running Tests

Run the test suite:
```bash
poetry run pytest
```

Run tests with coverage:
```bash
poetry run pytest --cov=cloud_billing
```

Run tests in parallel:
```bash
poetry run pytest -n auto
```

## Code Style and Quality

We use several tools to maintain code quality:

- **Black** - Code formatting
- **Pre-commit** - Git hooks for quality checks
- **Pytest** - Testing framework

### Formatting Code

Format your code with Black:
```bash
poetry run black cloud_billing/ tests/
```

### Running Pre-commit Checks

```bash
poetry run pre-commit run --all-files
```

## Adding a New Cloud Provider

To add support for a new cloud provider:

1. Create a new module under `cloud_billing/`:
```
cloud_billing/
├── new_provider/
│   ├── __init__.py
│   ├── client.py
│   ├── types.py
│   └── exceptions.py
```

2. Implement the required interfaces:
   - `client.py` - Main client class with billing methods
   - `types.py` - Pydantic models for data validation
   - `exceptions.py` - Provider-specific exceptions

3. Add tests in `tests/`:
```
tests/
├── test_new_provider.py
└── test_new_provider_utils.py
```

4. Update documentation:
   - Add provider guide in `docs/providers/`
   - Add API reference in `docs/api/`
   - Update navigation in `mkdocs.yml`

### Example Client Structure

```python
# cloud_billing/new_provider/client.py
from typing import List, Optional
from .types import BillingData, BillingItem
from .exceptions import NewProviderException

class NewProviderBillingClient:
    def __init__(self, api_key: str, region: str = "default"):
        self.api_key = api_key
        self.region = region

    def get_billing_data(
        self,
        start_date: str,
        end_date: str,
        granularity: str = "DAILY"
    ) -> BillingData:
        """Fetch billing data for the specified date range."""
        # Implementation here
        pass
```

## Testing Guidelines

### Unit Tests

- Write tests for all public methods
- Use meaningful test names that describe the scenario
- Mock external API calls
- Test both success and error cases

Example test:
```python
# tests/test_new_provider.py
import pytest
from cloud_billing.new_provider import NewProviderBillingClient
from cloud_billing.new_provider.exceptions import NewProviderException

def test_get_billing_data_success():
    client = NewProviderBillingClient("test-key")

    # Mock the API response
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {
            'total_cost': 100.0,
            'items': []
        }

        result = client.get_billing_data("2024-01-01", "2024-01-31")

        assert result.total_cost == 100.0
        assert len(result.billing_items) == 0

def test_get_billing_data_api_error():
    client = NewProviderBillingClient("invalid-key")

    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException("API Error")

        with pytest.raises(NewProviderException):
            client.get_billing_data("2024-01-01", "2024-01-31")
```

### Integration Tests

For integration tests that call real APIs:
- Use environment variables for credentials
- Skip tests if credentials are not available
- Use test accounts/sandbox environments when possible

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def get_billing_data(
    self,
    start_date: str,
    end_date: str,
    granularity: str = "DAILY"
) -> BillingData:
    """Fetch billing data for the specified date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        granularity: Data granularity (DAILY, MONTHLY)

    Returns:
        BillingData object containing cost and usage information

    Raises:
        NewProviderException: If the API request fails
        ValueError: If date format is invalid
    """
```

### Adding Documentation Pages

1. Create markdown files in the appropriate `docs/` subdirectory
2. Update the navigation in `mkdocs.yml`
3. Use code examples and clear explanations
4. Link between related pages

## Submitting Changes

### Pull Request Process

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit them:
```bash
git add .
git commit -m "Add support for New Provider"
```

3. Push to your fork:
```bash
git push origin feature/your-feature-name
```

4. Create a Pull Request on GitHub

### Pull Request Guidelines

- Provide a clear description of the changes
- Include tests for new functionality
- Update documentation as needed
- Ensure all CI checks pass
- Link to related issues if applicable

### Commit Message Format

Use clear, descriptive commit messages:
- `feat: add New Provider billing client`
- `fix: handle rate limiting in Alibaba Cloud client`
- `docs: update installation guide`
- `test: add integration tests for AWS client`

## Getting Help

- Open an issue for bug reports or feature requests
- Join discussions in existing issues
- Ask questions in pull request reviews

## Code of Conduct

Please be respectful and inclusive when contributing. We want this project to be welcoming to developers of all backgrounds and experience levels.

## Recognition

Contributors will be recognized in:
- The project's README
- Release notes
- Documentation acknowledgments

Thank you for contributing to Cloud Billing!

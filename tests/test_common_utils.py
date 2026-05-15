"""Unit tests for common utilities."""

from datetime import datetime

from cloud_billing.common.utils import get_billing_cycle


def test_get_billing_cycle_string():
    result = get_billing_cycle()
    assert isinstance(result, str)
    assert len(result) == 7  # YYYY-MM


def test_get_billing_cycle_datetime():
    result = get_billing_cycle(output="datetime")
    assert isinstance(result, datetime)

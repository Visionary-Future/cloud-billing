# Copyright 2025 Visionary Future
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

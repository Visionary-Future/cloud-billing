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

"""Pydantic models for Tencent Cloud Billing API responses."""

from typing import List, Optional

from pydantic import BaseModel


class TagItem(BaseModel):
    """Resource tag key-value pair."""

    TagKey: str
    TagValue: str


class BillDetailItem(BaseModel):
    """Individual bill detail record from DescribeBillDetail."""

    PayerAccountId: Optional[str] = None
    OwnerAccountId: Optional[str] = None
    OperatorAccountId: Optional[str] = None
    ProductName: Optional[str] = None
    SubProductName: Optional[str] = None
    BillingMode: Optional[str] = None
    ProjectName: Optional[str] = None
    Region: Optional[str] = None
    AvailabilityZone: Optional[str] = None
    InstanceId: Optional[str] = None
    InstanceName: Optional[str] = None
    TransactionType: Optional[str] = None
    TransactionId: Optional[str] = None
    TransactionTime: Optional[str] = None
    UsageStartTime: Optional[str] = None
    UsageEndTime: Optional[str] = None
    ComponentType: Optional[str] = None
    ComponentName: Optional[str] = None
    ComponentListPrice: Optional[str] = None
    ComponentPriceMeasurementUnit: Optional[str] = None
    ComponentUsage: Optional[str] = None
    ComponentUsageUnit: Optional[str] = None
    UsageDuration: Optional[str] = None
    DurationUnit: Optional[str] = None
    OriginalCost: Optional[str] = None
    TotalCost: Optional[str] = None
    Currency: Optional[str] = None
    Tags: Optional[List[TagItem]] = None


class DescribeBillDetailData(BaseModel):
    """Response data wrapper for DescribeBillDetail."""

    DetailSet: List[BillDetailItem] = []
    Total: Optional[int] = None
    Context: Optional[str] = None


class DescribeBillDetailResponse(BaseModel):
    """Top-level response for DescribeBillDetail."""

    DetailSet: List[BillDetailItem] = []
    Total: Optional[int] = None
    Context: Optional[str] = None
    RequestId: Optional[str] = None


class BillResourceSummaryItem(BaseModel):
    """Resource-level cost summary from DescribeBillResourceSummary."""

    PayerAccountId: Optional[str] = None
    OwnerAccountId: Optional[str] = None
    OperatorAccountId: Optional[str] = None
    ProductName: Optional[str] = None
    BillingMode: Optional[str] = None
    ProjectName: Optional[str] = None
    Region: Optional[str] = None
    AvailabilityZone: Optional[str] = None
    InstanceId: Optional[str] = None
    InstanceName: Optional[str] = None
    OriginalCost: Optional[str] = None
    TotalCost: Optional[str] = None
    Currency: Optional[str] = None
    Tags: Optional[List[TagItem]] = None


class DescribeBillResourceSummaryData(BaseModel):
    """Response data wrapper for DescribeBillResourceSummary."""

    ResourceSummarySet: List[BillResourceSummaryItem] = []
    Total: Optional[int] = None


class DescribeBillResourceSummaryResponse(BaseModel):
    """Top-level response for DescribeBillResourceSummary."""

    ResourceSummarySet: List[BillResourceSummaryItem] = []
    Total: Optional[int] = None
    RequestId: Optional[str] = None


class BillSummaryByProductItem(BaseModel):
    """Product-level cost summary."""

    ProductName: Optional[str] = None
    ProductCode: Optional[str] = None
    OriginalCost: Optional[str] = None
    TotalCost: Optional[str] = None
    RealTotalCost: Optional[str] = None
    CashPayAmount: Optional[str] = None
    IncentivePayAmount: Optional[str] = None
    VoucherPayAmount: Optional[str] = None
    TransferPayAmount: Optional[str] = None
    Currency: Optional[str] = None


class DescribeBillSummaryByProductResponse(BaseModel):
    """Top-level response for DescribeBillSummaryByProduct."""

    SummaryDetail: List[BillSummaryByProductItem] = []
    Total: Optional[int] = None
    RequestId: Optional[str] = None


class AccountBalanceItem(BaseModel):
    """Account balance information."""

    Balance: Optional[float] = None
    CashAccountBalance: Optional[float] = None
    CreditBalance: Optional[float] = None
    RealBalance: Optional[float] = None
    FrozenAmount: Optional[float] = None
    AvailableAmount: Optional[float] = None
    Currency: Optional[str] = None

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

from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


class SUBSCRIPTION_TYPE(Enum):
    SUBSCRIPTION = "Subscription"
    PAYASYOUGO = "PayAsYouGo"


class QueryInstanceBillItem(BaseModel):
    AfterDiscountAmount: Optional[float] = 0.0
    InstanceSpec: str
    ProductName: str
    InstanceID: str
    BillAccountID: str
    DeductedByCashCoupons: Optional[float] = 0.0
    BillingDate: Optional[str]
    ListPriceUnit: Optional[str]
    PaymentAmount: Optional[float] = 0.0
    ListPrice: Optional[str]
    DeductedByPrepaidCard: Optional[float] = 0.0
    InvoiceDiscount: float
    Item: str
    SubscriptionType: str
    PretaxGrossAmount: float
    InstanceConfig: str
    Currency: str
    CommodityCode: str
    ItemName: str
    CostUnit: str
    ResourceGroup: str
    AdjustAmount: Optional[float] = 0.0
    BillingType: str
    DeductedByCoupons: Optional[float] = 0.0
    Usage: Optional[str]
    ProductDetail: str
    ProductCode: str
    Zone: Optional[str]
    ProductType: str
    OutstandingAmount: Optional[float] = 0.0
    BizType: Optional[str]
    BillingItem: Optional[str]
    NickName: Optional[str]
    PipCode: str
    IntranetIP: Optional[str]
    ServicePeriodUnit: str
    ServicePeriod: str
    DeductedByResourcePackage: Optional[str]
    UsageUnit: Optional[str]
    InternetIP: Optional[str]
    PretaxAmount: float
    OwnerID: str
    BillAccountName: str
    Region: str
    Tag: Optional[str]
    CashAmount: Optional[float] = 0.0


class QueryInstanceBillData(BaseModel):
    BillingCycle: str
    TotalCount: int
    AccountID: str
    NextToken: Optional[str] = None
    MaxResults: int
    Items: List[QueryInstanceBillItem]
    AccountName: str


class QueryInstanceBillResponse(BaseModel):
    Message: str
    RequestId: str
    Data: QueryInstanceBillData
    Code: str
    Success: bool


class AmortizedItem(BaseModel):
    CurrentAmortizationPretaxAmount: float
    RemainingAmortizationDeductedByCoupons: float
    ProductName: str
    PreviouslyAmortizedExpenditureAmount: float
    InstanceID: str
    BillAccountID: str
    ProductDetailCode: str
    PreviouslyAmortizedRoundDownDiscount: float
    AmortizationStatus: str
    DeductedByPrepaidCard: float
    SplitItemName: str
    SubscriptionType: str
    CurrentAmortizationDeductedByCashCoupons: float
    CostUnitCode: str
    RemainingAmortizationDeductedByPrepaidCard: float
    CostUnit: str
    DeductedByCoupons: float
    ProductCode: str
    BillOwnerID: str
    BizType: str
    PreviouslyAmortizedPretaxAmount: float
    IntranetIP: str
    CurrentAmortizationPretaxGrossAmount: float
    InternetIP: str
    RemainingAmortizationExpenditureAmount: float
    Region: str
    RemainingAmortizationInvoiceDiscount: float
    PreviouslyAmortizedDeductedByCashCoupons: float
    CurrentAmortizationDeductedByCoupons: float
    CurrentAmortizationRoundDownDiscount: float
    CurrentAmortizationExpenditureAmount: float
    RemainingAmortizationRoundDownDiscount: float
    PreviouslyAmortizedInvoiceDiscount: float
    DeductedByCashCoupons: float
    PreviouslyAmortizedDeductedByCoupons: float
    RemainingAmortizationDeductedByCashCoupons: float
    InvoiceDiscount: float
    SplitProductDetail: str
    CurrentAmortizationDeductedByPrepaidCard: float
    AmortizationPeriod: str
    PretaxGrossAmount: float
    PreviouslyAmortizedPretaxGrossAmount: float
    ResourceGroup: str
    SplitAccountName: str
    RoundDownDiscount: float
    ProductDetail: str
    ConsumePeriod: str
    Zone: str
    BillOwnerName: str
    SplitItemID: str
    RemainingAmortizationPretaxGrossAmount: float
    PretaxAmount: float
    CurrentAmortizationInvoiceDiscount: float
    ExpenditureAmount: float
    RemainingAmortizationPretaxAmount: float
    BillAccountName: str
    Tag: str
    PreviouslyAmortizedDeductedByPrepaidCard: float

    @field_validator("BillAccountID", mode="before")
    def parse_int(cls, value):
        return str(value)

    @field_validator("BillOwnerID", mode="before")
    def parse_bill_owner_id(cls, value):
        return str(value)


class AmortizedDealedResponse(BaseModel):
    Items: List[AmortizedItem]
    AccountName: str
    AccountID: str


class AmortizedData(BaseModel):
    TotalCount: int
    AccountID: str
    NextToken: Optional[str] = None
    MaxResults: int
    Items: List[AmortizedItem]
    AccountName: str


class AmortizedResponse(BaseModel):
    RequestId: str
    Message: str
    Data: AmortizedData
    Code: str
    Success: bool


class QueryAccountBillItem(BaseModel):
    """Account bill item aggregated by product (QueryAccountBill)."""

    PipCode: Optional[str] = None
    PretaxAmount: float = 0.0
    BillingDate: Optional[str] = None
    ProductName: Optional[str] = None
    AdjustAmount: float = 0.0
    OwnerName: Optional[str] = None
    Currency: Optional[str] = None
    BillAccountName: Optional[str] = None
    SubscriptionType: Optional[str] = None
    DeductedByCashCoupons: float = 0.0
    BizType: Optional[str] = None
    OwnerID: Optional[str] = None
    DeductedByPrepaidCard: float = 0.0
    DeductedByCoupons: float = 0.0
    BillAccountID: Optional[str] = None
    PaymentAmount: float = 0.0
    InvoiceDiscount: float = 0.0
    OutstandingAmount: float = 0.0
    CostUnit: Optional[str] = None
    PretaxGrossAmount: float = 0.0
    CashAmount: float = 0.0
    ProductCode: Optional[str] = None

    @field_validator("OwnerID", "BillAccountID", mode="before")
    @classmethod
    def parse_id_as_str(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)


class QueryAccountBillData(BaseModel):
    PageNum: int = 1
    BillingCycle: str
    AccountID: str
    PageSize: int = 20
    TotalCount: int = 0
    AccountName: str
    Items: List[QueryAccountBillItem] = Field(default_factory=list)

    @field_validator("Items", mode="before")
    @classmethod
    def unwrap_items(cls, value: Any) -> List[Any]:
        """Alibaba returns Items as {"Item": [...]} for QueryAccountBill."""
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            item = value.get("Item", [])
            if item is None:
                return []
            if isinstance(item, list):
                return item
            return [item]
        return []


class QueryAccountBillResponse(BaseModel):
    Code: str
    Message: str
    RequestId: str
    Success: bool
    Data: QueryAccountBillData

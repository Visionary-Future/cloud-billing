from typing import List, Optional

from pydantic import BaseModel


class QueryInstanceBillItem(BaseModel):
    AfterDiscountAmount: float
    InstanceSpec: str
    ProductName: str
    InstanceID: str
    BillAccountID: str
    DeductedByCashCoupons: float
    BillingDate: Optional[str]
    ListPriceUnit: Optional[str]
    PaymentAmount: float
    ListPrice: Optional[str]
    DeductedByPrepaidCard: float
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
    AdjustAmount: float
    BillingType: str
    DeductedByCoupons: float
    Usage: Optional[str]
    ProductDetail: str
    ProductCode: str
    Zone: Optional[str]
    ProductType: str
    OutstandingAmount: float
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
    CashAmount: float


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

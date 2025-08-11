from typing import List, Optional

from pydantic import BaseModel, field_validator


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

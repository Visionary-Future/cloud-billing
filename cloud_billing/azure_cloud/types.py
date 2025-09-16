from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ChargeType(str, Enum):
    ROUNDING_ADJUSTMENT = "RoundingAdjustment"
    PURCHASE = "Purchase"
    USAGE = "Usage"
    REFUND = "Refund"
    OTHER = "Other"
    UNUSED_RESERVATION = "UnusedReservation"


class BillingRecord(BaseModel):
    invoiceId: str = Field(..., alias="invoiceId")
    previousInvoiceId: str
    billingAccountId: str
    billingAccountName: str
    billingProfileId: str
    billingProfileName: str
    invoiceSectionId: str
    invoiceSectionName: str
    resellerName: Optional[str] = None
    resellerMpnId: str
    costCenter: str
    billingPeriodEndDate: str
    billingPeriodStartDate: str
    servicePeriodStartDate: Optional[date] = None
    servicePeriodEndDate: Optional[date] = None
    billing_date: Optional[date] = Field(..., alias="date")
    serviceFamily: str
    productOrderId: str
    productOrderName: str
    consumedService: str
    meterId: str
    meterName: str
    meterCategory: str
    meterSubCategory: str
    meterRegion: str
    ProductId: str
    ProductName: str
    SubscriptionId: str
    subscriptionName: Optional[str] = None
    publisherType: str
    publisherId: str
    publisherName: str
    resourceGroupName: str
    ResourceId: str
    resourceLocation: str
    location: str
    effectivePrice: str
    quantity: str
    unitOfMeasure: str
    chargeType: ChargeType
    billingCurrency: str
    pricingCurrency: str
    costInBillingCurrency: float
    costInPricingCurrency: str
    costInUsd: float
    paygCostInBillingCurrency: float
    paygCostInUsd: float
    exchangeRatePricingToBilling: str
    exchangeRateDate: str
    isAzureCreditEligible: str
    serviceInfo1: str
    serviceInfo2: str
    additionalInfo: str
    tags: Optional[str] = None
    PayGPrice: str
    frequency: str
    term: str
    reservationId: str
    reservationName: str
    pricingModel: str
    unitPrice: str
    costAllocationRuleName: str
    benefitId: str
    benefitName: str
    provider: str

    @field_validator("servicePeriodStartDate", "servicePeriodEndDate", "billing_date", mode="before")
    def parse_date(cls, v):
        if not v or v == "":
            return None
        try:
            return datetime.strptime(v, "%m/%d/%Y").date()
        except ValueError:
            return None

    @field_validator("costInBillingCurrency", "costInUsd", mode="before")
    def parse_float(cls, v):
        return float(v) if v else 0.0

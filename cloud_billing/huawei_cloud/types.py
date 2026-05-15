"""Pydantic models for Huawei Cloud BSS API responses."""

from typing import List, Optional

from pydantic import BaseModel, field_validator


class MonthlyBillItem(BaseModel):
    """A single bill line item from the monthly bill summary (BillSumRecordInfoV2)."""

    bill_cycle: str
    consume_amount: float = 0.0
    cash_amount: Optional[float] = 0.0
    credit_amount: Optional[float] = 0.0
    coupon_amount: Optional[float] = 0.0
    debt_amount: Optional[float] = 0.0
    flexipurchase_coupon_amount: Optional[float] = 0.0
    stored_value_card_amount: Optional[float] = 0.0
    writeoff_amount: Optional[float] = 0.0
    service_type_code: Optional[str] = None
    service_type_name: Optional[str] = None
    resource_type_code: Optional[str] = None
    resource_type_name: Optional[str] = None
    customer_id: Optional[str] = None
    account_name: Optional[str] = None
    bill_type: Optional[int] = None
    charging_mode: Optional[int] = None
    measure_id: Optional[int] = None
    official_amount: Optional[float] = 0.0
    official_discount_amount: Optional[float] = 0.0
    truncated_amount: Optional[float] = 0.0

    @field_validator(
        "consume_amount",
        "cash_amount",
        "credit_amount",
        "coupon_amount",
        "debt_amount",
        "flexipurchase_coupon_amount",
        "stored_value_card_amount",
        "writeoff_amount",
        "official_amount",
        "official_discount_amount",
        "truncated_amount",
        mode="before",
    )
    @classmethod
    def parse_float(cls, v):
        if v is None or v == "":
            return 0.0
        return float(v)


class MonthlyBillResponse(BaseModel):
    """Wrapper for the ShowCustomerMonthlySum API response."""

    bill_sums: List[MonthlyBillItem] = []
    total_count: int = 0
    currency: str = "CNY"

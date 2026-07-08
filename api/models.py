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

"""Pydantic request/response models for the Cloud Billing SaaS API."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Alibaba Cloud
# ---------------------------------------------------------------------------


class AlibabaCredentials(BaseModel):
    access_key_id: str = Field(..., description="Alibaba Cloud Access Key ID")
    access_key_secret: str = Field(..., description="Alibaba Cloud Access Key Secret")
    region_id: str = Field(default="cn-hangzhou", description="Region ID")


class AlibabaFetchRequest(AlibabaCredentials):
    billing_cycle: str = Field(
        ..., pattern=r"^\d{4}-\d{2}$", description="Billing cycle in YYYY-MM format", examples=["2025-12"]
    )
    billing_date: Optional[str] = Field(
        default=None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Specific date YYYY-MM-DD (daily granularity)"
    )


class AlibabaAmortizedRequest(AlibabaCredentials):
    billing_cycle: str = Field(
        ..., pattern=r"^\d{4}-\d{2}$", description="Billing cycle in YYYY-MM format", examples=["2025-12"]
    )


# ---------------------------------------------------------------------------
# Azure Cloud
# ---------------------------------------------------------------------------


class AzureCredentials(BaseModel):
    tenant_id: str = Field(..., description="Azure tenant ID")
    client_id: str = Field(..., description="Azure application (client) ID")
    client_secret: str = Field(..., description="Azure client secret")


class AzureStartRequest(AzureCredentials):
    billing_account_id: str = Field(..., description="Azure billing account ID")
    start_date: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Report start date YYYY-MM-DD", examples=["2025-12-01"]
    )
    end_date: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Report end date YYYY-MM-DD", examples=["2025-12-31"]
    )
    metric: str = Field(default="ActualCost", description="Cost metric")


class AzurePollRequest(AzureCredentials):
    location_url: str = Field(..., description="Polling URL returned by /azure/billing/start")


class AzureStartResponse(BaseModel):
    location_url: str
    message: str = "Report generation started. Poll /api/azure/billing/poll for status."


class AzurePollResponse(BaseModel):
    status: str  # "pending" | "completed" | "error"
    csv_url: Optional[str] = None
    message: Optional[str] = None
    records: Optional[List[Dict[str, Any]]] = None


# ---------------------------------------------------------------------------
# AWS Cloud
# ---------------------------------------------------------------------------


class AWSCredentials(BaseModel):
    access_key_id: str = Field(..., description="AWS Access Key ID")
    secret_access_key: str = Field(..., description="AWS Secret Access Key")
    region_name: str = Field(default="us-east-1", description="AWS region for Cost Explorer")


class AWSCostRequest(AWSCredentials):
    start_date: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date YYYY-MM-DD", examples=["2025-12-01"]
    )
    end_date: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date YYYY-MM-DD", examples=["2025-12-31"]
    )
    granularity: Literal["MONTHLY", "DAILY"] = Field(default="MONTHLY", description="MONTHLY or DAILY")
    metrics: Optional[List[str]] = Field(default=None, description="Cost metrics, e.g. ['UnblendedCost']")
    group_by_dimension: Optional[str] = Field(default=None, description="Group by dimension, e.g. SERVICE, REGION")
    group_by_tag: Optional[str] = Field(default=None, description="Group by tag key")


# ---------------------------------------------------------------------------
# Huawei Cloud
# ---------------------------------------------------------------------------


class HuaweiCredentials(BaseModel):
    access_key: str = Field(..., description="Huawei Cloud Access Key")
    secret_key: str = Field(..., description="Huawei Cloud Secret Key")
    domain_id: str = Field(..., description="Huawei Cloud Domain ID")
    region_id: str = Field(default="cn-east-3", description="Region ID")


class HuaweiMonthlyBillRequest(HuaweiCredentials):
    bill_cycle: str = Field(
        ..., pattern=r"^\d{4}-\d{2}$", description="Billing cycle YYYY-MM", examples=["2025-12"]
    )


# ---------------------------------------------------------------------------
# Kubecost
# ---------------------------------------------------------------------------


class KubecostRequest(BaseModel):
    base_url: str = Field(..., description="Kubecost service base URL", examples=["http://kubecost.example.com:9090"])
    start_date: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date YYYY-MM-DD", examples=["2025-12-01"]
    )
    end_date: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date YYYY-MM-DD", examples=["2025-12-31"]
    )
    window: str = Field(default="1d", description="Time window, e.g. 1d, 1h")
    aggregate_by: Optional[List[str]] = Field(
        default=None, description="Aggregation dimensions, e.g. ['cluster', 'namespace']"
    )


class KubecostTestConnectionRequest(BaseModel):
    base_url: str = Field(..., description="Kubecost service base URL")


# ---------------------------------------------------------------------------
# Tencent Cloud
# ---------------------------------------------------------------------------


class TencentCredentials(BaseModel):
    secret_id: str = Field(..., description="Tencent Cloud Secret ID")
    secret_key: str = Field(..., description="Tencent Cloud Secret Key")
    region: str = Field(default="ap-guangzhou", description="Region")


class TencentBillDetailRequest(TencentCredentials):
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="Billing month YYYY-MM", examples=["2025-12"])
    pay_mode: Optional[Literal["prePay", "postPay"]] = Field(
        default=None, description="Payment mode: prePay or postPay"
    )
    resource_id: Optional[str] = Field(default=None, description="Filter by resource ID, e.g. ins-xxx")
    business_code: Optional[str] = Field(default=None, description="Filter by product code, e.g. p_cvm")


class TencentResourceSummaryRequest(TencentCredentials):
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="Billing month YYYY-MM", examples=["2025-12"])
    pay_mode: Optional[Literal["prePay", "postPay"]] = Field(
        default=None, description="Payment mode: prePay or postPay"
    )


class TencentProductSummaryRequest(TencentCredentials):
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="Billing month YYYY-MM", examples=["2025-12"])

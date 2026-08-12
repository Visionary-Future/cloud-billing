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

"""
Cloud Billing SaaS — FastAPI entry point for Vercel.

Design principles:
- Stateless: credentials are passed in each request body and never persisted server-side.
- Non-blocking: Azure long-poll is split into start + poll so the browser drives polling.
- Multi-cloud: exposes billing endpoints for Alibaba, AWS, Azure, Huawei, Kubecost, and Tencent Cloud.
"""

import csv
import io
import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from api.models import (
    AlibabaAmortizedRequest,
    AlibabaDailyProductBillRequest,
    AlibabaFetchRequest,
    AWSCostRequest,
    AzurePollRequest,
    AzurePollResponse,
    AzureStartRequest,
    AzureStartResponse,
    HuaweiMonthlyBillRequest,
    KubecostRequest,
    KubecostTestConnectionRequest,
    TencentBillDetailRequest,
    TencentCredentials,
    TencentProductSummaryRequest,
    TencentResourceSummaryRequest,
)
from cloud_billing.alibaba_cloud.client import AlibabaCloudClient
from cloud_billing.aws_cloud.client import AWSCloudClient
from cloud_billing.azure_cloud.client import AzureCloudClient
from cloud_billing.huawei_cloud.client import HuaweiCloudClient
from cloud_billing.kubecost.client import KubecostClient
from cloud_billing.tencent_cloud.client import TencentCloudClient

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cloud Billing API",
    description="Multi-cloud billing data service. Credentials are passed per-request and never stored.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _csv_response(
    items: list, filename: str, fieldnames: list[str] | None = None
) -> StreamingResponse:
    """Stream items as a CSV file download.

    Items can be Pydantic model instances (auto-detect fieldnames) or plain dicts
    (fieldnames must be provided).
    """
    if not items:
        raise HTTPException(status_code=404, detail="No billing data found.")
    output = io.StringIO()
    if fieldnames is None:
        fieldnames = list(items[0].model_fields.keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for item in items:
        row = item if isinstance(item, dict) else item.model_dump()
        writer.writerow(row)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _log_and_raise(status_code: int, provider: str, error: str | None, exc: Exception | None = None) -> HTTPException:
    """Log the full error server-side and raise a generic HTTPException.

    Args:
        status_code: HTTP status code to return.
        provider: Provider name for log context.
        error: Additional error string for logging (never exposed to client).
        exc: Original exception for traceback logging.
    """
    ref = uuid4().hex[:8]
    logger.error("[%s] %s error: %s", ref, provider, error or str(exc), exc_info=bool(exc))
    detail = f"{provider} API error — reference: {ref}"
    return HTTPException(status_code=status_code, detail=detail)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
def index():
    """Serve the frontend SPA. Works on both Vercel and local dev."""
    html_path = Path(__file__).parent / "templates" / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return {"message": "Cloud Billing API — visit /docs for API documentation"}


@app.get("/api/health", tags=["meta"])
def health():
    """Liveness probe."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Alibaba Cloud
# ---------------------------------------------------------------------------


@app.post("/api/alibaba/billing", tags=["alibaba"], summary="Fetch instance bill")
def alibaba_billing(req: AlibabaFetchRequest):
    """
    Fetch Alibaba Cloud instance-level bill for the given billing cycle.
    All pages are fetched automatically. Returns a list of bill items as JSON.
    Credentials are used only within this request and are never stored.
    """
    client = AlibabaCloudClient(
        access_key_id=req.access_key_id,
        access_key_secret=req.access_key_secret,
        region_id=req.region_id,
    )
    try:
        items = client.fetch_instance_bill_by_billing_cycle(
            billing_cycle=req.billing_cycle,
            billing_date=req.billing_date,
        )
        return {"billing_cycle": req.billing_cycle, "total": len(items), "items": [i.model_dump() for i in items]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _log_and_raise(502, "Alibaba", str(e), e)


@app.post("/api/alibaba/billing/csv", tags=["alibaba"], summary="Download instance bill as CSV")
def alibaba_billing_csv(req: AlibabaFetchRequest):
    """
    Fetch Alibaba Cloud instance-level bill and stream back as a CSV file download.
    """
    client = AlibabaCloudClient(
        access_key_id=req.access_key_id,
        access_key_secret=req.access_key_secret,
        region_id=req.region_id,
    )
    try:
        items = client.fetch_instance_bill_by_billing_cycle(
            billing_cycle=req.billing_cycle,
            billing_date=req.billing_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _log_and_raise(502, "Alibaba", str(e), e)

    return _csv_response(items, f"alibaba_billing_{req.billing_cycle}.csv")


@app.post("/api/alibaba/amortized", tags=["alibaba"], summary="Fetch amortized cost")
def alibaba_amortized(req: AlibabaAmortizedRequest):
    """
    Fetch Alibaba Cloud amortized cost by amortization period.
    """
    client = AlibabaCloudClient(
        access_key_id=req.access_key_id,
        access_key_secret=req.access_key_secret,
        region_id=req.region_id,
    )
    try:
        items = client.fetch_instance_amortized_cost_by_amortization_period(billing_cycle=req.billing_cycle)
        return {"billing_cycle": req.billing_cycle, "total": len(items), "items": [i.model_dump() for i in items]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _log_and_raise(502, "Alibaba", str(e), e)


@app.post(
    "/api/alibaba/billing/daily-by-product",
    tags=["alibaba"],
    summary="Fetch daily account bill by product",
)
def alibaba_daily_bill_by_product(req: AlibabaDailyProductBillRequest):
    """
    Fetch Alibaba Cloud account bill aggregated by product.

    Uses QueryAccountBill with IsGroupByProduct=true.
    When billing_date is provided, queries DAILY for that day; otherwise MONTHLY for the cycle.
    Credentials are used only within this request and are never stored.
    """
    client = AlibabaCloudClient(
        access_key_id=req.access_key_id,
        access_key_secret=req.access_key_secret,
        region_id=req.region_id,
    )
    try:
        items = client.fetch_daily_account_bill_by_product(
            billing_cycle=req.billing_cycle,
            billing_date=req.billing_date,
            product_code=req.product_code,
        )
        return {
            "billing_cycle": req.billing_cycle,
            "billing_date": req.billing_date,
            "total": len(items),
            "items": [i.model_dump() for i in items],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _log_and_raise(502, "Alibaba", str(e), e)


@app.post(
    "/api/alibaba/billing/daily-by-product/csv",
    tags=["alibaba"],
    summary="Download daily account bill by product as CSV",
)
def alibaba_daily_bill_by_product_csv(req: AlibabaDailyProductBillRequest):
    """
    Fetch Alibaba Cloud daily account bill aggregated by product and stream back as CSV.
    """
    client = AlibabaCloudClient(
        access_key_id=req.access_key_id,
        access_key_secret=req.access_key_secret,
        region_id=req.region_id,
    )
    try:
        items = client.fetch_daily_account_bill_by_product(
            billing_cycle=req.billing_cycle,
            billing_date=req.billing_date,
            product_code=req.product_code,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _log_and_raise(502, "Alibaba", str(e), e)

    return _csv_response(
        items,
        f"alibaba_daily_by_product_{req.billing_date or req.billing_cycle}.csv",
    )


# ---------------------------------------------------------------------------
# Azure Cloud — two-step async pattern
# ---------------------------------------------------------------------------


@app.post("/api/azure/billing/start", response_model=AzureStartResponse, tags=["azure"])
def azure_billing_start(req: AzureStartRequest):
    """
    Step 1: trigger Azure cost report generation.

    Azure's report generation is asynchronous (typically takes 1–5 minutes).
    This endpoint submits the request and returns a location_url.
    The client should poll /api/azure/billing/poll until status == "completed".
    Credentials are NOT stored; pass them again in each poll request.
    """
    client = AzureCloudClient(
        tenant_id=req.tenant_id,
        client_id=req.client_id,
        client_secret=req.client_secret,
    )

    token, err = client.get_access_token()
    if err:
        raise _log_and_raise(401, "Azure", err)

    location_url, err = client.get_ri_location(
        billing_account_id=req.billing_account_id,
        start_date=req.start_date,
        end_date=req.end_date,
        metric=req.metric,
        token=token,
    )
    if err:
        raise _log_and_raise(502, "Azure", err)

    return AzureStartResponse(location_url=location_url)


@app.post("/api/azure/billing/poll", response_model=AzurePollResponse, tags=["azure"])
def azure_billing_poll(req: AzurePollRequest):
    """
    Step 2: poll Azure report status (single non-blocking check).

    Returns status "pending" while the report is still generating,
    or status "completed" with a direct csv_url when ready.
    The client downloads the CSV directly from Azure Blob Storage.
    """
    client = AzureCloudClient(
        tenant_id=req.tenant_id,
        client_id=req.client_id,
        client_secret=req.client_secret,
    )

    token, err = client.get_access_token()
    if err:
        raise _log_and_raise(401, "Azure", err)

    status, csv_url, err = client.check_ri_report_once(location_url=req.location_url, token=token)

    if status == "error":
        raise HTTPException(status_code=502, detail=err or "Unknown Azure polling error")

    if status == "pending":
        return AzurePollResponse(status="pending", message="Report is still being generated, please retry.")

    # status == "completed"
    if not csv_url:
        raise HTTPException(status_code=502, detail="Report completed but no CSV URL returned.")

    return AzurePollResponse(status="completed", csv_url=csv_url)


# ---------------------------------------------------------------------------
# AWS Cloud
# ---------------------------------------------------------------------------


@app.post("/api/aws/cost-and-usage", tags=["aws"], summary="Fetch AWS cost and usage")
def aws_cost_and_usage(req: AWSCostRequest):
    """
    Fetch AWS cost and usage data from Cost Explorer.
    Supports grouping by dimension (SERVICE, REGION) or by tag.
    """
    client = AWSCloudClient(
        access_key_id=req.access_key_id,
        secret_access_key=req.secret_access_key,
        region_name=req.region_name,
    )

    time_period = {"Start": req.start_date, "End": req.end_date}
    group_by = None
    if req.group_by_dimension:
        group_by = [{"Type": "DIMENSION", "Key": req.group_by_dimension}]
    elif req.group_by_tag:
        group_by = [{"Type": "TAG", "Key": req.group_by_tag}]

    try:
        results = client.get_cost_and_usage(
            time_period=time_period,
            granularity=req.granularity,
            metrics=req.metrics,
            group_by=group_by,
        )
        return {
            "time_period": time_period,
            "granularity": req.granularity,
            "total_results": len(results),
            "results": [r.model_dump() for r in results],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _log_and_raise(502, "AWS", str(e), e)


@app.post("/api/aws/cost-and-usage/csv", tags=["aws"], summary="Download AWS cost data as CSV")
def aws_cost_and_usage_csv(req: AWSCostRequest):
    """Fetch AWS cost and usage data and stream back as CSV."""
    client = AWSCloudClient(
        access_key_id=req.access_key_id,
        secret_access_key=req.secret_access_key,
        region_name=req.region_name,
    )

    time_period = {"Start": req.start_date, "End": req.end_date}
    try:
        results = client.get_cost_and_usage(
            time_period=time_period,
            granularity=req.granularity,
            metrics=req.metrics,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _log_and_raise(502, "AWS", str(e), e)

    rows = []
    for r in results:
        start = r.TimePeriod.get("Start", "")
        end = r.TimePeriod.get("End", "")
        for metric_name, metric_value in (r.Total or {}).items():
            rows.append(
                {
                    "Start": start,
                    "End": end,
                    "Estimated": r.Estimated,
                    "Metric": metric_name,
                    "Amount": metric_value.Amount,
                    "Unit": metric_value.Unit,
                }
            )

    filename = f"aws_cost_{req.start_date}_{req.end_date}.csv"
    return _csv_response(rows, filename, fieldnames=["Start", "End", "Estimated", "Metric", "Amount", "Unit"])


# ---------------------------------------------------------------------------
# Huawei Cloud
# ---------------------------------------------------------------------------


@app.post("/api/huawei/monthly-bill", tags=["huawei"], summary="Fetch Huawei monthly bill summary")
def huawei_monthly_bill(req: HuaweiMonthlyBillRequest):
    """Fetch Huawei Cloud monthly bill summary for the given billing cycle."""
    client = HuaweiCloudClient(
        access_key=req.access_key,
        secret_key=req.secret_key,
        domain_id=req.domain_id,
        region_id=req.region_id,
    )

    items, error = client.query_monthly_bill_summary(bill_cycle=req.bill_cycle)
    if error:
        raise _log_and_raise(502, "Huawei", error)

    return {
        "bill_cycle": req.bill_cycle,
        "total": len(items) if items else 0,
        "items": [i.model_dump() for i in items] if items else [],
    }


@app.post("/api/huawei/monthly-bill/csv", tags=["huawei"], summary="Download Huawei monthly bill as CSV")
def huawei_monthly_bill_csv(req: HuaweiMonthlyBillRequest):
    """Fetch Huawei Cloud monthly bill summary and stream back as CSV."""
    client = HuaweiCloudClient(
        access_key=req.access_key,
        secret_key=req.secret_key,
        domain_id=req.domain_id,
        region_id=req.region_id,
    )

    items, error = client.query_monthly_bill_summary(bill_cycle=req.bill_cycle)
    if error:
        raise _log_and_raise(502, "Huawei", error)

    return _csv_response(items, f"huawei_bill_{req.bill_cycle}.csv")


# ---------------------------------------------------------------------------
# Kubecost
# ---------------------------------------------------------------------------


@app.post("/api/kubecost/allocation", tags=["kubecost"], summary="Fetch Kubecost allocation data")
def kubecost_allocation(req: KubecostRequest):
    """
    Fetch Kubernetes cost allocation data from Kubecost.
    Returns a stream of JSON records.
    """
    start_date = datetime.strptime(req.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(req.end_date, "%Y-%m-%d")

    client = KubecostClient(base_url=req.base_url)

    results = []
    errors = []
    for item, error in client.get_allocation_data(
        start_date=start_date,
        end_date=end_date,
        window=req.window,
        aggregate_by=req.aggregate_by,
    ):
        if error:
            errors.append(error)
        elif item:
            results.append(item.model_dump())

    return {
        "base_url": req.base_url,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "total": len(results),
        "errors": errors,
        "items": results,
    }


@app.post("/api/kubecost/test-connection", tags=["kubecost"], summary="Test Kubecost connection")
def kubecost_test_connection(req: KubecostTestConnectionRequest):
    """Test connectivity to a Kubecost instance."""
    client = KubecostClient(base_url=req.base_url)

    is_connected, error = client.test_connection()
    if is_connected:
        return {"base_url": req.base_url, "connected": True}

    logger.warning("Kubecost connection test failed: %s", error)
    return {"base_url": req.base_url, "connected": False, "error": "Connection test failed — check server logs for details."}


# ---------------------------------------------------------------------------
# Tencent Cloud
# ---------------------------------------------------------------------------


@app.post("/api/tencent/bill-detail", tags=["tencent"], summary="Fetch Tencent bill detail")
def tencent_bill_detail(req: TencentBillDetailRequest):
    """Fetch Tencent Cloud instance-level bill detail for the given month."""
    client = TencentCloudClient(
        secret_id=req.secret_id,
        secret_key=req.secret_key,
        region=req.region,
    )
    try:
        items = client.describe_bill_detail(
            month=req.month,
            pay_mode=req.pay_mode,
            resource_id=req.resource_id,
            business_code=req.business_code,
        )
        return {"month": req.month, "total": len(items), "items": [i.model_dump() for i in items]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _log_and_raise(502, "Tencent", str(e), e)


@app.post("/api/tencent/bill-detail/csv", tags=["tencent"], summary="Download Tencent bill detail as CSV")
def tencent_bill_detail_csv(req: TencentBillDetailRequest):
    """Fetch Tencent Cloud bill detail and stream back as CSV."""
    client = TencentCloudClient(
        secret_id=req.secret_id,
        secret_key=req.secret_key,
        region=req.region,
    )
    try:
        items = client.describe_bill_detail(
            month=req.month,
            pay_mode=req.pay_mode,
            resource_id=req.resource_id,
            business_code=req.business_code,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _log_and_raise(502, "Tencent", str(e), e)

    return _csv_response(items, f"tencent_bill_{req.month}.csv")


@app.post("/api/tencent/resource-summary", tags=["tencent"], summary="Fetch Tencent resource cost summary")
def tencent_resource_summary(req: TencentResourceSummaryRequest):
    """Fetch Tencent Cloud resource-level cost summary for the given month."""
    client = TencentCloudClient(
        secret_id=req.secret_id,
        secret_key=req.secret_key,
        region=req.region,
    )
    try:
        items = client.describe_bill_resource_summary(month=req.month, pay_mode=req.pay_mode)
        return {"month": req.month, "total": len(items), "items": [i.model_dump() for i in items]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _log_and_raise(502, "Tencent", str(e), e)


@app.post("/api/tencent/product-summary", tags=["tencent"], summary="Fetch Tencent product cost summary")
def tencent_product_summary(req: TencentProductSummaryRequest):
    """Fetch Tencent Cloud product-level cost summary for the given month."""
    client = TencentCloudClient(
        secret_id=req.secret_id,
        secret_key=req.secret_key,
        region=req.region,
    )
    try:
        items = client.describe_bill_summary_by_product(month=req.month)
        return {"month": req.month, "total": len(items), "items": [i.model_dump() for i in items]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _log_and_raise(502, "Tencent", str(e), e)


@app.post("/api/tencent/account-balance", tags=["tencent"], summary="Fetch Tencent account balance")
def tencent_account_balance(req: TencentCredentials):
    """Fetch Tencent Cloud account balance."""
    client = TencentCloudClient(
        secret_id=req.secret_id,
        secret_key=req.secret_key,
        region=req.region,
    )
    try:
        balance = client.describe_account_balance()
        return balance.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _log_and_raise(502, "Tencent", str(e), e)


# ---------------------------------------------------------------------------
# Static frontend — mounted LAST so all /api/* routes take priority.
# On Vercel, public/ is served by the CDN and this code path is never hit.
# Locally this gives a single-port (8000) dev experience with no CORS config.
# ---------------------------------------------------------------------------
_PUBLIC_DIR = Path(__file__).parent / "templates"
if _PUBLIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=_PUBLIC_DIR, html=True), name="static")

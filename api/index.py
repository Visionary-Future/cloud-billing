"""
Cloud Billing SaaS — FastAPI entry point for Vercel.

Design principles:
- Stateless: credentials are passed in each request body and never persisted server-side.
- Non-blocking: Azure long-poll is split into start + poll so the browser drives polling.
- Minimal: only exposes endpoints for fully-implemented providers (Alibaba + Azure).
"""

import csv
import io
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from cloud_billing.alibaba_cloud.client import AlibabaCloudClient
from cloud_billing.azure_cloud.client import AzureCloudClient

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
# Request / Response models
# ---------------------------------------------------------------------------


class AlibabaCredentials(BaseModel):
    access_key_id: str = Field(..., description="Alibaba Cloud Access Key ID")
    access_key_secret: str = Field(..., description="Alibaba Cloud Access Key Secret")
    region_id: str = Field(default="cn-hangzhou", description="Region ID")


class AlibabaFetchRequest(AlibabaCredentials):
    billing_cycle: str = Field(..., description="Billing cycle in YYYY-MM format", examples=["2025-12"])
    billing_date: Optional[str] = Field(default=None, description="Specific date YYYY-MM-DD (daily granularity)")


class AlibabaAmortizedRequest(AlibabaCredentials):
    billing_cycle: str = Field(..., description="Billing cycle in YYYY-MM format", examples=["2025-12"])


class AzureCredentials(BaseModel):
    tenant_id: str = Field(..., description="Azure tenant ID")
    client_id: str = Field(..., description="Azure application (client) ID")
    client_secret: str = Field(..., description="Azure client secret")


class AzureStartRequest(AzureCredentials):
    billing_account_id: str = Field(..., description="Azure billing account ID")
    start_date: str = Field(..., description="Report start date YYYY-MM-DD", examples=["2025-12-01"])
    end_date: str = Field(..., description="Report end date YYYY-MM-DD", examples=["2025-12-31"])
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
# Health
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
def index():
    """Serve the frontend SPA. Works on both Vercel and local dev."""
    html_path = Path(__file__).parent.parent / "public" / "index.html"
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
        raise HTTPException(status_code=502, detail=f"Alibaba Cloud API error: {str(e)}")


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
        raise HTTPException(status_code=502, detail=f"Alibaba Cloud API error: {str(e)}")

    if not items:
        raise HTTPException(status_code=404, detail="No billing data found for the given cycle.")

    output = io.StringIO()
    fieldnames = list(items[0].model_fields.keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for item in items:
        writer.writerow(item.model_dump())

    output.seek(0)
    filename = f"alibaba_billing_{req.billing_cycle}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
        raise HTTPException(status_code=502, detail=f"Alibaba Cloud API error: {str(e)}")


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
        raise HTTPException(status_code=401, detail=f"Azure authentication failed: {err}")

    location_url, err = client.get_ri_location(
        billing_account_id=req.billing_account_id,
        start_date=req.start_date,
        end_date=req.end_date,
        metric=req.metric,
        token=token,
    )
    if err:
        raise HTTPException(status_code=502, detail=f"Failed to start report generation: {err}")

    return AzureStartResponse(location_url=location_url)


@app.post("/api/azure/billing/poll", response_model=AzurePollResponse, tags=["azure"])
def azure_billing_poll(req: AzurePollRequest):
    """
    Step 2: poll Azure report status (single non-blocking check).

    Returns status "pending" while the report is still generating,
    or status "completed" with records when ready.
    The client (browser) should call this endpoint every ~10 seconds.
    """
    client = AzureCloudClient(
        tenant_id=req.tenant_id,
        client_id=req.client_id,
        client_secret=req.client_secret,
    )

    token, err = client.get_access_token()
    if err:
        raise HTTPException(status_code=401, detail=f"Azure authentication failed: {err}")

    status, csv_url, err = client.check_ri_report_once(location_url=req.location_url, token=token)

    if status == "error":
        raise HTTPException(status_code=502, detail=err or "Unknown Azure polling error")

    if status == "pending":
        return AzurePollResponse(status="pending", message="Report is still being generated, please retry.")

    # status == "completed"
    if not csv_url:
        raise HTTPException(status_code=502, detail="Report completed but no CSV URL returned.")

    csv_bytes, err = client.download_ri_csv(csv_url, token=token)
    if err:
        raise HTTPException(status_code=502, detail=f"Failed to download CSV: {err}")

    records = []
    if csv_bytes:
        import csv as csv_mod

        csv_str = csv_bytes.decode("utf-8-sig")
        reader = csv_mod.DictReader(csv_str.splitlines())
        for row in reader:
            records.append(dict(row))

    return AzurePollResponse(status="completed", csv_url=csv_url, records=records)


@app.post("/api/azure/billing/csv", tags=["azure"], summary="Download Azure billing CSV directly")
def azure_billing_csv(req: AzurePollRequest):
    """
    Download Azure billing CSV as a file attachment.
    Requires the location_url from the start endpoint (i.e., report must already be completed).
    """
    client = AzureCloudClient(
        tenant_id=req.tenant_id,
        client_id=req.client_id,
        client_secret=req.client_secret,
    )

    token, err = client.get_access_token()
    if err:
        raise HTTPException(status_code=401, detail=f"Azure authentication failed: {err}")

    status, csv_url, err = client.check_ri_report_once(location_url=req.location_url, token=token)

    if status == "error":
        raise HTTPException(status_code=502, detail=err)
    if status == "pending":
        raise HTTPException(status_code=202, detail="Report is still being generated, please poll first.")
    if not csv_url:
        raise HTTPException(status_code=502, detail="No CSV URL available.")

    csv_bytes, err = client.download_ri_csv(csv_url, token=token)
    if err:
        raise HTTPException(status_code=502, detail=f"Failed to download CSV: {err}")

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="azure_billing.csv"'},
    )


# ---------------------------------------------------------------------------
# Static frontend — mounted LAST so all /api/* routes take priority.
# On Vercel, public/ is served by the CDN and this code path is never hit.
# Locally this gives a single-port (8000) dev experience with no CORS config.
# ---------------------------------------------------------------------------
_PUBLIC_DIR = Path(__file__).parent.parent / "public"
if _PUBLIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=_PUBLIC_DIR, html=True), name="static")

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


class KubecostAllocationData(BaseModel):
    cluster_id: str = Field(..., description="集群ID")
    cluster_name: str = Field(..., description="集群名称")
    namespace: str = Field(..., description="命名空间")
    workload_name: Optional[str] = Field(None, description="工作负载名称")
    workload_type: Optional[str] = Field(None, description="工作负载类型")
    container_name: Optional[str] = Field(None, description="容器名称")

    start_date: datetime = Field(..., description="开始时间")
    end_date: datetime = Field(..., description="结束时间")
    window_start: datetime = Field(..., description="窗口开始时间")
    window_end: datetime = Field(..., description="窗口结束时间")

    cpu_cores_allocated: Optional[Decimal] = Field(None, description="分配CPU核数")
    cpu_cores_used: Optional[Decimal] = Field(None, description="使用CPU核数")
    memory_gb_allocated: Optional[Decimal] = Field(None, description="分配内存GB")
    memory_gb_used: Optional[Decimal] = Field(None, description="使用内存GB")
    storage_gb_allocated: Optional[Decimal] = Field(None, description="分配存储GB")

    total_cost: Decimal = Field(default=Decimal("0"), description="总成本")
    cpu_cost: Optional[Decimal] = Field(None, description="CPU成本")
    memory_cost: Optional[Decimal] = Field(None, description="内存成本")
    storage_cost: Optional[Decimal] = Field(None, description="存储成本")
    network_cost: Optional[Decimal] = Field(None, description="网络成本")

    labels: Optional[Dict] = Field(default_factory=dict, description="K8s标签")
    annotations: Optional[Dict] = Field(default_factory=dict, description="K8s注解")

    cloud_provider: str = Field(default="unknown", description="云服务商")
    region: Optional[str] = Field(None, description="区域")

    @field_validator("total_cost", "cpu_cost", "memory_cost", "storage_cost", "network_cost", mode="before")
    def convert_to_decimal(cls, v: Any) -> Optional[Decimal]:
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return Decimal(v)
            except:
                return Decimal("0")
        return Decimal(str(v))

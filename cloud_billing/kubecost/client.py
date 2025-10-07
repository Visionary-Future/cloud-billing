import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Iterator, List, Optional, Tuple
from urllib.parse import urljoin

import requests

from .types import KubecostAllocationData

logger = logging.getLogger(__name__)


class KubecostClient:
    def __init__(self, base_url: str, timeout: int = 30):
        """
        初始化kubecost客户端

        Args:
            base_url: kubecost服务的基础URL，如 http://kubecost.example.com:9090
            timeout: HTTP请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        self.session.headers.update({"Content-Type": "application/json", "User-Agent": "SoftwareOne-FinOps/1.0"})

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """
        发起HTTP请求

        返回 (data, error) 元组，遵循现有客户端模式
        """
        try:
            url = urljoin(self.base_url, endpoint)
            response = self.session.get(url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                return response.json(), None
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Kubecost API请求失败: {error_msg}")
                return None, error_msg

        except requests.RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            logger.error(f"Kubecost API请求异常: {error_msg}")
            return None, error_msg
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析失败: {str(e)}"
            logger.error(f"Kubecost响应解析失败: {error_msg}")
            return None, error_msg

    def get_allocation_data(
        self, start_date: datetime, end_date: datetime, window: str = "1d", aggregate_by: Optional[List[str]] = None
    ) -> Iterator[Tuple[Optional[KubecostAllocationData], Optional[str]]]:
        """
        获取成本分配数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            window: 时间窗口，如 "1d", "1h"
            aggregate_by: 聚合维度，如 ["cluster", "namespace"]（简化聚合以适配阿里云）

        Yields:
            (KubecostAllocationData, error) 元组
        """
        if aggregate_by is None:
            aggregate_by = ["cluster", "namespace"]

        start_iso = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_iso = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        params = {
            "window": f"{start_iso},{end_iso}",
            "step": window,
            "aggregate": ",".join(aggregate_by),
            "accumulate": "false",
        }

        logger.info(f"Kubecost请求参数: {params}")
        data, error = self._make_request("/model/allocation", params)
        if error:
            yield None, error
            return

        if not data or "data" not in data:
            yield None, "响应数据格式错误：缺少data字段"
            return

        try:
            for allocation_entry in data["data"]:
                if not isinstance(allocation_entry, dict):
                    continue

                for allocation_key, allocation_value in allocation_entry.items():
                    if not isinstance(allocation_value, dict):
                        continue

                    key_parts = allocation_key.split("/")
                    if len(key_parts) < 2:
                        continue

                    cluster_name = key_parts[0] if len(key_parts) > 0 else "unknown"
                    namespace = key_parts[1] if len(key_parts) > 1 else "default"
                    workload_name = key_parts[2] if len(key_parts) > 2 else None

                    total_cost = Decimal(str(allocation_value.get("totalCost", 0)))
                    cpu_cost = Decimal(str(allocation_value.get("cpuCost", 0)))
                    memory_cost = Decimal(str(allocation_value.get("ramCost", 0)))
                    storage_cost = Decimal(str(allocation_value.get("pvCost", 0)))

                    network_cost = Decimal(str(allocation_value.get("networkCost", 0)))
                    lb_cost = Decimal(str(allocation_value.get("loadBalancerCost", 0)))
                    total_network_cost = network_cost + lb_cost

                    cpu_core_hours = Decimal(str(allocation_value.get("cpuCoreHours", 0)))
                    ram_byte_hours = Decimal(str(allocation_value.get("ramByteHours", 0)))
                    pv_byte_hours = Decimal(str(allocation_value.get("pvByteHours", 0)))

                    minutes = Decimal(str(allocation_value.get("minutes", 1440)))  # 默认24小时
                    hours = minutes / Decimal("60")

                    cpu_cores_allocated = cpu_core_hours / hours if hours > 0 else None
                    memory_gb_allocated = (ram_byte_hours / hours / (1024**3)) if hours > 0 else None
                    storage_gb_allocated = (pv_byte_hours / hours / (1024**3)) if hours > 0 else None

                    cpu_cores_used = Decimal(str(allocation_value.get("cpuCoreUsageAverage", 0)))
                    memory_bytes_used = Decimal(str(allocation_value.get("ramByteUsageAverage", 0)))
                    memory_gb_used = memory_bytes_used / (1024**3) if memory_bytes_used > 0 else None

                    properties = allocation_value.get("properties", {})
                    labels = properties.get("labels", {}) if isinstance(properties, dict) else {}
                    annotations = properties.get("annotations", {}) if isinstance(properties, dict) else {}

                    if not labels and isinstance(properties, dict):
                        if "cluster" in properties:
                            cluster_name = properties["cluster"]
                        if "namespace" in properties:
                            namespace = properties["namespace"]

                    cloud_provider = self._detect_cloud_provider(labels, annotations, cluster_name)

                    window_info = allocation_value.get("window", {})
                    window_start = self._parse_time(window_info.get("start")) or start_date
                    window_end = self._parse_time(window_info.get("end")) or end_date

                    allocation_data = KubecostAllocationData(
                        cluster_id=cluster_name,
                        cluster_name=cluster_name,
                        namespace=namespace,
                        workload_name=workload_name,
                        workload_type=self._extract_workload_type(labels),
                        container_name=self._extract_container_name(allocation_value),
                        start_date=start_date,
                        end_date=end_date,
                        window_start=window_start,
                        window_end=window_end,
                        cpu_cores_allocated=cpu_cores_allocated
                        if cpu_cores_allocated and cpu_cores_allocated > 0
                        else None,
                        cpu_cores_used=cpu_cores_used if cpu_cores_used > 0 else None,
                        memory_gb_allocated=memory_gb_allocated
                        if memory_gb_allocated and memory_gb_allocated > 0
                        else None,
                        memory_gb_used=memory_gb_used if memory_gb_used and memory_gb_used > 0 else None,
                        storage_gb_allocated=storage_gb_allocated
                        if storage_gb_allocated and storage_gb_allocated > 0
                        else None,
                        total_cost=total_cost,
                        cpu_cost=cpu_cost if cpu_cost > 0 else None,
                        memory_cost=memory_cost if memory_cost > 0 else None,
                        storage_cost=storage_cost if storage_cost > 0 else None,
                        network_cost=total_network_cost if total_network_cost > 0 else None,
                        labels=labels,
                        annotations=annotations,
                        cloud_provider=cloud_provider,
                        region=self._extract_region(labels, annotations),
                    )

                    yield allocation_data, None

        except Exception as e:
            error_msg = f"解析分配数据失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield None, error_msg

    def _detect_cloud_provider(self, labels: Dict, annotations: Dict, cluster_name: str) -> str:
        for key, value in labels.items():
            key_lower = key.lower()
            if "alibaba" in key_lower or "aliyun" in key_lower:
                return "alibaba"
            elif "azure" in key_lower or "microsoft" in key_lower:
                return "azure"
            elif "aws" in key_lower or "amazon" in key_lower:
                return "aws"
            elif "gcp" in key_lower or "google" in key_lower:
                return "gcp"

        cluster_lower = cluster_name.lower()
        if "alibaba" in cluster_lower or "aliyun" in cluster_lower:
            return "alibaba"
        elif "azure" in cluster_lower or "aks" in cluster_lower:
            return "azure"
        elif "aws" in cluster_lower or "eks" in cluster_lower:
            return "aws"
        elif "gcp" in cluster_lower or "gke" in cluster_lower:
            return "gcp"

        return "unknown"

    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """
        解析ISO 8601时间字符串

        Args:
            time_str: ISO格式时间字符串，如 "2025-09-06T00:00:00Z"

        Returns:
            解析后的datetime对象，解析失败返回None
        """
        if not time_str:
            return None

        try:
            if time_str.endswith("Z"):
                time_str = time_str[:-1] + "+00:00"
            return datetime.fromisoformat(time_str)
        except (ValueError, AttributeError):
            logger.warning(f"无法解析时间字符串: {time_str}")
            return None

    def _extract_workload_type(self, labels: Dict) -> Optional[str]:
        if "app.kubernetes.io/component" in labels:
            return labels["app.kubernetes.io/component"]
        if "workload.user.cattle.io/workloadselector" in labels:
            return "Deployment"

        for key in labels:
            if "workload" in key.lower() or "component" in key.lower():
                return labels[key]

        return None

    def _extract_container_name(self, allocation_data: Dict) -> Optional[str]:
        properties = allocation_data.get("properties", {})
        return properties.get("container", None)

    def _extract_region(self, labels: Dict, annotations: Dict) -> Optional[str]:
        region_keys = [
            "topology.kubernetes.io/region",
            "failure-domain.beta.kubernetes.io/region",
            "kubernetes.io/region",
        ]

        for key in region_keys:
            if key in labels:
                return labels[key]

        for key, value in labels.items():
            if "region" in key.lower() or "zone" in key.lower():
                return value

        return None

    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        测试与kubecost的连接

        Returns:
            (is_connected, error_message)
        """
        now = datetime.now()
        start_time = now - timedelta(days=1)

        start_iso = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        params = {"window": f"{start_iso},{end_iso}", "step": "1d", "aggregate": "cluster,namespace"}

        _, error = self._make_request("/model/allocation", params)
        if error:
            return False, f"连接测试失败: {error}"
        return True, None

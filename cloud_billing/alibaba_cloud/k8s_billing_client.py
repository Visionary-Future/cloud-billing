from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


@dataclass
class KubecostConfig:
    """Kubecost configuration for Alibaba Cloud"""

    kubecost_url: str
    cluster_name: str
    timeout: int = 30
    headers: Optional[Dict[str, str]] = None


class K8sBillingClient:
    def __init__(self, config: KubecostConfig):
        """
        Initialize Kubecost client for Alibaba Cloud billing queries

        Args:
            config: KubecostConfig object containing connection details
        """
        self.config = config
        self.session = requests.Session()
        if config.headers:
            self.session.headers.update(config.headers)

    def query_monthly_cost(self, year: int, month: int) -> Dict[str, Any]:
        """
        Query monthly cost data from Kubecost for Alibaba Cloud

        Args:
            year: Year (e.g., 2024)
            month: Month (1-12)

        Returns:
            Dict containing cost data
        """
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        return self._query_cost_range(start_date, end_date)

    def _query_cost_range(
        self, start_date: datetime, end_date: datetime, aggregate_by: str = "cluster", step: str = "1d"
    ) -> Dict[str, Any]:
        """
        Query cost data for a specific date range

        Args:
            start_date: Start date
            end_date: End date
            aggregate_by: How to aggregate data (cluster, namespace, pod, etc.)
            step: Time step for aggregation

        Returns:
            Dict containing cost response data
        """
        url = f"{self.config.kubecost_url}/model/allocation"

        params = {
            "window": f"{start_date.isoformat()},{end_date.isoformat()}",
            "aggregate": aggregate_by,
            "step": step,
            "filter": f"cluster:{self.config.cluster_name}",
        }

        try:
            response = self.session.get(url, params=params, timeout=self.config.timeout)
            response.raise_for_status()

            json_data = response.json()

            if not json_data or "data" not in json_data:
                raise ValueError("Invalid response format from Kubecost API")

            return json_data

        except requests.exceptions.Timeout:
            raise Exception(f"Kubecost API request timed out after {self.config.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Failed to connect to Kubecost API at {self.config.kubecost_url}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error from Kubecost API: {e.response.status_code} - {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to query Kubecost API: {str(e)}")
        except ValueError as e:
            raise Exception(f"Invalid JSON response from Kubecost API: {str(e)}")

    def get_cluster_costs_summary(self, year: int, month: int) -> Dict[str, float]:
        """
        Get summarized cluster costs for a specific month

        Args:
            year: Year
            month: Month

        Returns:
            Dict with cost summary (cpu_cost, memory_cost, storage_cost, total_cost)
        """
        data = self.query_monthly_cost(year, month)

        summary = {"cpu_cost": 0.0, "memory_cost": 0.0, "storage_cost": 0.0, "network_cost": 0.0, "total_cost": 0.0}

        if "data" in data:
            for allocation_data in data["data"]:
                for allocation in allocation_data.values():
                    if isinstance(allocation, dict):
                        summary["cpu_cost"] += allocation.get("cpuCost", 0.0)
                        summary["memory_cost"] += allocation.get("ramCost", 0.0)
                        summary["storage_cost"] += allocation.get("pvCost", 0.0)
                        summary["network_cost"] += allocation.get("networkCost", 0.0)
                        summary["total_cost"] += allocation.get("totalCost", 0.0)

        return summary

    def get_namespace_costs(self, year: int, month: int) -> List[Dict[str, Any]]:
        """
        Get cost breakdown by namespace for a specific month

        Args:
            year: Year
            month: Month

        Returns:
            List of namespace cost data
        """
        data = self.query_monthly_cost(year, month, aggregate_by="namespace")
        namespaces = []

        if "data" in data:
            for allocation_data in data["data"]:
                for ns_name, allocation in allocation_data.items():
                    if isinstance(allocation, dict):
                        namespaces.append(
                            {
                                "namespace": ns_name,
                                "cpu_cost": allocation.get("cpuCost", 0.0),
                                "memory_cost": allocation.get("ramCost", 0.0),
                                "storage_cost": allocation.get("pvCost", 0.0),
                                "network_cost": allocation.get("networkCost", 0.0),
                                "total_cost": allocation.get("totalCost", 0.0),
                                "cpu_hours": allocation.get("cpuCoreHours", 0.0),
                                "memory_gb_hours": allocation.get("ramByteHours", 0.0) / (1024**3),
                            }
                        )

        return sorted(namespaces, key=lambda x: x["total_cost"], reverse=True)

    def get_workload_costs(self, year: int, month: int, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get cost breakdown by workload (deployments, pods) for a specific month

        Args:
            year: Year
            month: Month
            namespace: Optional namespace filter

        Returns:
            List of workload cost data
        """
        aggregate_by = "pod"
        data = self.query_monthly_cost(year, month, aggregate_by=aggregate_by)
        workloads = []

        if "data" in data:
            for allocation_data in data["data"]:
                for pod_name, allocation in allocation_data.items():
                    if isinstance(allocation, dict):
                        pod_namespace = allocation.get("properties", {}).get("namespace", "")

                        if namespace and pod_namespace != namespace:
                            continue

                        workloads.append(
                            {
                                "pod": pod_name,
                                "namespace": pod_namespace,
                                "controller_kind": allocation.get("properties", {}).get("controller", ""),
                                "cpu_cost": allocation.get("cpuCost", 0.0),
                                "memory_cost": allocation.get("ramCost", 0.0),
                                "storage_cost": allocation.get("pvCost", 0.0),
                                "network_cost": allocation.get("networkCost", 0.0),
                                "total_cost": allocation.get("totalCost", 0.0),
                            }
                        )

        return sorted(workloads, key=lambda x: x["total_cost"], reverse=True)

    def get_alibaba_cloud_resources_cost(self, year: int, month: int) -> Dict[str, Any]:
        """
        Get Alibaba Cloud specific resource costs with detailed breakdown

        Args:
            year: Year
            month: Month

        Returns:
            Dict with Alibaba Cloud resource cost breakdown
        """
        data = self.query_monthly_cost(year, month, aggregate_by="cluster")

        alibaba_resources = {
            "ecs_instances": 0.0,
            "rds_instances": 0.0,
            "slb_instances": 0.0,
            "oss_storage": 0.0,
            "vpc_network": 0.0,
            "total_cost": 0.0,
            "resource_details": [],
        }

        if "data" in data:
            for allocation_data in data["data"]:
                for resource_name, allocation in allocation_data.items():
                    if isinstance(allocation, dict):
                        properties = allocation.get("properties", {})
                        instance_type = properties.get("instanceType", "")
                        node_type = properties.get("nodeType", "")

                        cost_breakdown = {
                            "resource_name": resource_name,
                            "instance_type": instance_type,
                            "node_type": node_type,
                            "cpu_cost": allocation.get("cpuCost", 0.0),
                            "memory_cost": allocation.get("ramCost", 0.0),
                            "storage_cost": allocation.get("pvCost", 0.0),
                            "network_cost": allocation.get("networkCost", 0.0),
                            "total_cost": allocation.get("totalCost", 0.0),
                        }

                        alibaba_resources["resource_details"].append(cost_breakdown)
                        alibaba_resources["total_cost"] += cost_breakdown["total_cost"]

                        if "ecs" in instance_type.lower():
                            alibaba_resources["ecs_instances"] += cost_breakdown["total_cost"]
                        elif "rds" in instance_type.lower():
                            alibaba_resources["rds_instances"] += cost_breakdown["total_cost"]
                        elif "slb" in instance_type.lower():
                            alibaba_resources["slb_instances"] += cost_breakdown["total_cost"]

        return alibaba_resources

    def format_cost_report(self, cost_data: Dict[str, Any], report_type: str = "summary") -> str:
        """
        Format cost data into a readable report

        Args:
            cost_data: Cost data from any of the get_* methods
            report_type: Type of report (summary, detailed)

        Returns:
            Formatted string report
        """
        if report_type == "summary" and "total_cost" in cost_data:
            return (
                f"Total Cost: ${cost_data['total_cost']:.2f}\n"
                f"CPU Cost: ${cost_data.get('cpu_cost', 0):.2f}\n"
                f"Memory Cost: ${cost_data.get('memory_cost', 0):.2f}\n"
                f"Storage Cost: ${cost_data.get('storage_cost', 0):.2f}\n"
                f"Network Cost: ${cost_data.get('network_cost', 0):.2f}"
            )

        elif isinstance(cost_data, list):
            report = "Cost Breakdown:\n"
            items_to_show = cost_data[:10] if len(cost_data) > 10 else cost_data
            for i, item in enumerate(items_to_show, 1):
                name = item.get("namespace") or item.get("pod") or item.get("resource_name", "Unknown")
                cost = item.get("total_cost", 0)
                report += f"{i:2d}. {name}: ${cost:.2f}\n"
            return report

        return str(cost_data)

    def validate_config(self) -> bool:
        """
        Validate the Kubecost configuration

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.config.kubecost_url:
            raise ValueError("Kubecost URL is required")

        if not self.config.cluster_name:
            raise ValueError("Cluster name is required")

        if not self.config.kubecost_url.startswith(("http://", "https://")):
            raise ValueError("Kubecost URL must start with http:// or https://")

        try:
            test_url = f"{self.config.kubecost_url}/model/allocation"
            self.session.head(test_url, timeout=5)
        except requests.exceptions.RequestException:
            raise ValueError(f"Cannot connect to Kubecost API at {self.config.kubecost_url}")

        return True

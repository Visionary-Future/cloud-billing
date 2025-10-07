from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

from cloud_billing.kubecost.client import KubecostClient
from cloud_billing.kubecost.types import KubecostAllocationData

azure_sample_response = {
    "data": [
        {
            "cluster-one/utc": {
                "cpuCoreHours": 0.02917,
                "cpuCoreRequestAverage": 0.05,
                "cpuCoreUsageAverage": 0.02627,
                "cpuCores": 0.05,
                "cpuCost": 0.00092,
                "cpuCostAdjustment": 0,
                "cpuCostIdle": 0,
                "cpuEfficiency": 0.52538,
                "end": "2025-10-06T23:35:00Z",
                "externalCost": 0,
                "gpuAllocation": {"gpuRequestAverage": 0, "gpuUsageAverage": 0, "isGPUShared": False},
                "gpuCost": 0,
                "gpuCostAdjustment": 0,
                "gpuCostIdle": 0,
                "gpuCount": 0,
                "gpuEfficiency": 0,
                "gpuHours": 0,
                "lbAllocations": None,
                "loadBalancerCost": 0,
                "loadBalancerCostAdjustment": 0,
                "minutes": 35,
                "name": "cluster-one/utc",
                "networkCost": 0,
                "networkCostAdjustment": 0,
                "networkCrossRegionCost": 0,
                "networkCrossZoneCost": 0,
                "networkInternetCost": 0,
                "networkReceiveBytes": 2133204.67414,
                "networkTransferBytes": 3679378.54565,
                "properties": {
                    "cluster": "cluster-one",
                    "labels": {
                        "agentpool": "pnp2",
                        "app": "utc-project-tool",
                        "beta_kubernetes_io_arch": "amd64",
                        "beta_kubernetes_io_instance_type": "Standard_D16_v4",
                        "beta_kubernetes_io_os": "linux",
                        "failure_domain_beta_kubernetes_io_region": "chinanorth3",
                        "failure_domain_beta_kubernetes_io_zone": "0",
                        "field_cattle_io_projectId": "p-xsfhk",
                        "kubernetes_azure_com_agentpool": "pnp2",
                        "kubernetes_azure_com_cluster": "nprd-aks-rg-000_cn3-nprd-app-aks-001",
                        "kubernetes_azure_com_consolidated_additional_properties": "89394975-1fdb-11ef-b9de-cccsdsf",
                        "kubernetes_azure_com_kubelet_identity_client_id": "9c2348c5-2a7a-4478-a876-4e435cccd",
                        "kubernetes_azure_com_mode": "user",
                        "kubernetes_azure_com_node_image_version": "AKSUbuntu-2204gen2containerd-202405.03.0",
                        "kubernetes_azure_com_nodepool_type": "VirtualMachineScaleSets",
                        "kubernetes_azure_com_os_sku": "Ubuntu",
                        "kubernetes_azure_com_os_sku_effective": "Ubuntu2204",
                        "kubernetes_azure_com_os_sku_requested": "Ubuntu",
                        "kubernetes_azure_com_role": "agent",
                        "kubernetes_azure_com_storageprofile": "managed",
                        "kubernetes_azure_com_storagetier": "Standard_LRS",
                        "kubernetes_io_arch": "amd64",
                        "kubernetes_io_hostname": "aks-pnp2-22222-vmss000001",
                        "kubernetes_io_metadata_name": "utc",
                        "kubernetes_io_os": "linux",
                        "kubernetes_io_role": "agent",
                        "node_kubernetes_io_instance_type": "Standard_D16_v4",
                        "pod_template_hash": "65f7ccbb55",
                        "providerID": "xxxx",
                        "storageprofile": "managed",
                        "storagetier": "Standard_LRS",
                        "topology_kubernetes_io_region": "chinanorth3",
                        "topology_kubernetes_io_zone": "0",
                        "version": "159",
                    },
                    "namespace": "utc",
                    "namespaceLabels": {"field_cattle_io_projectId": "p-xsfhk", "kubernetes_io_metadata_name": "utc"},
                },
                "pvByteHours": 0,
                "pvBytes": 0,
                "pvCost": 0,
                "pvCostAdjustment": 0,
                "pvs": None,
                "ramByteHours": 162479023.68627,
                "ramByteRequestAverage": 268435456,
                "ramByteUsageAverage": 279514316.8,
                "ramBytes": 278535469.17647,
                "ramCost": 0.00064,
                "ramCostAdjustment": 0,
                "ramCostIdle": 0,
                "ramEfficiency": 1.04127,
                "rawAllocationOnly": {
                    "cpuCoreUsageMax": 0.05041955128767863,
                    "gpuUsageMax": 0,
                    "ramByteUsageMax": 279994368,
                },
                "sharedCost": 0,
                "start": "2025-10-06T23:00:00Z",
                "totalCost": 0.00156,
                "totalEfficiency": 0.73698,
                "window": {"end": "2025-10-07T00:00:00Z", "start": "2025-10-06T23:00:00Z"},
            }
        }
    ]
}


def mock_azure_get(*args, **kwargs):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = azure_sample_response
    return mock_resp


@patch("cloud_billing.kubecost.client.requests.Session.get", side_effect=mock_azure_get)
def test_get_allocation_data_azure_sample(mocked_get):
    client = KubecostClient("http://fake-kubecost")
    start = datetime(2025, 10, 6, 23, 0, 0)
    end = datetime(2025, 10, 7, 0, 0, 0)
    results = list(client.get_allocation_data(start, end))
    assert len(results) == 1
    data, error = results[0]
    assert error is None
    assert isinstance(data, KubecostAllocationData)
    assert data.cluster_id == "cluster-one"
    assert data.namespace == "utc"
    assert data.workload_name is None
    assert data.cpu_cost == Decimal("0.00092")
    assert data.memory_cost == Decimal("0.00064")
    assert data.storage_cost is None or data.storage_cost == Decimal("0")
    assert data.network_cost is None or data.network_cost == Decimal("0")
    assert data.labels is not None
    assert data.labels["app"] == "utc-project-tool"
    assert data.region == "chinanorth3"
    assert data.container_name is None
    assert data.window_start == datetime(2025, 10, 6, 23, 0, 0, tzinfo=timezone.utc)
    assert data.window_end == datetime(2025, 10, 7, 0, 0, 0, tzinfo=timezone.utc)
    assert data.cloud_provider == "azure"


def mock_get(*args, **kwargs):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = azure_sample_response
    return mock_resp


def mock_get_error(*args, **kwargs):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    return mock_resp


@patch("cloud_billing.kubecost.client.requests.Session.get", side_effect=mock_azure_get)
def test_get_allocation_data_success(mock_azure_get):
    client = KubecostClient("http://fake-kubecost")
    start = datetime(2025, 10, 6)
    end = datetime(2025, 10, 7)
    results = list(client.get_allocation_data(start, end))
    assert len(results) == 1
    data, error = results[0]
    assert error is None
    assert isinstance(data, KubecostAllocationData)
    assert data.cluster_id == "cluster-one"
    assert data.namespace == "utc"
    assert data.workload_name is None
    assert data.cpu_cost == Decimal("0.00092")
    assert data.memory_cost == Decimal("0.00064")
    assert data.storage_cost is None
    assert data.network_cost is None
    assert data.region == "chinanorth3"
    assert data.container_name is None
    assert data.window_start == datetime(2025, 10, 6, 23, 0, tzinfo=timezone.utc)
    assert data.window_end == datetime(2025, 10, 7, 0, 0, tzinfo=timezone.utc)


@patch("cloud_billing.kubecost.client.requests.Session.get", side_effect=mock_get_error)
def test_get_allocation_data_http_error(mock_azure_get):
    client = KubecostClient("http://fake-kubecost")
    start = datetime(2025, 10, 6)
    end = datetime(2025, 10, 7)
    results = list(client.get_allocation_data(start, end))
    assert len(results) == 1
    data, error = results[0]
    assert data is None
    assert error is not None
    assert "HTTP 500" in error


@patch("cloud_billing.kubecost.client.requests.Session.get", side_effect=mock_get)
def test_test_connection_success(mock_azure_get):
    client = KubecostClient("http://fake-kubecost")
    ok, error = client.test_connection()
    assert ok is True
    assert error is None


@patch("cloud_billing.kubecost.client.requests.Session.get", side_effect=mock_get_error)
def test_test_connection_fail(mock_azure_get):
    client = KubecostClient("http://fake-kubecost")
    ok, error = client.test_connection()
    assert ok is False
    assert error is not None
    assert "连接测试失败" in error

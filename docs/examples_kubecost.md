# Kubecost Allocation Example

This short example shows how to fetch allocation data from a Kubecost instance using the bundled helper script `scripts/get_kubecost_allocation.py`.

The script fetches allocation records for the fixed date range 2025-10-06 → 2025-10-07 and prints each record as a JSON/Pydantic model per line.

Usage:

```bash
python scripts/get_kubecost_allocation.py --base-url http://kubecost.example.com:9090
```

You can save the output to a file:

```bash
python scripts/get_kubecost_allocation.py --base-url http://kubecost.example.com:9090 --output allocations.jsonl
```

The models printed are instances of `cloud_billing.kubecost.types.KubecostAllocationData` and include fields such as `cluster_name`, `namespace`, `workload_name`, `cpu_cores_used`, and `total_cost`.

Tip: set the environment variable `KUBECOST_BASE_URL` to avoid passing `--base-url` repeatedly.

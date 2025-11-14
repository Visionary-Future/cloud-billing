#!/usr/bin/env python3
"""Fetch Kubecost allocation data for 2025-10-06 → 2025-10-07 and print as JSON lines.

Usage examples:
  # use environment variable KUBECOST_BASE_URL or default to http://localhost:9090
  python scripts/get_kubecost_allocation.py

  # specify base URL and save to file
  python scripts/get_kubecost_allocation.py --base-url http://kubecost.example.com:9090 --output allocations.jsonl
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime
from typing import Optional

from cloud_billing.kubecost.client import KubecostClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Kubecost allocation data for 2025-10-06 → 2025-10-07")
    parser.add_argument(
        "--base-url",
        help="Kubecost base URL (or set KUBECOST_BASE_URL env var)",
        default=os.environ.get("KUBECOST_BASE_URL", "http://localhost:9090"),
    )
    parser.add_argument("--window", help="time step/window (e.g. 1d, 1h)", default="1d")
    parser.add_argument("--output", help="Optional output file (JSONL). If omitted, prints to stdout", default=None)
    args = parser.parse_args()
    base_url = args.base_url
    client = KubecostClient(base_url)

    # fixed date range requested by the user
    start_date = datetime(2025, 10, 6)
    end_date = datetime(2025, 10, 7)

    out_file: Optional[object] = None
    if args.output:
        out_file = open(args.output, "w", encoding="utf-8")

    try:
        count = 0
        for allocation, error in client.get_allocation_data(start_date, end_date, window=args.window):
            if error:
                print(f"Error: {error}")
                continue

            # Print JSON representation (Pydantic model -> dict)
            try:
                if hasattr(allocation, "model_dump"):
                    obj = allocation.model_dump()
                elif hasattr(allocation, "dict"):
                    obj = allocation.dict()
                else:
                    obj = allocation.__dict__

                import json as _json

                line = _json.dumps(obj, default=str, ensure_ascii=False)
            except Exception:
                # Fallback to repr
                line = repr(allocation)

            if out_file:
                out_file.write(line + "\n")
            else:
                print(line)

            count += 1

        print(f"Finished. Processed {count} allocation records.")

    finally:
        if out_file:
            out_file.close()


if __name__ == "__main__":
    main()

"""Pytest configuration – provide mock stubs for cloud SDKs not installed locally."""
import sys
import types
from unittest.mock import MagicMock


def _make_module(name: str, is_package: bool = False) -> types.ModuleType:
    """Create a stub module that Python's import system accepts."""
    mod = types.ModuleType(name)
    if is_package:
        mod.__path__ = []
    return mod


def _setup_cloud_sdk_mocks() -> None:
    """Ensure cloud SDK modules resolve so the test suite can import the client."""

    # Parent packages (need __path__ so sub-module imports work)
    packages: dict[str, types.ModuleType] = {}

    def _ensure_package(name: str) -> types.ModuleType:
        if name not in packages:
            packages[name] = _make_module(name, is_package=True)
            if name not in sys.modules:
                sys.modules[name] = packages[name]
        return packages[name]

    def _ensure_module(name: str) -> types.ModuleType:
        if name in sys.modules:
            return sys.modules[name]
        # Ensure parent package exists
        if "." in name:
            parent = name.rsplit(".", 1)[0]
            _ensure_package(parent)
        mod = _make_module(name)
        sys.modules[name] = mod
        return mod

    # --- aliyun SDK stubs ---
    _ensure_module("aliyunsdkcore.auth.credentials")
    sys.modules["aliyunsdkcore.auth.credentials"].AccessKeyCredential = MagicMock
    sys.modules["aliyunsdkcore.auth.credentials"].StsTokenCredential = MagicMock

    client_mod = _ensure_module("aliyunsdkcore.client")
    client_mod.AcsClient = MagicMock
    client_mod.CommonRequest = MagicMock
    client_mod.RpcClient = MagicMock

    _ensure_module("aliyunsdkbssopenapi.request.v20171214")

    # --- AWS stubs ---
    _ensure_module("boto3")
    sys.modules["boto3"].client = MagicMock()
    sys.modules["boto3"].Session = MagicMock()
    _ensure_module("botocore.exceptions")

    # --- Huawei SDK stubs ---
    _ensure_module("huaweicloudsdkcore.auth.credentials")
    sys.modules["huaweicloudsdkcore.auth.credentials"].BasicCredentials = MagicMock
    _ensure_module("huaweicloudsdkcore.exceptions")
    hw_http_config = _ensure_module("huaweicloudsdkcore.http.http_config")
    hw_http_config.HttpConfig = MagicMock

    hw_bss = _ensure_module("huaweicloudsdkbss.v2")
    hw_bss.BssClient = MagicMock
    hw_bss.ShowCustomerMonthlySumRequest = MagicMock

    _ensure_module("huaweicloudsdkbssintl.v2.region.region_provider")

    # --- Google Cloud stubs (installed via pip, but just in case) ---
    for mod_name in [
        "google.cloud.billing_v1.types.cloud_billing",
        "google.cloud.bigquery",
        "google.api_core.exceptions",
        "google.auth.credentials",
        "google.oauth2.service_account",
    ]:
        _ensure_module(mod_name)


_setup_cloud_sdk_mocks()

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

    class _StubCommonRequest:
        """Stub for aliyunsdkcore.client.CommonRequest with real getter behavior."""

        def __init__(self) -> None:
            self._action_name: str = ""
            self._domain: str = ""
            self._query_params: dict[str, str] = {}

        def set_accept_format(self, fmt: str) -> None:
            pass

        def set_domain(self, domain: str) -> None:
            self._domain = domain

        def set_method(self, method: str) -> None:
            pass

        def set_protocol_type(self, proto: str) -> None:
            pass

        def set_version(self, version: str) -> None:
            pass

        def set_action_name(self, name: str) -> None:
            self._action_name = name

        def add_query_param(self, key: str, value: str) -> None:
            self._query_params[key] = value

        def get_action_name(self) -> str:
            return self._action_name

        def get_domain(self) -> str:
            return self._domain

        def get_query_params(self) -> dict[str, str]:
            return dict(self._query_params)

    client_mod = _ensure_module("aliyunsdkcore.client")
    client_mod.AcsClient = MagicMock
    client_mod.CommonRequest = _StubCommonRequest
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
    class _StubHttpConfig:
        """Stub for huaweicloudsdkcore.http.http_config.HttpConfig."""

        ignore_ssl_verification: bool = False

        @classmethod
        def get_default_config(cls) -> "_StubHttpConfig":
            return cls()

    hw_http_config = _ensure_module("huaweicloudsdkcore.http.http_config")
    hw_http_config.HttpConfig = _StubHttpConfig

    class _StubBssResponse:
        """Stub response with to_dict() for Huawei BSS API responses."""

        def to_dict(self) -> dict:
            return {"bill_sums": [], "total_count": 0, "currency": "CNY"}

    class _StubBssClient:
        """Stub BssClient that returns empty results by default."""

        def show_customer_monthly_sum(self, request) -> _StubBssResponse:
            return _StubBssResponse()

    class _StubBssClientBuilder:
        """Fluent builder stub for BssClient.new_builder() chain."""

        def with_http_config(self, config) -> "_StubBssClientBuilder":
            return self

        def with_credentials(self, credentials) -> "_StubBssClientBuilder":
            return self

        def with_endpoint(self, endpoint: str) -> "_StubBssClientBuilder":
            return self

        def build(self) -> _StubBssClient:
            return _StubBssClient()

    hw_bss = _ensure_module("huaweicloudsdkbss.v2")
    hw_bss.BssClient = type("BssClient", (), {"new_builder": staticmethod(_StubBssClientBuilder)})
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

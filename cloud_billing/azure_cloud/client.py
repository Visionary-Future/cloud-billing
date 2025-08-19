import csv
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import requests
from requests_toolbelt.multipart import encoder

from .types import BillingRecord


@dataclass
class BlobInfo:
    """Blob信息数据结构"""

    status: str
    manifest: Dict[str, Any]


@dataclass
class RiUrlRequest:
    """
    RI 账单 URL 请求参数数据类
    """

    metric: str
    time_period: Dict[str, str]


class AzureCloudClient:

    TOKEN_URL_TEMPLATE = "https://login.partner.microsoftonline.cn/{tenant_id}/oauth2/token?api-version=1.0"
    AUTH_RESOURCE = "https://management.chinacloudapi.cn"

    BILLING_API_VERSION = "2023-08-01"
    BILLING_BASE_URL = "https://management.chinacloudapi.cn/providers/Microsoft.Billing/billingAccounts/{}/providers/Microsoft.CostManagement/generateCostDetailsReport"
    POLLING_INTERVAL = 30

    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        """
        初始化RI管理客户端

        :param tenant_id: Azure租户ID
        :param client_id: 应用程序(客户端)ID
        :param client_secret: 客户端密钥
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = requests.Session()
        self._current_token = None

    def _prepare_auth_form_data(self) -> encoder.MultipartEncoder:
        """准备认证所需的表单数据"""
        return encoder.MultipartEncoder(
            fields={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "Resource": self.AUTH_RESOURCE,
            }
        )

    def _validate_token_response(self, response: requests.Response) -> Tuple[Optional[str], Optional[str]]:
        """验证并解析令牌响应"""
        if response.status_code != 200:
            error_msg = f"HTTP响应失败，状态码：{response.status_code}"
            return None, error_msg

        try:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                return None, "响应中未找到access_token"
            return access_token, None
        except json.JSONDecodeError:
            return None, "响应不是有效的JSON格式"
        except Exception as e:
            return None, f"解析响应时出错: {str(e)}"

    def get_access_token(self) -> Tuple[Optional[str], Optional[str]]:
        """
        获取Azure访问令牌

        :return: 元组 (access_token, error)
                 成功时返回 (token, None)
                 失败时返回 (None, error_message)
        """
        try:
            token_url = self.TOKEN_URL_TEMPLATE.format(tenant_id=self.tenant_id)
            form = self._prepare_auth_form_data()

            headers = {"Content-Type": form.content_type}
            response = requests.post(token_url, data=form, headers=headers)

            token, error = self._validate_token_response(response)
            if not error:
                self._current_token = token
            return token, error
        except requests.exceptions.RequestException as e:
            return None, f"请求失败: {str(e)}"
        except Exception as e:
            return None, f"未知错误: {str(e)}"

    def refresh_token(self) -> Tuple[Optional[str], Optional[str]]:
        """
        刷新访问令牌

        :return: 元组 (access_token, error)
        """
        return self.get_access_token()

    def _build_billing_request_url(self, billing_account_id: str) -> str:
        """构建账单请求URL"""
        return self.BILLING_BASE_URL.format(billing_account_id) + f"?api-version={self.BILLING_API_VERSION}"

    def _prepare_billing_request_params(self, start_date: str, end_date: str, metric: str) -> Dict[str, Any]:
        """准备账单请求参数"""
        return {"metric": metric, "timePeriod": {"start": start_date, "end": end_date}}

    def get_ri_location(
        self, billing_account_id: str, start_date: str, end_date: str, metric: str, token: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        获取RI账单URL请求链接

        :param billing_account_id: 账单账户ID
        :param start_date: 开始日期 (YYYY-MM-DD)
        :param end_date: 结束日期 (YYYY-MM-DD)
        :param metric: 计量类型 (如 ActualCost)
        :param token: 访问令牌(可选，如果不提供将使用缓存的令牌)
        :return: (location_url, error) 元组
        """
        use_token = token if token else self._current_token
        if not use_token:
            return None, "未提供有效的访问令牌"

        try:
            url = self._build_billing_request_url(billing_account_id)
            params = self._prepare_billing_request_params(start_date, end_date, metric)

            headers = {"Authorization": f"Bearer {use_token}", "Content-Type": "application/json"}

            response = self.session.post(url, headers=headers, json=params)

            if response.status_code == 202:
                location = response.headers.get("Location")
                if location:
                    return location, None
                return None, "响应中未找到Location头"
            else:
                error_msg = f"请求失败，状态码: {response.status_code}"
                try:
                    error_details = response.json()
                    error_msg += f", 详情: {error_details}"
                except:
                    pass
                return None, error_msg

        except requests.exceptions.RequestException as e:
            print(e)
            return None, f"请求异常: {str(e)}"
        except Exception as e:
            return None, f"处理请求时发生错误: {str(e)}"

    def get_ri_report(self, location_url: str, token: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """
        获取RI账单报告数据
        :param location_url: 从get_ri_location获取的位置URL
        :param token: 访问令牌(可选)
        :return: (report_data, error) 元组
        """
        # 确定使用的令牌
        use_token = token if token else self._current_token
        if not use_token:
            return None, "未提供有效的访问令牌"

        try:
            headers = {"Authorization": f"Bearer {use_token}"}
            response = self.session.get(location_url, headers=headers)

            if response.status_code == 200:
                try:
                    return response.json(), None
                except json.JSONDecodeError:
                    return None, "无法解析响应JSON"
            elif response.status_code == 202:
                return None, "报告仍在处理中，请稍后再试"
            else:
                error_msg = f"获取报告失败，状态码: {response.status_code}"
                try:
                    error_details = response.json()
                    error_msg += f", 详情: {error_details}"
                except:
                    pass
                return None, error_msg

        except requests.exceptions.RequestException as e:
            return None, f"请求异常: {str(e)}"
        except Exception as e:
            return None, f"处理请求时发生错误: {str(e)}"

    def get_ri_csv_url(
        self, location_url: str, token: Optional[str] = None, max_retries: int = 1
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        获取RI账单CSV文件下载URL
        :param location_url: 从get_ri_location获取的位置URL
        :param token: 访问令牌(可选)
        :param max_retries: 最大轮询次数(默认10次)
        :return: (csv_url, error) 元组
        """
        use_token = token if token else self._current_token
        if not use_token:
            return None, "未提供有效的访问令牌"
        print(f"使用的访问令牌: {use_token}")
        try:
            headers = {"Authorization": f"Bearer {use_token}"}
            retry_count = 0

            while retry_count < max_retries:
                response = self.session.get(location_url, headers=headers)
                if response.status_code == 200:
                    try:
                        blob_info = self._parse_blob_response(response.text)

                        if blob_info.status == "Completed" and blob_info.manifest.get("blobs"):
                            return blob_info.manifest["blobs"][0].get("blobLink"), None
                        elif blob_info.status != "Completed":
                            return None, f"报告生成未完成，当前状态: {blob_info.status}"
                        else:
                            return None, "响应中未找到有效的CSV下载链接"
                    except Exception as e:
                        return None, f"解析响应时出错: {str(e)}"

                time.sleep(self.POLLING_INTERVAL)
                retry_count += 1

            return None, f"超过最大重试次数({max_retries})，仍未获取到CSV下载链接"
        except requests.exceptions.RequestException as e:
            print(e)
            return None, f"请求异常: {str(e)}"
        except Exception as e:
            return None, f"处理请求时发生错误: {str(e)}"

    def _parse_blob_response(self, response_text: str) -> BlobInfo:
        """解析Blob响应"""
        try:
            data = json.loads(response_text)
            return BlobInfo(status=data.get("status", ""), manifest=data.get("manifest", {}))
        except json.JSONDecodeError:
            raise ValueError("无法解析JSON响应")
        except Exception as e:
            raise ValueError(f"解析Blob信息时出错: {str(e)}")

    def download_ri_csv(self, csv_url: str, token: Optional[str] = None) -> Tuple[Optional[bytes], Optional[str]]:
        """
        下载RI账单CSV文件
        :param csv_url: 从get_ri_csv_url获取的CSV下载URL
        :param token: 访问令牌(可选)
        :return: (csv_content, error) 元组
        """
        use_token = token if token else self._current_token
        if not use_token:
            return None, "未提供有效的访问令牌"
        try:
            response = self.session.get(csv_url)
            if response.status_code == 200:
                return response.content, None
            else:
                error_msg = f"下载CSV失败，状态码: {response.status_code}"
                try:
                    error_details = response.json()
                    error_msg += f", 详情: {error_details}"
                except:
                    pass
                return None, error_msg
        except requests.exceptions.RequestException as e:
            return None, f"请求异常: {str(e)}"
        except Exception as e:
            return None, f"处理请求时发生错误: {str(e)}"

    def get_ri_csv_as_json(self, location_url: str, token: Optional[str] = None, max_retries: int = 10):
        """
        获取RI账单CSV内容并转换为JSON格式
        :param location_url: 从get_ri_location获取的位置URL
        :param token: 访问令牌(可选)
        :param max_retries: 最大轮询次数(默认10次)
        :yield: (row_data, error) 元组，成功时为(dict, None)，失败时为(None, error_message)
        """
        csv_url, error = self.get_ri_csv_url(location_url, token, max_retries)
        if error:
            yield None, f"获取CSV下载URL失败: {error}"
            return
        if not csv_url:
            yield None, "未能获取有效的CSV下载URL"
            return

        csv_content, error = self.download_ri_csv(csv_url, token)
        if error:
            yield None, f"下载CSV内容失败: {error}"
            return
        if not csv_content:
            yield None, "下载的CSV内容为空"
            return

        try:
            csv_str = csv_content.decode("utf-8-sig")
            csv_reader = csv.DictReader(csv_str.splitlines())
            for row in csv_reader:
                yield BillingRecord.model_validate(row), None
        except UnicodeDecodeError as e:
            yield None, f"CSV解码失败: {str(e)}"
        except Exception as e:
            yield None, f"CSV转换为JSON时出错: {str(e)}"

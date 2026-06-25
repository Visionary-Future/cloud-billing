# Copyright 2025 Visionary Future
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Dict, Optional


class APIError(Exception):
    """自定义API请求异常基类"""

    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        """
        Args:
            message: 错误描述
            status_code: HTTP状态码（如果有）
            response_data: API返回的原始数据（如果有）
        """
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class InvalidResponseError(APIError):
    """响应数据格式无效异常"""

    pass


class RequestFailedError(APIError):
    """API请求失败异常"""

    pass

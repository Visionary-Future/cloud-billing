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

from typing import Dict


def parse_aliyun_tag(tag: str) -> Dict[str, str]:
    """
    解析阿里云资源标签字符串为字典格式

    支持两种格式：
    1. 'key:Environment value:PROD; key:Role value:App; key:Application value:xxxx'
    2. 'key:Environment value:Prod; key:Application_Owner value:xxxxx;'

    Args:
        tag: 原始标签字符串

    Returns:
        解析后的标签字典，如 {'Environment': 'PROD', 'Role': 'App'}

    Raises:
        ValueError: 当标签格式不符合预期时
    """
    if not tag or not tag.strip():
        return {}

    normalized_tag = (
        tag.strip().replace("; ", ";").replace(";", "; ").rstrip("; ")  # 先统一去掉已有空格  # 然后统一添加标准分隔符  # 去除末尾可能多余的分隔符
    )

    result = {}
    for pair in normalized_tag.split("; "):
        if not pair.strip():
            continue

        try:
            if "value:" not in pair:
                raise ValueError(f"Invalid tag pair format, missing 'value:': {pair}")

            key_part, value = pair.split("value:", 1)
            key = key_part.replace("key:", "").strip()

            if not key:
                raise ValueError(f"Empty key in tag pair: {pair}")

            result[key] = value.strip()

        except ValueError as e:
            raise ValueError(f"Failed to parse tag pair '{pair}'. Original error: {str(e)}") from e

    return result

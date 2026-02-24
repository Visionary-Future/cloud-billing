from typing import Dict


def parse_aliyun_tag(tag: str) -> Dict[str, str]:
    """Parse an Alibaba Cloud resource tag string into a dictionary.

    Supports two formats:
    1. 'key:Environment value:PROD; key:Role value:App; key:Application value:xxxx'
    2. 'key:Environment value:Prod; key:Application_Owner value:xxxxx;'

    Args:
        tag: Raw tag string.

    Returns:
        Parsed tag dictionary, e.g. {'Environment': 'PROD', 'Role': 'App'}.

    Raises:
        ValueError: When the tag format does not match the expected pattern.
    """
    if not tag or not tag.strip():
        return {}

    normalized_tag = (
        tag.strip()
        .replace("; ", ";")
        .replace(";", "; ")
        .rstrip("; ")  # normalize separators and strip trailing delimiter
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

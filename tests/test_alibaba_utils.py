import pytest

from cloud_billing.alibaba_cloud.utils import parse_aliyun_tag


class TestParseAliyunTag:
    """Test cases for parse_aliyun_tag function"""

    def test_empty_input(self):
        """Test empty and None inputs"""
        assert parse_aliyun_tag("") == {}
        assert parse_aliyun_tag("   ") == {}
        assert parse_aliyun_tag(None) == {}

    def test_mdlz_format(self):
        """Test MDLZ format parsing"""
        tag = "key:Environment value:PROD; key:Role value:App; key:Application value:LSZL|APP2|"
        expected = {"Environment": "PROD", "Role": "App", "Application": "LSZL|APP2|"}
        assert parse_aliyun_tag(tag) == expected

    def test_carlsberg_format(self):
        """Test Carlsberg format parsing"""
        tag = "key:Environment value:Prod; key:Application_Owner value:Vanessa.WC.Jiang@carlsberg.asia;"
        expected = {"Environment": "Prod", "Application_Owner": "Vanessa.WC.Jiang@carlsberg.asia"}
        assert parse_aliyun_tag(tag) == expected

    def test_single_tag_pair(self):
        """Test single tag pair"""
        tag = "key:Environment value:Production"
        expected = {"Environment": "Production"}
        assert parse_aliyun_tag(tag) == expected

    def test_whitespace_variations(self):
        """Test different whitespace scenarios"""
        # No spaces around semicolon
        tag1 = "key:Env value:Prod;key:Role value:App"
        expected1 = {"Env": "Prod", "Role": "App"}
        assert parse_aliyun_tag(tag1) == expected1

        # Multiple spaces
        tag2 = "key:Env value:Prod  ;  key:Role value:App"
        expected2 = {"Env": "Prod", "Role": "App"}
        assert parse_aliyun_tag(tag2) == expected2

        # Trailing semicolon
        tag3 = "key:Env value:Prod; key:Role value:App;"
        expected3 = {"Env": "Prod", "Role": "App"}
        assert parse_aliyun_tag(tag3) == expected3

    def test_values_with_special_characters(self):
        """Test values containing special characters"""
        tag = "key:Email value:user@domain.com; key:Path value:/home/user; key:Version value:v1.2.3"
        expected = {"Email": "user@domain.com", "Path": "/home/user", "Version": "v1.2.3"}
        assert parse_aliyun_tag(tag) == expected

    def test_values_with_colons(self):
        """Test values that contain colons"""
        tag = "key:URL value:https://example.com:8080; key:Time value:12:30:45"
        expected = {"URL": "https://example.com:8080", "Time": "12:30:45"}
        assert parse_aliyun_tag(tag) == expected

    def test_empty_values(self):
        """Test tags with empty values"""
        tag = "key:Environment value:; key:Role value:App"
        expected = {"Environment": "", "Role": "App"}
        assert parse_aliyun_tag(tag) == expected

    def test_keys_with_special_characters(self):
        """Test keys containing underscores and other characters"""
        tag = "key:Application_Owner value:John; key:Cost-Center value:IT"
        expected = {"Application_Owner": "John", "Cost-Center": "IT"}
        assert parse_aliyun_tag(tag) == expected

    def test_invalid_format_missing_value(self):
        """Test invalid format - missing 'value:' keyword"""
        tag = "key:Environment PROD; key:Role value:App"
        with pytest.raises(ValueError, match="Invalid tag pair format, missing 'value:'"):
            parse_aliyun_tag(tag)

    def test_invalid_format_empty_key(self):
        """Test invalid format - empty key"""
        tag = "key: value:PROD; key:Role value:App"
        with pytest.raises(ValueError, match="Empty key in tag pair"):
            parse_aliyun_tag(tag)

    def test_missing_key_prefix_still_works(self):
        """Test that missing 'key:' prefix still works (flexible parsing)"""
        tag = "Environment value:PROD; key:Role value:App"
        expected = {"Environment": "PROD", "Role": "App"}
        assert parse_aliyun_tag(tag) == expected

    def test_invalid_format_malformed_pair(self):
        """Test various malformed tag pairs"""
        # No colon separator
        tag1 = "keyEnvironment valuePROD"
        with pytest.raises(ValueError, match="Invalid tag pair format, missing 'value:'"):
            parse_aliyun_tag(tag1)

        # Only key part
        tag2 = "key:Environment"
        with pytest.raises(ValueError, match="Invalid tag pair format, missing 'value:'"):
            parse_aliyun_tag(tag2)

    def test_mixed_valid_invalid_pairs(self):
        """Test string with mixed valid and invalid pairs"""
        tag = "key:Environment value:PROD; invalid_pair; key:Role value:App"
        with pytest.raises(ValueError, match="Failed to parse tag pair 'invalid_pair'"):
            parse_aliyun_tag(tag)

    def test_edge_case_only_separators(self):
        """Test edge case with only separators"""
        tag = "; ; ;"
        assert parse_aliyun_tag(tag) == {}

    def test_unicode_characters(self):
        """Test with unicode characters in keys and values"""
        tag = "key:环境 value:生产; key:Role value:应用"
        expected = {"环境": "生产", "Role": "应用"}
        assert parse_aliyun_tag(tag) == expected

    def test_very_long_values(self):
        """Test with very long values"""
        long_value = "a" * 1000
        tag = f"key:Environment value:{long_value}; key:Role value:App"
        expected = {"Environment": long_value, "Role": "App"}
        assert parse_aliyun_tag(tag) == expected

    def test_case_sensitivity(self):
        """Test case sensitivity in keys and values"""
        tag = "key:environment value:PROD; key:Environment value:prod"
        expected = {"environment": "PROD", "Environment": "prod"}
        assert parse_aliyun_tag(tag) == expected

    @pytest.mark.parametrize(
        "tag_input,expected",
        [
            ("key:A value:1", {"A": "1"}),
            ("key:A value:1; key:B value:2", {"A": "1", "B": "2"}),
            ("key:A value:1; key:B value:2; key:C value:3", {"A": "1", "B": "2", "C": "3"}),
        ],
    )
    def test_parametrized_valid_cases(self, tag_input, expected):
        """Parametrized test for various valid inputs"""
        assert parse_aliyun_tag(tag_input) == expected

    @pytest.mark.parametrize(
        "invalid_tag",
        [
            "key:A value",  # Missing value
            "key: value:1",  # Empty key
            "key:A:1",  # Wrong format
        ],
    )
    def test_parametrized_invalid_cases(self, invalid_tag):
        """Parametrized test for various invalid inputs"""
        with pytest.raises(ValueError):
            parse_aliyun_tag(invalid_tag)

    @pytest.mark.parametrize(
        "valid_tag,expected",
        [
            ("", {}),  # Empty string returns empty dict
            ("A value:1", {"A": "1"}),  # Missing key prefix still works
        ],
    )
    def test_parametrized_flexible_cases(self, valid_tag, expected):
        """Test cases that work due to flexible parsing"""
        assert parse_aliyun_tag(valid_tag) == expected

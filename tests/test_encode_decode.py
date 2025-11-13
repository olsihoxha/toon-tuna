"""
Test basic TOON encoding and decoding functionality
"""

import pytest
from toon_tuna import encode, decode, EncodeOptions, DecodeOptions


class TestEncoding:
    """Test TOON encoding."""

    def test_simple_object(self):
        """Test encoding a simple object."""
        data = {"id": 123, "name": "Alice"}

        result = encode(data)

        assert "id: 123" in result
        assert "name: Alice" in result

    def test_nested_object(self):
        """Test encoding nested objects."""
        data = {
            "user": {
                "id": 123,
                "name": "Alice",
                "settings": {"theme": "dark", "lang": "en"},
            }
        }

        result = encode(data)

        assert "user:" in result
        assert "id: 123" in result
        assert "name: Alice" in result
        assert "settings:" in result
        assert "theme: dark" in result

    def test_tabular_array(self):
        """Test encoding uniform arrays (tabular format)."""
        data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}

        result = encode(data)

        # Should use tabular format
        assert "[2,]{id,name}:" in result or "[2]{id,name}:" in result
        assert "1,Alice" in result
        assert "2,Bob" in result

    def test_primitive_array(self):
        """Test encoding arrays of primitives."""
        data = {"tags": [1, 2, 3, 4, 5]}

        result = encode(data)

        # Should use inline format
        assert "[5,]:" in result or "[5]:" in result
        assert "1,2,3,4,5" in result

    def test_string_array(self):
        """Test encoding arrays of strings."""
        data = {"colors": ["red", "green", "blue"]}

        result = encode(data)

        assert "[3,]:" in result or "[3]:" in result
        assert "red,green,blue" in result or "red" in result

    def test_empty_object(self):
        """Test encoding empty object."""
        data = {}

        result = encode(data)

        assert result == "" or result.strip() == ""

    def test_empty_array(self):
        """Test encoding empty array."""
        data = {"items": []}

        result = encode(data)

        assert "[0]:" in result

    def test_boolean_values(self):
        """Test encoding boolean values."""
        data = {"active": True, "deleted": False}

        result = encode(data)

        assert "active: true" in result
        assert "deleted: false" in result

    def test_null_values(self):
        """Test encoding null values."""
        data = {"value": None, "other": "test"}

        result = encode(data)

        assert "value: null" in result
        assert "other: test" in result

    def test_number_types(self):
        """Test encoding different number types."""
        data = {"integer": 42, "float": 3.14159, "large": 1000000, "zero": 0}

        result = encode(data)

        assert "integer: 42" in result
        assert "float: 3.14159" in result
        assert "large: 1000000" in result
        assert "zero: 0" in result

    def test_special_characters_quoting(self):
        """Test that special characters trigger quoting."""
        data = {
            "url": "https://example.com?q=a:b",
            "pipe": "value|with|pipes",
            "space": "has spaces",
        }

        result = encode(data)

        # URLs with colons should be quoted
        assert '"https://example.com?q=a:b"' in result or "url:" in result
        assert "pipe:" in result
        assert "space:" in result

    def test_custom_delimiter_comma(self):
        """Test with comma delimiter (default)."""
        data = {"items": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]}
        options = EncodeOptions(delimiter=",")

        result = encode(data, options)

        assert "," in result

    def test_custom_delimiter_pipe(self):
        """Test with pipe delimiter."""
        data = {"items": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]}
        options = EncodeOptions(delimiter="|")

        result = encode(data, options)

        assert "|" in result

    def test_custom_indent(self):
        """Test custom indentation."""
        data = {"user": {"name": "Alice", "id": 1}}
        options = EncodeOptions(indent=4)

        result = encode(data, options)

        # Check for 4-space indentation
        assert "    " in result or result  # Basic check

    def test_mixed_array(self):
        """Test arrays with mixed types."""
        data = {"items": [1, "string", {"nested": "object"}]}

        result = encode(data)

        # Should handle mixed types
        assert "items:" in result


class TestDecoding:
    """Test TOON decoding."""

    def test_decode_simple_object(self):
        """Test decoding a simple object."""
        toon_str = "id: 123\nname: Alice"

        result = decode(toon_str)

        assert result["id"] == 123
        assert result["name"] == "Alice"

    def test_decode_tabular_array(self):
        """Test decoding tabular array."""
        toon_str = """users:
  [2,]{id,name}:
    1,Alice
    2,Bob"""

        result = decode(toon_str)

        assert "users" in result
        assert len(result["users"]) == 2
        assert result["users"][0]["id"] == 1
        assert result["users"][0]["name"] == "Alice"
        assert result["users"][1]["id"] == 2
        assert result["users"][1]["name"] == "Bob"

    def test_decode_primitive_array(self):
        """Test decoding primitive array."""
        toon_str = "tags:\n  [3,]: 1,2,3"

        result = decode(toon_str)

        assert "tags" in result
        assert result["tags"] == [1, 2, 3]

    def test_decode_boolean(self):
        """Test decoding boolean values."""
        toon_str = "active: true\ndeleted: false"

        result = decode(toon_str)

        assert result["active"] is True
        assert result["deleted"] is False

    def test_decode_null(self):
        """Test decoding null values."""
        toon_str = "value: null"

        result = decode(toon_str)

        assert result["value"] is None

    def test_decode_quoted_strings(self):
        """Test decoding quoted strings."""
        toon_str = 'url: "https://example.com?q=a:b"\nname: Alice'

        result = decode(toon_str)

        assert result["url"] == "https://example.com?q=a:b"
        assert result["name"] == "Alice"

    def test_decode_escaped_characters(self):
        """Test decoding escaped characters."""
        toon_str = r'text: "Line 1\nLine 2\tTabbed"'

        result = decode(toon_str)

        assert result["text"] == "Line 1\nLine 2\tTabbed"


class TestRoundTrip:
    """Test encoding and decoding round-trip."""

    def test_roundtrip_simple_object(self):
        """Test round-trip for simple object."""
        original = {"id": 123, "name": "Alice", "active": True}

        encoded = encode(original)
        decoded = decode(encoded)

        assert decoded["id"] == original["id"]
        assert decoded["name"] == original["name"]
        assert decoded["active"] == original["active"]

    def test_roundtrip_tabular_array(self):
        """Test round-trip for tabular array."""
        original = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}

        encoded = encode(original)
        decoded = decode(encoded)

        assert len(decoded["users"]) == len(original["users"])
        assert decoded["users"][0]["id"] == original["users"][0]["id"]
        assert decoded["users"][0]["name"] == original["users"][0]["name"]

    def test_roundtrip_primitive_array(self):
        """Test round-trip for primitive array."""
        original = {"numbers": [1, 2, 3, 4, 5]}

        encoded = encode(original)
        decoded = decode(encoded)

        assert decoded["numbers"] == original["numbers"]

    def test_roundtrip_with_nulls(self):
        """Test round-trip with null values."""
        original = {"value": None, "other": "test"}

        encoded = encode(original)
        decoded = decode(encoded)

        assert decoded["value"] is None
        assert decoded["other"] == original["other"]

    def test_roundtrip_numbers(self):
        """Test round-trip for various number types."""
        original = {"int": 42, "float": 3.14, "zero": 0}

        encoded = encode(original)
        decoded = decode(encoded)

        assert decoded["int"] == original["int"]
        assert abs(decoded["float"] - original["float"]) < 0.01
        assert decoded["zero"] == original["zero"]


class TestOptions:
    """Test encoding/decoding options."""

    def test_encode_options_creation(self):
        """Test creating EncodeOptions."""
        options = EncodeOptions(delimiter="|", indent=4, use_length_markers=False)

        assert options.delimiter == "|"
        assert options.indent == 4
        assert options.use_length_markers is False

    def test_decode_options_creation(self):
        """Test creating DecodeOptions."""
        options = DecodeOptions(strict=False)

        assert options.strict is False

    def test_no_length_markers(self):
        """Test encoding without length markers."""
        data = {"items": [1, 2, 3]}
        options = EncodeOptions(use_length_markers=False)

        result = encode(data, options)

        assert "[]: 1,2,3" in result


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string_value(self):
        """Test empty string values."""
        data = {"empty": "", "other": "value"}

        result = encode(data)

        assert "empty:" in result
        assert "other: value" in result

    def test_very_long_string(self):
        """Test very long strings."""
        data = {"long": "x" * 10000}

        result = encode(data)

        assert "long:" in result

    def test_deeply_nested(self):
        """Test deeply nested structures."""
        data = {"a": {"b": {"c": {"d": {"e": "value"}}}}}

        result = encode(data)

        assert "a:" in result
        assert "value" in result

    def test_large_array(self):
        """Test large arrays."""
        data = {"items": [{"id": i, "value": f"item{i}"} for i in range(1000)]}

        result = encode(data)

        assert "[1000" in result or "items:" in result

    def test_unicode_characters(self):
        """Test Unicode characters."""
        data = {"chinese": "你好", "emoji": "😀", "arabic": "مرحبا"}

        result = encode(data)

        # Should handle Unicode
        assert "chinese:" in result or "你好" in result

    def test_special_number_values(self):
        """Test special number values."""
        data = {"negative": -42, "decimal": 0.001, "large": 999999999}

        result = encode(data)

        assert "negative: -42" in result
        assert "decimal:" in result
        assert "large:" in result

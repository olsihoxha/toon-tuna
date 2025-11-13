"""
Test the smart format selection (encode_optimal) - THE MOST IMPORTANT FEATURE
"""

import pytest
from toon_tuna import encode_optimal, estimate_savings


class TestOptimalSelection:
    """Test that encode_optimal chooses the right format."""

    def test_uniform_arrays_prefer_toon(self):
        """Large uniform arrays should prefer TOON format."""
        data = {"users": [{"id": i, "name": f"User{i}", "email": f"user{i}@example.com"} for i in range(100)]}

        result = encode_optimal(data)

        assert result["format"] == "toon", "Should prefer TOON for large uniform arrays"
        assert result["savings_percent"] > 10, "Should save >10% tokens"
        assert result["toon_tokens"] < result["json_tokens"], "TOON should use fewer tokens"

    def test_small_objects_prefer_json(self):
        """Small simple objects might prefer JSON."""
        data = {"id": 1, "name": "Alice", "active": True}

        result = encode_optimal(data)

        # Small objects could go either way, but should make a valid decision
        assert result["format"] in ["toon", "json"]
        assert "toon_tokens" in result
        assert "json_tokens" in result

    def test_nested_objects(self):
        """Test deeply nested structures."""
        data = {
            "a": {
                "b": {
                    "c": {
                        "d": "value",
                        "e": [1, 2, 3]
                    }
                }
            }
        }

        result = encode_optimal(data)

        assert result["format"] in ["toon", "json"]
        assert isinstance(result["savings_percent"], (int, float))

    def test_optimal_is_actually_better(self):
        """Ensure the chosen format actually uses fewer or equal tokens."""
        test_cases = [
            {"users": [{"id": i, "name": f"User{i}"} for i in range(50)]},
            {"tags": ["python", "rust", "json", "toon"]},
            {"config": {"timeout": 30, "retries": 3, "debug": False}},
            [{"id": 1, "value": "a"}, {"id": 2, "value": "b"}],
        ]

        for data in test_cases:
            result = encode_optimal(data)

            if result["format"] == "toon":
                assert (
                    result["toon_tokens"] <= result["json_tokens"]
                ), f"TOON was chosen but uses more tokens for {data}"
            else:
                assert (
                    result["json_tokens"] <= result["toon_tokens"]
                ), f"JSON was chosen but uses more tokens for {data}"

    def test_large_uniform_array_significant_savings(self):
        """Large uniform arrays should show significant savings with TOON."""
        data = {
            "products": [
                {"sku": f"SKU{i:04d}", "price": i * 10.99, "qty": i % 100}
                for i in range(200)
            ]
        }

        result = encode_optimal(data)

        assert result["format"] == "toon"
        assert result["savings_percent"] > 20, "Should save >20% tokens for large dataset"

    def test_heterogeneous_array(self):
        """Mixed-type arrays should be handled correctly."""
        data = {
            "items": [
                1,
                "string",
                {"nested": "object"},
                [1, 2, 3],
                True,
                None,
            ]
        }

        result = encode_optimal(data)

        # Should make a valid decision
        assert result["format"] in ["toon", "json"]

    def test_primitive_arrays(self):
        """Arrays of primitives."""
        data = {
            "numbers": list(range(100)),
            "strings": [f"item{i}" for i in range(50)],
            "booleans": [True, False] * 25,
        }

        result = encode_optimal(data)

        assert result["format"] in ["toon", "json"]
        assert result["toon_tokens"] > 0
        assert result["json_tokens"] > 0

    def test_estimate_savings(self):
        """Test estimate_savings function."""
        data = {"users": [{"id": i, "name": f"User{i}"} for i in range(100)]}

        result = estimate_savings(data)

        assert "json_tokens" in result
        assert "toon_tokens" in result
        assert "savings" in result
        assert "savings_percent" in result
        assert "recommended_format" in result
        assert result["recommended_format"] in ["toon", "json"]
        assert result["savings"] == abs(result["json_tokens"] - result["toon_tokens"])

    def test_empty_structures(self):
        """Test empty data structures."""
        test_cases = [
            {},
            [],
            {"empty_list": [], "empty_obj": {}},
        ]

        for data in test_cases:
            result = encode_optimal(data)
            assert result["format"] in ["toon", "json"]

    def test_special_characters(self):
        """Test data with special characters."""
        data = {
            "urls": [
                {"url": "https://example.com?q=a:b", "title": "Example"},
                {"url": "https://test.com/path|with|pipes", "title": "Test"},
            ]
        }

        result = encode_optimal(data)

        assert result["format"] in ["toon", "json"]
        # Should not crash or error

    def test_unicode_data(self):
        """Test Unicode characters."""
        data = {
            "messages": [
                {"user": "Alice", "text": "Hello 世界!"},
                {"user": "Bob", "text": "Привет мир!"},
                {"user": "Carol", "text": "مرحبا بالعالم"},
            ]
        }

        result = encode_optimal(data)

        assert result["format"] in ["toon", "json"]
        assert result["toon_tokens"] > 0

    def test_recommendation_reason(self):
        """Test that recommendation reasons are provided."""
        test_cases = [
            {"users": [{"id": i} for i in range(100)]},
            {"simple": "value"},
            {"nested": {"deep": {"structure": "here"}}},
        ]

        for data in test_cases:
            result = encode_optimal(data)
            assert "recommendation_reason" in result
            assert isinstance(result["recommendation_reason"], str)
            assert len(result["recommendation_reason"]) > 0

    def test_different_tokenizers(self):
        """Test with different tokenizers."""
        data = {"users": [{"id": i, "name": f"User{i}"} for i in range(50)]}

        tokenizers = ["cl100k_base", "p50k_base", "r50k_base"]

        for tokenizer in tokenizers:
            try:
                result = encode_optimal(data, tokenizer=tokenizer)
                assert result["format"] in ["toon", "json"]
                assert result["toon_tokens"] > 0
                assert result["json_tokens"] > 0
            except ValueError:
                # Some tokenizers might not be available
                pass

    def test_numbers_formatting(self):
        """Test that numbers are formatted correctly."""
        data = {
            "values": [
                {"int": 42, "float": 3.14, "large": 1000000},
                {"int": 0, "float": 0.5, "large": 999999},
            ]
        }

        result = encode_optimal(data)

        # Should handle all number types
        assert result["format"] in ["toon", "json"]

    def test_boolean_and_null(self):
        """Test boolean and null values."""
        data = {
            "items": [
                {"active": True, "value": None},
                {"active": False, "value": None},
            ]
        }

        result = encode_optimal(data)

        assert result["format"] in ["toon", "json"]

    def test_savings_calculation(self):
        """Verify savings percentage calculation is correct."""
        data = {"users": [{"id": i} for i in range(100)]}

        result = encode_optimal(data)

        # Manually verify calculation
        expected_savings = abs(result["json_tokens"] - result["toon_tokens"]) / max(
            result["json_tokens"], result["toon_tokens"]
        ) * 100

        assert abs(result["savings_percent"] - expected_savings) < 0.1

    def test_consistent_results(self):
        """Ensure encode_optimal returns consistent results."""
        data = {"users": [{"id": i, "name": f"User{i}"} for i in range(50)]}

        result1 = encode_optimal(data)
        result2 = encode_optimal(data)

        assert result1["format"] == result2["format"]
        assert result1["toon_tokens"] == result2["toon_tokens"]
        assert result1["json_tokens"] == result2["json_tokens"]
        assert result1["data"] == result2["data"]

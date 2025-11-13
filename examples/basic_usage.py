"""
Basic usage examples for toon-tuna

This demonstrates the core functionality of toon-tuna:
- encode_optimal() - Smart format selection
- encode() - Manual TOON encoding
- decode() - TOON to Python
- estimate_savings() - Calculate token savings
"""

from toon_tuna import encode, decode, encode_optimal, estimate_savings, EncodeOptions


def example_1_smart_optimization():
    """Example 1: Smart format selection (RECOMMENDED!)"""
    print("=" * 60)
    print("Example 1: Smart Format Selection")
    print("=" * 60)

    # Your data
    data = {
        "users": [
            {"id": i, "name": f"User{i}", "email": f"user{i}@example.com"}
            for i in range(100)
        ]
    }

    # Let toon-tuna choose the best format
    result = encode_optimal(data)

    print(f"Chosen format: {result['format']}")
    print(f"TOON tokens: {result['toon_tokens']}")
    print(f"JSON tokens: {result['json_tokens']}")
    print(f"Savings: {result['savings_percent']:.1f}%")
    print(f"Reason: {result['recommendation_reason']}")
    print()
    print("First 200 chars of optimized data:")
    print(result["data"][:200])
    print()


def example_2_manual_encoding():
    """Example 2: Manual TOON encoding"""
    print("=" * 60)
    print("Example 2: Manual TOON Encoding")
    print("=" * 60)

    data = {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Carol", "email": "carol@example.com"},
        ]
    }

    # Encode to TOON
    toon_str = encode(data)
    print("TOON format:")
    print(toon_str)
    print()

    # Decode back to Python
    decoded = decode(toon_str)
    print("Decoded back:")
    print(decoded)
    print()


def example_3_custom_options():
    """Example 3: Custom encoding options"""
    print("=" * 60)
    print("Example 3: Custom Encoding Options")
    print("=" * 60)

    data = {
        "products": [
            {"sku": "A1", "name": "Widget", "price": 9.99},
            {"sku": "B2", "name": "Gadget", "price": 19.99},
        ]
    }

    # Use pipe delimiter instead of comma
    options = EncodeOptions(delimiter="|", indent=4)
    toon_str = encode(data, options)

    print("TOON with pipe delimiter:")
    print(toon_str)
    print()


def example_4_estimate_savings():
    """Example 4: Estimate token savings"""
    print("=" * 60)
    print("Example 4: Estimate Token Savings")
    print("=" * 60)

    datasets = [
        ("Small object", {"id": 1, "name": "Alice"}),
        (
            "Medium array",
            {"users": [{"id": i, "name": f"User{i}"} for i in range(50)]},
        ),
        (
            "Large array",
            {"products": [{"sku": f"SKU{i}", "price": i * 10} for i in range(200)]},
        ),
    ]

    for name, data in datasets:
        result = estimate_savings(data)
        print(f"{name}:")
        print(f"  JSON tokens: {result['json_tokens']}")
        print(f"  TOON tokens: {result['toon_tokens']}")
        print(f"  Savings: {result['savings']} tokens ({result['savings_percent']:.1f}%)")
        print(f"  Recommended: {result['recommended_format'].upper()}")
        print()


def example_5_real_world_api_response():
    """Example 5: Real-world API response"""
    print("=" * 60)
    print("Example 5: Real-World API Response")
    print("=" * 60)

    # Simulate API response with pagination
    api_response = {
        "data": [
            {
                "user_id": i,
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "created_at": "2025-01-01T00:00:00Z",
                "is_active": True,
            }
            for i in range(100)
        ],
        "pagination": {"page": 1, "per_page": 100, "total": 1000},
    }

    result = encode_optimal(api_response)

    print(f"Format: {result['format']}")
    print(f"Token savings: {result['savings_percent']:.1f}%")
    print()

    # Calculate cost savings (GPT-4 pricing: $10/1M input tokens)
    tokens_saved_per_request = result["json_tokens"] - result["toon_tokens"]
    requests_per_day = 1000
    tokens_saved_per_day = tokens_saved_per_request * requests_per_day
    cost_saved_per_day = tokens_saved_per_day * (10 / 1_000_000)
    cost_saved_per_year = cost_saved_per_day * 365

    print(f"Cost Analysis (based on GPT-4 pricing):")
    print(f"  Tokens saved per request: {tokens_saved_per_request}")
    print(f"  Tokens saved per day (1000 requests): {tokens_saved_per_day:,}")
    print(f"  Cost saved per day: ${cost_saved_per_day:.2f}")
    print(f"  Cost saved per year: ${cost_saved_per_year:.2f}")
    print()


def example_6_nested_data():
    """Example 6: Nested data structures"""
    print("=" * 60)
    print("Example 6: Nested Data Structures")
    print("=" * 60)

    data = {
        "company": {
            "name": "Acme Corp",
            "employees": [
                {
                    "id": 1,
                    "name": "Alice",
                    "department": "Engineering",
                    "salary": 100000,
                },
                {"id": 2, "name": "Bob", "department": "Sales", "salary": 80000},
            ],
            "offices": [
                {"city": "NYC", "employees": 50},
                {"city": "SF", "employees": 30},
            ],
        }
    }

    result = encode_optimal(data)

    print(f"Format: {result['format']}")
    print(f"Savings: {result['savings_percent']:.1f}%")
    print()
    print("Encoded data:")
    print(result["data"])
    print()


if __name__ == "__main__":
    print("\n🐟 toon-tuna Examples\n")

    try:
        example_1_smart_optimization()
        example_2_manual_encoding()
        example_3_custom_options()
        example_4_estimate_savings()
        example_5_real_world_api_response()
        example_6_nested_data()

        print("=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)

    except ImportError as e:
        print(f"❌ Error: {e}")
        print("\nPlease install toon-tuna first:")
        print("  pip install toon-tuna")
        print("\nOr for development:")
        print("  maturin develop")

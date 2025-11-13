"""
Toon Tuna: Smart TOON/JSON Optimizer for LLMs

High-performance library that intelligently chooses between TOON format
and minified JSON based on token efficiency for LLM contexts.
"""

import json
from typing import Any, Dict, Optional

try:
    import tiktoken
except ImportError:
    raise ImportError(
        "tiktoken is required for optimal encoding. Install with: pip install tiktoken"
    )

from toon_tuna._toon_tuna import (
    encode as _encode,
    decode_toon as _decode,
    EncodeOptions,
    DecodeOptions,
)

__version__ = "0.1.0"
__all__ = [
    "encode",
    "decode",
    "encode_optimal",
    "estimate_savings",
    "EncodeOptions",
    "DecodeOptions",
]


def encode(data: Any, options: Optional[EncodeOptions] = None) -> str:
    """
    Encode Python data to TOON format.

    Args:
        data: Python data structure (dict, list, primitives)
        options: Optional encoding options (delimiter, indent, etc.)

    Returns:
        TOON-formatted string

    Examples:
        >>> encode({"id": 1, "name": "Alice"})
        'id: 1\\nname: Alice'

        >>> encode({"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]})
        'users:\\n  [2,]{id,name}:\\n    1,Alice\\n    2,Bob'
    """
    return _encode(data, options)


def decode(toon_str: str, options: Optional[DecodeOptions] = None) -> Any:
    """
    Decode TOON format to Python data.

    Args:
        toon_str: TOON-formatted string
        options: Optional decoding options

    Returns:
        Python data structure

    Examples:
        >>> decode("id: 1\\nname: Alice")
        {'id': 1, 'name': 'Alice'}
    """
    return _decode(toon_str, options)


def encode_optimal(
    data: Any,
    target: str = "llm",
    tokenizer: str = "cl100k_base",
    options: Optional[EncodeOptions] = None,
) -> Dict[str, Any]:
    """
    Smart format selection: encode data using the most token-efficient format.

    This is the CORE FEATURE of toon-tuna. It compares TOON and JSON encodings
    and returns whichever uses fewer tokens for LLM contexts.

    Args:
        data: Python data structure to encode
        target: Target use case ('llm' for language models)
        tokenizer: Tokenizer to use for counting (default: cl100k_base for GPT-4)
        options: Optional TOON encoding options

    Returns:
        Dictionary with:
            - format: 'toon' or 'json' (the chosen format)
            - data: The encoded string in the optimal format
            - toon_tokens: Token count for TOON encoding
            - json_tokens: Token count for JSON encoding
            - savings_percent: Percentage of tokens saved
            - recommendation_reason: Human-readable explanation

    Examples:
        >>> result = encode_optimal([{"id": i, "name": f"User{i}"} for i in range(100)])
        >>> print(f"Format: {result['format']}, Savings: {result['savings_percent']:.1f}%")
        Format: toon, Savings: 42.3%

        >>> # Use the optimal encoding for LLM
        >>> prompt = f"Analyze this data:\\n{result['data']}"
    """
    # Encode in both formats
    toon_str = encode(data, options)
    json_str = json.dumps(data, separators=(",", ":"), ensure_ascii=False)

    # Count tokens using tiktoken
    try:
        enc = tiktoken.get_encoding(tokenizer)
    except Exception as e:
        raise ValueError(f"Invalid tokenizer '{tokenizer}': {e}")

    toon_tokens = len(enc.encode(toon_str))
    json_tokens = len(enc.encode(json_str))

    # Calculate savings percentage
    if json_tokens > 0:
        savings = (json_tokens - toon_tokens) / json_tokens * 100
    else:
        savings = 0.0

    # Decision logic
    format_choice = None
    data_str = None
    reason = ""

    if savings > 5:
        # TOON saves >5% tokens
        format_choice = "toon"
        data_str = toon_str
        reason = _analyze_toon_advantage(data)
    elif savings < -5:
        # JSON saves >5% tokens
        format_choice = "json"
        data_str = json_str
        savings = -savings
        reason = _analyze_json_advantage(data)
    else:
        # Similar token counts (within ±5%)
        # Prefer TOON for uniform arrays, JSON otherwise
        if _has_uniform_arrays(data):
            format_choice = "toon"
            data_str = toon_str
            reason = "Similar token counts, preferring TOON for uniform arrays"
        else:
            format_choice = "json"
            data_str = json_str
            reason = "Similar token counts, preferring JSON for irregular structure"
        savings = abs(savings)

    return {
        "format": format_choice,
        "data": data_str,
        "toon_tokens": toon_tokens,
        "json_tokens": json_tokens,
        "savings_percent": savings,
        "recommendation_reason": reason,
    }


def estimate_savings(
    data: Any, tokenizer: str = "cl100k_base", options: Optional[EncodeOptions] = None
) -> Dict[str, Any]:
    """
    Calculate potential token savings between TOON and JSON formats.

    Args:
        data: Python data structure
        tokenizer: Tokenizer to use for counting
        options: Optional TOON encoding options

    Returns:
        Dictionary with token counts and savings metrics

    Examples:
        >>> savings = estimate_savings({"users": [{"id": i} for i in range(100)]})
        >>> print(f"TOON: {savings['toon_tokens']}, JSON: {savings['json_tokens']}")
        >>> print(f"Savings: {savings['savings']} tokens ({savings['savings_percent']:.1f}%)")
    """
    result = encode_optimal(data, tokenizer=tokenizer, options=options)

    return {
        "json_tokens": result["json_tokens"],
        "toon_tokens": result["toon_tokens"],
        "savings": abs(result["json_tokens"] - result["toon_tokens"]),
        "savings_percent": result["savings_percent"],
        "recommended_format": result["format"],
    }


def _has_uniform_arrays(data: Any) -> bool:
    """Check if data contains uniform arrays (arrays of objects with same keys)."""
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list) and len(value) > 0:
                if all(isinstance(item, dict) for item in value):
                    # Check if all dicts have same keys
                    if len(value) > 0:
                        first_keys = set(value[0].keys())
                        if all(set(item.keys()) == first_keys for item in value):
                            # Check if all values are primitives
                            all_primitives = all(
                                not isinstance(v, (dict, list))
                                for item in value
                                for v in item.values()
                            )
                            if all_primitives:
                                return True
    elif isinstance(data, list) and len(data) > 0:
        if all(isinstance(item, dict) for item in data):
            first_keys = set(data[0].keys())
            if all(set(item.keys()) == first_keys for item in data):
                all_primitives = all(
                    not isinstance(v, (dict, list)) for item in data for v in item.values()
                )
                if all_primitives:
                    return True

    return False


def _analyze_toon_advantage(data: Any) -> str:
    """Analyze why TOON format is advantageous for this data."""
    if isinstance(data, dict):
        # Count uniform arrays
        uniform_arrays = 0
        total_items = 0

        for value in data.values():
            if isinstance(value, list) and len(value) > 1:
                if all(isinstance(item, dict) for item in value):
                    first_keys = set(value[0].keys())
                    if all(set(item.keys()) == first_keys for item in value):
                        uniform_arrays += 1
                        total_items += len(value)

        if uniform_arrays > 0:
            return f"Uniform array structure with {total_items} items in {uniform_arrays} array(s)"

    if isinstance(data, list) and len(data) > 1:
        if all(isinstance(item, dict) for item in data):
            first_keys = set(data[0].keys())
            if all(set(item.keys()) == first_keys for item in data):
                return f"Uniform array with {len(data)} items"

    return "TOON format more efficient for this structure"


def _analyze_json_advantage(data: Any) -> str:
    """Analyze why JSON format is advantageous for this data."""
    if isinstance(data, dict):
        # Check for deeply nested structures
        max_depth = _get_max_depth(data)
        if max_depth > 3:
            return f"Deeply nested structure (depth {max_depth})"

        # Check for small objects
        if len(data) <= 3:
            return "Small object with few fields"

    if isinstance(data, list):
        # Check for heterogeneous arrays
        types = set(type(item).__name__ for item in data)
        if len(types) > 1:
            return "Heterogeneous array with mixed types"

        # Check for small arrays
        if len(data) <= 3:
            return "Small array"

    return "JSON format more efficient for this structure"


def _get_max_depth(data: Any, current_depth: int = 0) -> int:
    """Calculate maximum nesting depth of data structure."""
    if isinstance(data, dict):
        if not data:
            return current_depth
        return max(_get_max_depth(v, current_depth + 1) for v in data.values())
    elif isinstance(data, list):
        if not data:
            return current_depth
        return max(_get_max_depth(item, current_depth + 1) for item in data)
    else:
        return current_depth

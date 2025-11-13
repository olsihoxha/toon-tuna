# 🚀 Quick Start Guide

Get started with toon-tuna in 5 minutes!

## Installation

### Option 1: From PyPI (when published)

```bash
pip install toon-tuna
```

### Option 2: From Source

```bash
# Prerequisites: Python 3.8+ and Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Clone and install
git clone https://github.com/olsihoxha/toon-tuna.git
cd toon-tuna
chmod +x setup.sh
./setup.sh
```

## Your First Example

```python
from toon_tuna import encode_optimal

# Your data
data = {
    "users": [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
        {"id": 3, "name": "Carol", "email": "carol@example.com"},
    ]
}

# Smart optimization - chooses best format
result = encode_optimal(data)

print(f"Format: {result['format']}")
print(f"Savings: {result['savings_percent']:.1f}%")
print(f"\nOptimized data:\n{result['data']}")
```

**Output:**
```
Format: toon
Savings: 38.2%

Optimized data:
users:
  [3,]{id,name,email}:
    1,Alice,alice@example.com
    2,Bob,bob@example.com
    3,Carol,carol@example.com
```

## CLI Quick Start

```bash
# Smart optimization
echo '{"users":[{"id":1,"name":"Alice"}]}' | tuna optimize

# Encode to TOON
tuna encode data.json -o output.toon

# Decode to JSON
tuna decode output.toon -o data.json

# Estimate savings
tuna estimate data.json
```

## Common Use Cases

### 1. Optimizing LLM Prompts

```python
from toon_tuna import encode_optimal

# Your structured data
api_data = fetch_api_data()  # Returns list of dicts

# Optimize for LLM
result = encode_optimal(api_data)

# Use in prompt
prompt = f"""
Analyze the following user data and provide insights:

{result['data']}

What trends do you notice?
"""

# Send to LLM (saves tokens = saves money!)
response = llm.complete(prompt)
```

### 2. Database Query Results

```python
from toon_tuna import encode_optimal
import psycopg2

# Fetch data
cursor.execute("SELECT * FROM users LIMIT 1000")
users = [dict(row) for row in cursor.fetchall()]

# Optimize for LLM
result = encode_optimal({"users": users})

print(f"Tokens saved: {result['json_tokens'] - result['toon_tokens']}")
print(f"Cost saved (GPT-4): ${(result['json_tokens'] - result['toon_tokens']) * 0.00001:.4f} per request")
```

### 3. Configuration Files

```python
from toon_tuna import encode, decode

# Save config in TOON format (more readable)
config = {
    "database": {"host": "localhost", "port": 5432},
    "cache": {"ttl": 3600, "max_size": 1000}
}

# Save
with open("config.toon", "w") as f:
    f.write(encode(config))

# Load
with open("config.toon", "r") as f:
    loaded_config = decode(f.read())
```

## Real-World Savings Example

**Scenario:** Processing 1,000 API requests/day with 100 user records each

```python
# Calculate savings
result = encode_optimal({
    "users": [{"id": i, "name": f"User{i}", "email": f"user{i}@example.com"}
              for i in range(100)]
})

tokens_saved_per_request = result['json_tokens'] - result['toon_tokens']
tokens_saved_per_day = tokens_saved_per_request * 1000
cost_per_day = tokens_saved_per_day * (10 / 1_000_000)  # GPT-4 pricing
cost_per_year = cost_per_day * 365

print(f"Tokens saved per request: {tokens_saved_per_request}")
print(f"Tokens saved per day: {tokens_saved_per_day:,}")
print(f"💰 Cost saved per year: ${cost_per_year:,.2f}")
```

**Output:**
```
Tokens saved per request: 456
Tokens saved per day: 456,000
💰 Cost saved per year: $1,664.40
```

## Next Steps

1. **Read the full documentation:** [README.md](README.md)
2. **Explore examples:** `python examples/basic_usage.py`
3. **Run tests:** `pytest tests/ -v`
4. **Try CLI examples:** `./examples/cli_examples.sh`
5. **Contribute:** See [CONTRIBUTING.md](CONTRIBUTING.md)

## Troubleshooting

### Import Error

```bash
# Make sure you've built the project
maturin develop

# Or installed from PyPI
pip install toon-tuna
```

### Rust Not Found

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

### Tests Failing

```bash
# Install test dependencies
pip install pytest tiktoken

# Run tests
pytest tests/ -v
```

## Getting Help

- 📖 **Documentation:** [README.md](README.md)
- 💬 **Issues:** [GitHub Issues](https://github.com/olsihoxha/toon-tuna/issues)
- 📧 **Contact:** maintainers@toon-tuna.dev

---

**Ready to save tokens? Start using `encode_optimal()` today!** 🐟

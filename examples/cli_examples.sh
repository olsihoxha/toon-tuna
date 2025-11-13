#!/bin/bash

# CLI Examples for toon-tuna
# Run these commands after installing: pip install toon-tuna

echo "🐟 toon-tuna CLI Examples"
echo "=========================="
echo

# Create sample data
cat > /tmp/sample_users.json <<EOF
{
  "users": [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "age": 25},
    {"id": 3, "name": "Carol", "email": "carol@example.com", "age": 35},
    {"id": 4, "name": "Dave", "email": "dave@example.com", "age": 28},
    {"id": 5, "name": "Eve", "email": "eve@example.com", "age": 32}
  ]
}
EOF

echo "Sample data created: /tmp/sample_users.json"
echo

# Example 1: Smart optimization (RECOMMENDED!)
echo "Example 1: Smart Optimization"
echo "=============================="
echo "Command: tuna optimize /tmp/sample_users.json --compare-all"
echo
tuna optimize /tmp/sample_users.json --compare-all
echo
echo

# Example 2: Encode to TOON
echo "Example 2: Encode JSON to TOON"
echo "==============================="
echo "Command: tuna encode /tmp/sample_users.json"
echo
tuna encode /tmp/sample_users.json
echo
echo

# Example 3: Save to file
echo "Example 3: Save to TOON file"
echo "============================="
echo "Command: tuna encode /tmp/sample_users.json -o /tmp/users.toon"
echo
tuna encode /tmp/sample_users.json -o /tmp/users.toon
echo "✅ Saved to /tmp/users.toon"
echo
cat /tmp/users.toon
echo
echo

# Example 4: Decode TOON to JSON
echo "Example 4: Decode TOON to JSON"
echo "==============================="
echo "Command: tuna decode /tmp/users.toon --pretty"
echo
tuna decode /tmp/users.toon --pretty
echo
echo

# Example 5: Estimate savings
echo "Example 5: Estimate Token Savings"
echo "=================================="
echo "Command: tuna estimate /tmp/sample_users.json"
echo
tuna estimate /tmp/sample_users.json
echo
echo

# Example 6: Use with pipes
echo "Example 6: Use with Pipes"
echo "========================="
echo "Command: echo '{\"users\":[{\"id\":1,\"name\":\"Alice\"}]}' | tuna optimize"
echo
echo '{"users":[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]}' | tuna optimize
echo
echo

# Example 7: Custom delimiter
echo "Example 7: Custom Delimiter (pipe)"
echo "==================================="
echo "Command: tuna encode /tmp/sample_users.json --delimiter '|'"
echo
tuna encode /tmp/sample_users.json --delimiter '|'
echo
echo

# Example 8: Large dataset
cat > /tmp/large_dataset.json <<EOF
{
  "products": [
EOF

for i in {1..100}; do
    if [ $i -eq 100 ]; then
        echo "    {\"sku\": \"PROD$(printf %04d $i)\", \"name\": \"Product $i\", \"price\": $((i * 10)), \"stock\": $((i % 100))}" >> /tmp/large_dataset.json
    else
        echo "    {\"sku\": \"PROD$(printf %04d $i)\", \"name\": \"Product $i\", \"price\": $((i * 10)), \"stock\": $((i % 100))}," >> /tmp/large_dataset.json
    fi
done

cat >> /tmp/large_dataset.json <<EOF
  ]
}
EOF

echo "Example 8: Large Dataset (100 products)"
echo "========================================"
echo "Command: tuna optimize /tmp/large_dataset.json --compare-all"
echo
tuna optimize /tmp/large_dataset.json --compare-all | head -20
echo "... (truncated)"
echo
echo

# Example 9: Save statistics
echo "Example 9: Save Statistics to File"
echo "==================================="
echo "Command: tuna optimize /tmp/sample_users.json -o /tmp/optimized.txt --stats-file /tmp/stats.json"
echo
tuna optimize /tmp/sample_users.json -o /tmp/optimized.txt --stats-file /tmp/stats.json --compare-all
echo
echo "📊 Statistics saved to /tmp/stats.json:"
cat /tmp/stats.json
echo
echo

# Example 10: Auto-detect format
echo "Example 10: Auto-detect Format"
echo "==============================="
echo "Command: tuna /tmp/users.toon (auto-detects TOON, converts to JSON)"
echo
tuna /tmp/users.toon --pretty | head -10
echo
echo

# Clean up
echo "🧹 Cleaning up temporary files..."
rm -f /tmp/sample_users.json /tmp/users.toon /tmp/large_dataset.json /tmp/optimized.txt /tmp/stats.json

echo
echo "✅ All examples completed!"
echo
echo "For more information:"
echo "  tuna --help"
echo "  tuna encode --help"
echo "  tuna optimize --help"

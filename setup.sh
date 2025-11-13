#!/bin/bash

# Setup script for toon-tuna development environment

set -e

echo "🐟 toon-tuna Setup Script"
echo "========================="
echo

# Check Python
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Found Python $PYTHON_VERSION"
echo

# Check Rust
echo "Checking Rust..."
if ! command -v rustc &> /dev/null; then
    echo "⚠️  Rust is not installed."
    echo
    read -p "Would you like to install Rust now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing Rust..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source $HOME/.cargo/env
        echo "✅ Rust installed successfully"
    else
        echo "❌ Rust is required. Please install from: https://rustup.rs/"
        exit 1
    fi
else
    RUST_VERSION=$(rustc --version | cut -d' ' -f2)
    echo "✅ Found Rust $RUST_VERSION"
fi
echo

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi
echo

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✅ pip upgraded"
echo

# Install maturin
echo "Installing maturin..."
pip install maturin > /dev/null 2>&1
echo "✅ maturin installed"
echo

# Install dependencies
echo "Installing Python dependencies..."
pip install tiktoken pytest pytest-cov pytest-benchmark ruff > /dev/null 2>&1
echo "✅ Dependencies installed"
echo

# Build the project
echo "Building toon-tuna..."
maturin develop
echo "✅ Build successful"
echo

# Run tests
echo "Running tests..."
if pytest tests/ -v --tb=short; then
    echo "✅ All tests passed!"
else
    echo "⚠️  Some tests failed. Please check the output above."
fi
echo

# Show installation info
echo "=" * 60
echo "🎉 Setup complete!"
echo "=" * 60
echo
echo "To use toon-tuna:"
echo "  source venv/bin/activate"
echo "  python -c 'from toon_tuna import encode_optimal; print(encode_optimal({\"test\": [1,2,3]}))'"
echo
echo "To run tests:"
echo "  pytest tests/ -v"
echo
echo "To run examples:"
echo "  python examples/basic_usage.py"
echo
echo "To use CLI:"
echo "  tuna --help"
echo
echo "For more information, see README.md"
echo

# Save activation command to .envrc for direnv users
if command -v direnv &> /dev/null; then
    echo "source venv/bin/activate" > .envrc
    echo "✅ Created .envrc for direnv users"
    echo "   Run 'direnv allow' to auto-activate the virtualenv"
fi

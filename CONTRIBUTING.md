# Contributing to toon-tuna

Thank you for your interest in contributing to toon-tuna! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

1. **Python 3.8+**
   ```bash
   python3 --version  # Should be 3.8 or higher
   ```

2. **Rust** (latest stable)
   ```bash
   # Install Rust
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source $HOME/.cargo/env

   # Verify installation
   rustc --version
   cargo --version
   ```

3. **Maturin** (for building Python extensions)
   ```bash
   pip install maturin
   ```

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/olsihoxha/toon-tuna.git
cd toon-tuna

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Build the Rust extension
maturin develop

# Verify installation
python -c "import toon_tuna; print('Success!')"
```

## Development Workflow

### Building

```bash
# Development build (faster, with debug info)
maturin develop

# Release build (optimized, slower to build)
maturin develop --release
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_optimal_selection.py -v

# Run with coverage
pytest tests/ --cov=toon_tuna --cov-report=html

# Run Rust tests
cargo test

# Run Rust tests with output
cargo test -- --nocapture
```

### Linting and Formatting

```bash
# Rust formatting
cargo fmt

# Rust linting
cargo clippy -- -D warnings

# Python linting
ruff check python/

# Python formatting
ruff format python/
```

### Running the CLI

```bash
# After maturin develop, the CLI should be available
tuna --help

# Test encoding
echo '{"users":[{"id":1,"name":"Alice"}]}' | tuna optimize --compare-all
```

## Code Structure

```
toon-tuna/
├── src/
│   └── lib.rs              # Rust implementation (encoder, decoder, PyO3 bindings)
├── python/
│   └── toon_tuna/
│       ├── __init__.py     # Python API (encode_optimal, etc.)
│       └── cli.py          # CLI tool
├── tests/
│   ├── test_encode_decode.py      # Basic functionality tests
│   ├── test_optimal_selection.py  # Smart selection tests
│   └── ...
├── Cargo.toml              # Rust dependencies
└── pyproject.toml          # Python package config
```

## Contributing Guidelines

### Code Style

**Rust:**
- Follow standard Rust conventions (`cargo fmt`)
- Use descriptive variable names
- Add comments for complex logic
- Write tests for new features

**Python:**
- Follow PEP 8 (use `ruff` for formatting)
- Type hints for public APIs
- Docstrings for all public functions
- Write tests for new features

### Commit Messages

Use clear, descriptive commit messages:

```
Add support for custom delimiters in TOON encoder

- Implement delimiter validation
- Add tests for tab and pipe delimiters
- Update documentation
```

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code
   - Add tests
   - Update documentation

3. **Test thoroughly**
   ```bash
   # Run all tests
   pytest tests/ -v
   cargo test

   # Check formatting
   cargo fmt --check
   ruff check python/
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Your descriptive message"
   git push origin feature/your-feature-name
   ```

5. **Create pull request**
   - Go to GitHub
   - Create PR from your branch to `main`
   - Fill out PR template
   - Wait for CI to pass
   - Request review

### Testing Requirements

All PRs must:
- ✅ Pass all existing tests
- ✅ Include tests for new features
- ✅ Maintain or improve code coverage (>80%)
- ✅ Pass linting checks
- ✅ Include documentation updates

## Areas for Contribution

### High Priority

- 🔥 **Performance optimizations** in Rust encoder/decoder
- 🔥 **More comprehensive TOON spec compliance** (edge cases)
- 🔥 **Additional test cases** for real-world data
- 🔥 **Benchmarking suite** with realistic datasets

### Medium Priority

- 📊 **Support for more tokenizers** (beyond tiktoken)
- 📊 **Streaming encoder/decoder** for large datasets
- 📊 **Better error messages** with context
- 📊 **Documentation improvements**

### Nice to Have

- ✨ **Web playground** for testing TOON encoding
- ✨ **VS Code extension** for TOON syntax highlighting
- ✨ **Integration examples** (LangChain, etc.)
- ✨ **Performance comparison dashboard**

## Running Benchmarks

```bash
# Python benchmarks
pytest tests/test_performance.py --benchmark-only

# Rust benchmarks
cargo bench
```

## Releasing (Maintainers Only)

```bash
# Update version in Cargo.toml and pyproject.toml
# Commit changes
git add Cargo.toml pyproject.toml
git commit -m "Bump version to 0.2.0"

# Create and push tag
git tag v0.2.0
git push origin main --tags

# GitHub Actions will automatically:
# - Build wheels for all platforms
# - Run tests
# - Publish to PyPI
# - Create GitHub release
```

## Getting Help

- 📖 **Documentation:** [README.md](README.md)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/olsihoxha/toon-tuna/discussions)
- 🐛 **Issues:** [GitHub Issues](https://github.com/olsihoxha/toon-tuna/issues)
- 📧 **Email:** maintainers@toon-tuna.dev

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to build something great together!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to toon-tuna! 🐟

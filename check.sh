#!/bin/bash

# Pre-commit quality check script
# Run this before committing to catch issues early

echo "🔍 Running pre-commit checks..."

# Exit on any failure
set -e

echo "📝 Checking code formatting with black..."
black --check .

echo "🔧 Running linter with ruff..."
ruff check .

echo "🔍 Running type checker with mypy..."
mypy .

echo "🧪 Running tests with pytest..."
pytest

echo "✅ All checks passed! Ready to commit."
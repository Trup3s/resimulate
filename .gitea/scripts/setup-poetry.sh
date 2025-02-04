#!/bin/bash
set -e

echo "Setting up Python and Poetry..."

# Install Poetry
pip install pipx
pipx install poetry

# Add Poetry to PATH
echo "$HOME/.poetry/bin" >> $GITHUB_PATH

poetry check

poetry lock --check

# Install dependencies
poetry install --no-root --no-interaction
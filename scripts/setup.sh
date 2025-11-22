#!/bin/bash
# Setup script for AML Casefile Generation System

set -e

echo "Setting up AML Casefile Generation System..."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p data/raw data/processed data/outputs logs models

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please update .env with your configuration"
fi

# Download model (optional - user can do this manually)
echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your configuration"
echo "2. (Optional) Download your Hugging Face model:"
echo "   python scripts/download_model.py"
echo "3. Run the system:"
echo "   python -m src.main"
echo ""


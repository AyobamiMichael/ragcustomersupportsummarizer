#!/bin/bash

set -e

echo "=== RAG Summarizer Setup ==="

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.9 or higher required"
    exit 1
fi

echo "Python version: $python_version ✓"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt

# Download ML models
echo "Downloading NLP models..."
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
python -m spacy download en_core_web_sm

# Download sentence transformer
echo "Downloading sentence transformer model..."
python << EOF
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder='./models')
print("Model downloaded successfully")
EOF

cd ..

# Setup environment file
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p backend/models
mkdir -p backend/logs
mkdir -p backend/tests/fixtures

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Start Redis: docker run -d -p 6379:6379 redis:7-alpine"
echo "3. Run the server: make run"
echo "4. Or use Docker: make docker-up"
echo ""

#!/bin/bash

# InvoiceExtractor Deployment Script

echo "Setting up InvoiceExtractor..."

# Check if we're on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS"
    PLATFORM="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Detected Linux"
    PLATFORM="Linux"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Setup backend
echo "Setting up backend..."
cd backend

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check if Tesseract is installed
if ! command -v tesseract &> /dev/null
then
    echo "Tesseract OCR is not installed"
    if [[ "$PLATFORM" == "macOS" ]]; then
        echo "Install Tesseract using: brew install tesseract"
    else
        echo "Install Tesseract using: sudo apt-get install tesseract-ocr"
    fi
    echo "Also install language data: sudo apt-get install tesseract-ocr-eng  (on Linux)"
    echo "Or: brew install tesseract-lang  (on macOS)"
else
    echo "Tesseract OCR is already installed"
fi

# Check if Poppler is installed (for PDF processing)
if ! command -v pdftoppm &> /dev/null
then
    echo "Poppler is not installed"
    if [[ "$PLATFORM" == "macOS" ]]; then
        echo "Install Poppler using: brew install poppler"
    else
        echo "Install Poppler using: sudo apt-get install poppler-utils"
    fi
else
    echo "Poppler is already installed"
fi

echo "Backend setup complete!"
echo "To run the backend:"
echo "1. cd backend"
echo "2. source venv/bin/activate"
echo "3. python app.py"

# Setup frontend
echo "Setting up frontend..."
cd ../frontend

echo "Frontend setup complete!"
echo "To run the frontend:"
echo "1. cd frontend"
echo "2. python -m http.server 8000"
echo "3. Open http://localhost:8000 in your browser"

echo "Deployment script completed!"
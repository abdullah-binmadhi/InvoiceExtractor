# Quick Start Guide

## Prerequisites
- Python 3.7 or higher
- pip (Python package manager)
- Tesseract OCR
- Poppler (for PDF processing)

## Installation Steps

### 1. Clone or Download the Repository
```
git clone <repository-url>
# or download and extract the ZIP file
```

### 2. Set Up the Backend

Navigate to the backend directory:
```bash
cd InvoiceExtractor/backend
```

Create and activate a virtual environment:
```bash
# On macOS/Linux
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Install system dependencies:
- **Tesseract OCR**: 
  - macOS: `brew install tesseract`
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
  - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

- **Poppler**:
  - macOS: `brew install poppler`
  - Ubuntu/Debian: `sudo apt-get install poppler-utils`
  - Windows: Download from [GitHub](https://github.com/oschwartz10612/poppler-windows/releases/)

### 3. Run the Backend Server

With the virtual environment activated:
```bash
python app.py
```

The backend will start on `http://localhost:5000`

### 4. Set Up the Frontend

In a new terminal, navigate to the frontend directory:
```bash
cd InvoiceExtractor/frontend
```

Serve the frontend files:
```bash
# Using Python's built-in server
python -m http.server 8000
```

### 5. Access the Application

Open your browser and go to `http://localhost:8000`

Login with the default credentials:
- Username: `admin`
- Password: `password`

### 6. Process Your First Invoice

1. Click "Browse Files" or drag and drop an invoice file (PDF/JPG/PNG)
2. Wait for processing to complete
3. Review and edit the extracted data if needed
4. Export results as JSON or CSV

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Make sure you've activated the virtual environment and installed all dependencies.

2. **Tesseract not found**: Ensure Tesseract is installed and added to your system PATH.

3. **Poppler not found**: Ensure Poppler is installed and added to your system PATH.

4. **CORS errors**: The application should already have CORS enabled, but if you encounter issues, check the Flask-CORS configuration.

### Need Help?

Check the detailed instructions in [README.md](README.md) or open an issue on the repository.
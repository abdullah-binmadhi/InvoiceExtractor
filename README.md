# InvoiceExtractor

A web application for extracting invoice data from PDFs and images using OCR.

## Features
- Upload PDF/image files (PDF, JPG, PNG up to 5MB)
- Extract invoice data using OCR and text processing
- View and edit extracted data
- Export results as JSON/CSV
- Processing history
- Simple authentication

## Tech Stack
- Backend: Python/Flask
- Frontend: Vanilla JavaScript
- Database: SQLite
- OCR: pytesseract
- PDF Processing: PyPDF2

## Project Structure
```
InvoiceExtractor/
├── README.md
├── deploy.sh                # Deployment script for macOS/Linux
├── deploy.bat               # Deployment script for Windows
├── backend/
│   ├── app.py              # Flask application entry point
│   ├── config.py           # Configuration settings
│   ├── database.py         # Database operations and schema
│   ├── processing.py       # Document processing and OCR
│   ├── routes.py           # API endpoints
│   ├── requirements.txt    # Python dependencies
│   └── test_backend.py     # Backend unit tests
└── frontend/
    ├── index.html          # Main application page
    ├── login.html          # Login page
    ├── styles.css          # Styling
    └── app.js              # Frontend logic
```

## Setup Instructions

### Backend Setup
1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows: `venv\\Scripts\\activate`
   - On macOS/Linux: `source venv/bin/activate`

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Install additional system dependencies:
   - Install Tesseract OCR: https://github.com/tesseract-ocr/tesseract
   - Install Poppler (for PDF to image conversion): https://github.com/oschwartz10612/poppler-windows/releases/

6. Run the Flask application:
   ```
   python app.py
   ```

### Frontend Setup
1. Serve the frontend files using any static file server.
   - Python example: `python -m http.server 8000` in the frontend directory
   - Navigate to `http://localhost:8000` in your browser

2. Login with the default credentials:
   - Username: admin
   - Password: password

## API Endpoints
- POST /api/upload - Upload document
- GET /api/results/{id} - Get extraction results
- POST /api/correct/{id} - Save manual corrections
- GET /api/history - List past extractions
- POST /api/login - User authentication
- GET /api/export/{id}/{format} - Export results (format: json or csv)

## Database Schema
- documents table: id, filename, upload_date, status
- extractions table: id, document_id, field_name, field_value, confidence_score
- corrections table: id, extraction_id, original_value, corrected_value
- users table: id, username, password_hash

## Processing Logic
1. Convert PDF to images if needed
2. Run OCR to get text
3. Use regex patterns to find invoice data:
   - Invoice numbers (INV-*, Invoice #*, etc.)
   - Dates (MM/DD/YYYY, DD-MM-YYYY patterns)
   - Money amounts ($XX.XX, total patterns)
   - Vendor names (top of document text)
4. Return structured JSON with confidence scores

## Implementation Details

### Backend Components
- **app.py**: Main Flask application with CORS enabled
- **config.py**: Configuration settings including file upload limits
- **database.py**: SQLite database schema and operations
- **processing.py**: Document processing logic with OCR and regex pattern matching
- **routes.py**: API endpoints for upload, results, corrections, history, and authentication

### Frontend Components
- **index.html**: Main application interface with upload, results, and history sections
- **login.html**: Simple authentication page
- **styles.css**: Responsive design with clean, modern styling
- **app.js**: Client-side logic for file handling, API communication, and UI updates

### Key Features Implemented
1. **File Upload**: Drag & drop interface with validation for PDF, JPG, PNG files up to 5MB
2. **Document Processing**: OCR with pytesseract and text extraction with PyPDF2
3. **Data Extraction**: Regex patterns to identify invoice fields (number, date, vendor, total, tax, line items)
4. **Editable Results**: Form interface to correct extracted data
5. **Export Functionality**: JSON/CSV export options
6. **Processing History**: View past document processing jobs
7. **Simple Authentication**: Basic login system with hashed passwords
8. **Responsive Design**: Mobile-friendly interface
9. **Progress Indicators**: Visual feedback during file processing
10. **Error Handling**: Proper validation and error messages for edge cases

## Deployment Scripts
- **deploy.sh**: Automated setup script for macOS/Linux
- **deploy.bat**: Automated setup script for Windows

## Testing
Run the backend tests with:
```
cd backend
python -m unittest test_backend.py -v
```

Note: Tests require all dependencies to be installed in the virtual environment.
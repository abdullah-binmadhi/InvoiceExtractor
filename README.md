# InvoiceExtractor

A web application for extracting invoice and receipt data from PDFs and images using OCR.

## Features
- Upload PDF/image files (PDF, JPG, PNG up to 5MB)
- Automatic document classification (invoice vs receipt)
- Extract invoice data using OCR and text processing
- Extract receipt data including detailed line items
- View and edit extracted data
- Export results as JSON/CSV
- Processing history with document type indicators
- Simple authentication
- Automatic expense categorization
- **Batch processing of multiple documents**
- **ZIP file support for batch uploads**

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
│   ├── processing.py        # Document processing and OCR
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
- POST /api/upload - Upload single document
- POST /api/classify-document - Classify document as invoice or receipt
- GET /api/results/{id} - Get extraction results for single document
- GET /api/receipts/{id} - Get receipt-specific data
- POST /api/correct/{id} - Save manual corrections
- GET /api/history - List past extractions
- POST /api/login - User authentication
- GET /api/export/{id}/{format} - Export results (format: json or csv)

### Batch Processing Endpoints
- POST /api/upload-batch - Upload and process multiple documents
- GET /api/batch-status/{batch_id} - Get processing progress for batch
- GET /api/batch-results/{batch_id} - Get all results from batch
- POST /api/download-batch/{batch_id} - Download batch results (JSON or CSV)

## Database Schema
- documents table: id, filename, upload_date, status, document_type, batch_id
- extractions table: id, document_id, field_name, field_value, confidence_score
- corrections table: id, extraction_id, original_value, corrected_value
- users table: id, username, password_hash
- receipt_items table: id, document_id, item_name, quantity, unit_price, total_price
- receipt_details table: id, document_id, merchant_name, location, payment_method, tip_amount, subtotal, tax_amount, total_amount, cashier_name, transaction_time, category
- batch_jobs table: id, user_id, status, total_files, processed_files, failed_files, created_date, completed_date

## Processing Logic

### Document Classification
The system automatically classifies documents as either invoices or receipts based on keyword analysis:
- Receipt indicators: "Thank you", store names, "Cash/Credit", time stamps
- Invoice indicators: "Invoice", "Bill To", "Due Date"

### Invoice Processing
1. Extract text from document (PDF or image)
2. Identify invoice fields using regex patterns:
   - Invoice numbers (INV-*, Invoice #*, etc.)
   - Dates (MM/DD/YYYY, DD-MM-YYYY patterns)
   - Money amounts ($XX.XX, total patterns)
   - Vendor names (top of document text)
   - Line items

### Receipt Processing
1. Extract text from document (PDF or image)
2. Identify receipt fields using regex patterns:
   - Merchant/store names (usually at top, all caps)
   - Store locations/addresses
   - Receipt numbers/transaction IDs
   - Payment methods (cash, card, etc.)
   - Detailed line items with quantities
   - Subtotal, tax, tip, total
   - Cashier/server names
   - Transaction dates and times

### Expense Categorization
Automatic categorization based on merchant names and keywords:
- Food & Dining (restaurants, cafes)
- Grocery (supermarkets, grocery stores)
- Transportation (gas stations, parking)
- Office Supplies (office stores, electronics)
- Travel (hotels, airlines)
- Entertainment (movies, events)

### Batch Processing
1. Create batch job record in database
2. Handle ZIP files or multiple individual uploads
3. Process each document individually with progress tracking
4. Update batch progress as each document completes
5. Generate combined results when batch finishes

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
2. **Document Classification**: Automatic detection of document type (invoice vs receipt)
3. **Document Processing**: OCR with pytesseract and text extraction with PyPDF2
4. **Data Extraction**: Regex patterns to identify document fields
5. **Editable Results**: Form interface to correct extracted data
6. **Export Functionality**: JSON/CSV export options
7. **Processing History**: View past document processing jobs with type indicators
8. **Simple Authentication**: Basic login system with hashed passwords
9. **Responsive Design**: Mobile-friendly interface
10. **Progress Indicators**: Visual feedback during file processing
11. **Error Handling**: Proper validation and error messages for edge cases
12. **Expense Categorization**: Automatic categorization of expenses
13. **Batch Processing**: Handle multiple documents simultaneously
14. **ZIP File Support**: Extract and process documents from ZIP archives

## Batch Processing Features
- Accept ZIP files containing multiple documents
- Support drag & drop of multiple individual files
- Maximum 20 files per batch, 50MB total size limit
- Real-time progress tracking
- Batch results summary with success/error counts
- Combined export options (JSON, CSV)
- Batch history view

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
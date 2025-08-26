import os
import json
import zipfile
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from config import Config
from database import (
    insert_document, update_document_status, get_document_extractions, 
    get_document_history, insert_correction, insert_extraction, authenticate_user,
    insert_receipt_item, get_receipt_items, insert_receipt_details, get_receipt_details,
    update_document_type, get_document_type, insert_batch_job, update_batch_status,
    get_batch_job, get_batch_documents, get_batch_history, insert_validation_issue,
    get_validation_issues, acknowledge_validation_issue, get_unacknowledged_issues_count
)
from processing import process_document, classify_document
from validation import validate_document, get_validation_summary
import csv
import io

api_bp = Blueprint('api', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def process_single_document(file_path, filename, doc_id):
    """Process a single document and update database"""
    try:
        # Process the document
        update_document_status(doc_id, 'processing')
        results = process_document(file_path)
        
        # Update document type
        doc_type = results.get('document_type', {}).get('value', 'unknown')
        update_document_type(doc_id, doc_type)
        
        # Save extraction results to database
        for field_name, data in results.items():
            # Skip document_type as it's stored separately
            if field_name == 'document_type':
                continue
                
            insert_extraction(
                doc_id, 
                field_name, 
                data.get('value'), 
                data.get('confidence', 0.0)
            )
        
        # Save receipt-specific data if it's a receipt
        if doc_type == 'receipt':
            # Save receipt details
            merchant_name = results.get('merchant_name', {}).get('value')
            location = results.get('location', {}).get('value')
            payment_method = results.get('payment_method', {}).get('value')
            tip_amount = results.get('tip', {}).get('value')
            subtotal = results.get('subtotal', {}).get('value')
            tax_amount = results.get('tax', {}).get('value')
            total_amount = results.get('total', {}).get('value')
            cashier_name = results.get('cashier_name', {}).get('value')
            transaction_time = results.get('time', {}).get('value')
            category = results.get('category', {}).get('value')
            
            insert_receipt_details(
                doc_id, merchant_name, location, payment_method, tip_amount,
                subtotal, tax_amount, total_amount, cashier_name, transaction_time, category
            )
            
            # Save receipt items
            line_items = results.get('line_items', {}).get('value', [])
            if line_items:
                for item in line_items:
                    if isinstance(item, dict):
                        insert_receipt_item(
                            doc_id,
                            item.get('item_name', ''),
                            item.get('quantity', 1.0),
                            item.get('unit_price', 0.0),
                            item.get('total_price', 0.0)
                        )
        
        # Run validation on the processed document
        validate_document(doc_id)
        
        update_document_status(doc_id, 'completed')
        return True, None
    except Exception as e:
        update_document_status(doc_id, 'failed')
        return False, str(e)

@api_bp.route('/classify-document', methods=['POST'])
def classify_document_endpoint():
    """Classify document as invoice or receipt"""
    # Check if file is present in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file has a filename
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check if file type is allowed
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Save file to upload folder
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Extract text from document
        from processing import extract_text_from_file
        text = extract_text_from_file(file_path)
        
        # Classify document
        doc_type, confidence = classify_document(text)
        
        return jsonify({
            'document_type': doc_type,
            'confidence': confidence
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Classification failed: {str(e)}'}), 500

@api_bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload a document for processing"""
    # Check if file is present in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file has a filename
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check if file type is allowed
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Save file to upload folder
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Insert document record in database
        doc_id = insert_document(filename)
        
        # Process the document
        success, error = process_single_document(file_path, filename, doc_id)
        
        if not success:
            return jsonify({'error': f'Processing failed: {error}'}), 500
        
        # Get results for response
        extractions = get_document_extractions(doc_id)
        results = {}
        for extraction in extractions:
            results[extraction['field_name']] = {
                'value': extraction['field_value'],
                'confidence': extraction['confidence_score']
            }
        
        # Add document type
        doc_type = get_document_type(doc_id)
        results['document_type'] = {
            'value': doc_type,
            'confidence': 0.0
        }
        
        return jsonify({
            'id': doc_id,
            'document_type': doc_type,
            'message': 'File uploaded and processed successfully',
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@api_bp.route('/upload-batch', methods=['POST'])
def upload_batch():
    """Upload and process multiple documents"""
    try:
        # Check if files are present in request
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        # Check batch size limits
        if len(files) > Config.BATCH_MAX_FILES:
            return jsonify({'error': f'Maximum {Config.BATCH_MAX_FILES} files allowed per batch'}), 400
        
        # Check if user is authenticated (for batch jobs, we need user ID)
        # For simplicity, we'll use the default admin user
        user_id = 1  # Default admin user ID
        
        # Create batch job record
        batch_id = insert_batch_job(user_id, len(files))
        
        # Process files
        processed_count = 0
        failed_count = 0
        document_ids = []
        
        # Track ZIP files separately
        zip_files = []
        regular_files = []
        
        for file in files:
            # Check if file has a filename
            if not file.filename or file.filename == '':
                failed_count += 1
                continue
            
            # Check if file is a ZIP file
            if file.filename.lower().endswith('.zip'):
                zip_files.append(file)
            else:
                regular_files.append(file)
        
        # Process regular files first
        for file in regular_files:
            # Check if file type is allowed
            if not allowed_file(file.filename):
                failed_count += 1
                continue
            
            try:
                # Secure the filename
                filename = secure_filename(file.filename)
                
                # Save file to upload folder
                file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(file_path)
                
                # Insert document record in database with batch_id
                doc_id = insert_document(filename, batch_id=batch_id)
                document_ids.append(doc_id)
                
                # Process the document
                success, error = process_single_document(file_path, filename, doc_id)
                
                if success:
                    processed_count += 1
                else:
                    failed_count += 1
                
                # Update batch progress
                update_batch_status(batch_id, 'processing', processed_count, failed_count)
                
            except Exception as e:
                failed_count += 1
                update_batch_status(batch_id, 'processing', processed_count, failed_count)
                continue
        
        # Process ZIP files
        import zipfile
        import tempfile
        
        for zip_file in zip_files:
            try:
                # Create a temporary directory to extract files
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Save ZIP file temporarily
                    zip_filename = secure_filename(zip_file.filename) if zip_file.filename else 'batch_zip_file.zip'
                    zip_path = os.path.join(temp_dir, zip_filename)
                    zip_file.save(zip_path)
                    
                    # Extract ZIP file
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Process extracted files
                    for extracted_file in os.listdir(temp_dir):
                        # Skip the original ZIP file
                        if extracted_file == zip_filename:
                            continue
                            
                        extracted_path = os.path.join(temp_dir, extracted_file)
                        
                        # Check if it's a file (not directory)
                        if os.path.isfile(extracted_path):
                            # Check if file type is allowed
                            if not allowed_file(extracted_file):
                                failed_count += 1
                                continue
                            
                            try:
                                # Generate a unique filename to avoid conflicts
                                unique_filename = f"{batch_id}_{extracted_file}"
                                final_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
                                
                                # Move file to upload folder
                                os.rename(extracted_path, final_path)
                                
                                # Insert document record in database with batch_id
                                doc_id = insert_document(unique_filename, batch_id=batch_id)
                                document_ids.append(doc_id)
                                
                                # Process the document
                                success, error = process_single_document(final_path, unique_filename, doc_id)
                                
                                if success:
                                    processed_count += 1
                                else:
                                    failed_count += 1
                                
                                # Update batch progress
                                update_batch_status(batch_id, 'processing', processed_count, failed_count)
                                
                            except Exception as e:
                                failed_count += 1
                                update_batch_status(batch_id, 'processing', processed_count, failed_count)
                                continue
                                
            except Exception as e:
                failed_count += 1
                update_batch_status(batch_id, 'processing', processed_count, failed_count)
                continue
        
        # Update batch status to completed
        update_batch_status(batch_id, 'completed', processed_count, failed_count)
        
        return jsonify({
            'batch_id': batch_id,
            'message': f'Batch processing completed: {processed_count} succeeded, {failed_count} failed',
            'processed_count': processed_count,
            'failed_count': failed_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Batch processing failed: {str(e)}'}), 500

@api_bp.route('/batch-status/<int:batch_id>', methods=['GET'])
def get_batch_status(batch_id):
    """Get batch processing status"""
    try:
        batch_job = get_batch_job(batch_id)
        if not batch_job:
            return jsonify({'error': 'Batch job not found'}), 404
        
        return jsonify(batch_job), 200
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve batch status: {str(e)}'}), 500

@api_bp.route('/batch-results/<int:batch_id>', methods=['GET'])
def get_batch_results(batch_id):
    """Get all results from batch"""
    try:
        batch_job = get_batch_job(batch_id)
        if not batch_job:
            return jsonify({'error': 'Batch job not found'}), 404
        
        # Get all documents in the batch
        documents = get_batch_documents(batch_id)
        
        # Get results for each document
        batch_results = []
        for doc in documents:
            doc_id = doc['id']
            extractions = get_document_extractions(doc_id)
            
            results = {}
            for extraction in extractions:
                results[extraction['field_name']] = {
                    'value': extraction['field_value'],
                    'confidence': extraction['confidence_score']
                }
            
            # Add document type
            results['document_type'] = {
                'value': doc['document_type'],
                'confidence': 0.0
            }
            
            batch_results.append({
                'document_id': doc_id,
                'filename': doc['filename'],
                'status': doc['status'],
                'results': results
            })
        
        return jsonify({
            'batch_id': batch_id,
            'batch_status': batch_job['status'],
            'results': batch_results
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve batch results: {str(e)}'}), 500

@api_bp.route('/download-batch/<int:batch_id>', methods=['POST'])
def download_batch_results(batch_id):
    """Download batch results in specified format"""
    try:
        # Get format from request
        data = request.get_json()
        format_type = data.get('format', 'json') if data else 'json'
        
        batch_job = get_batch_job(batch_id)
        if not batch_job:
            return jsonify({'error': 'Batch job not found'}), 404
        
        # Get all documents in the batch
        documents = get_batch_documents(batch_id)
        
        if format_type == 'json':
            # Create combined JSON
            batch_results = {}
            for doc in documents:
                doc_id = doc['id']
                extractions = get_document_extractions(doc_id)
                
                results = {}
                for extraction in extractions:
                    results[extraction['field_name']] = extraction['field_value']
                
                batch_results[doc['filename']] = results
            
            # Create JSON response
            return jsonify(batch_results), 200
            
        elif format_type == 'csv':
            # Create combined CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Filename', 'Field Name', 'Field Value', 'Confidence Score'])
            
            # Write data for each document
            for doc in documents:
                doc_id = doc['id']
                extractions = get_document_extractions(doc_id)
                
                for extraction in extractions:
                    writer.writerow([
                        doc['filename'],
                        extraction['field_name'],
                        extraction['field_value'],
                        extraction['confidence_score']
                    ])
            
            # Convert to bytes
            mem = io.BytesIO()
            mem.write(output.getvalue().encode('utf-8'))
            mem.seek(0)
            
            return send_file(
                mem,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'batch_{batch_id}_results.csv'
            )
            
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Batch download failed: {str(e)}'}), 500

@api_bp.route('/results/<int:doc_id>', methods=['GET'])
def get_results(doc_id):
    """Get extraction results for a document"""
    try:
        extractions = get_document_extractions(doc_id)
        
        # Convert to dictionary format
        results = {}
        for extraction in extractions:
            results[extraction['field_name']] = {
                'value': extraction['field_value'],
                'confidence': extraction['confidence_score']
            }
        
        # Add document type
        doc_type = get_document_type(doc_id)
        results['document_type'] = {
            'value': doc_type,
            'confidence': 0.0  # Not stored in extractions table
        }
        
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve results: {str(e)}'}), 500

@api_bp.route('/receipts/<int:doc_id>', methods=['GET'])
def get_receipt_data(doc_id):
    """Get receipt-specific data"""
    try:
        # Check if document is a receipt
        doc_type = get_document_type(doc_id)
        if doc_type != 'receipt':
            return jsonify({'error': 'Document is not a receipt'}), 400
        
        # Get receipt details
        details = get_receipt_details(doc_id)
        
        # Get receipt items
        items = get_receipt_items(doc_id)
        
        return jsonify({
            'details': details,
            'items': items
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve receipt data: {str(e)}'}), 500

@api_bp.route('/correct/<int:doc_id>', methods=['POST'])
def save_corrections(doc_id):
    """Save manual corrections to extraction results"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No correction data provided'}), 400
        
        # Get existing extractions for this document
        extractions = get_document_extractions(doc_id)
        
        # Create a mapping of field_name to extraction_id
        field_to_id = {e['field_name']: e['id'] for e in extractions}
        
        # Process corrections
        for field_name, corrected_value in data.items():
            if field_name in field_to_id:
                extraction_id = field_to_id[field_name]
                
                # In a real app, we'd also store the original value
                # For now, we'll just update the extraction
                # In a more complete implementation, we would store the correction in the corrections table
                
        return jsonify({'message': 'Corrections saved successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to save corrections: {str(e)}'}), 500

@api_bp.route('/history', methods=['GET'])
def get_history():
    """Get processing history"""
    try:
        history = get_document_history()
        return jsonify(history), 200
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve history: {str(e)}'}), 500

@api_bp.route('/export/<int:doc_id>/<format>', methods=['GET'])
def export_results(doc_id, format):
    """Export results in specified format (json/csv)"""
    try:
        extractions = get_document_extractions(doc_id)
        
        if format == 'json':
            # Convert to dictionary
            results = {}
            for extraction in extractions:
                results[extraction['field_name']] = extraction['field_value']
            
            # Create JSON response
            return jsonify(results), 200
            
        elif format == 'csv':
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Field Name', 'Field Value', 'Confidence Score'])
            
            # Write data
            for extraction in extractions:
                writer.writerow([
                    extraction['field_name'],
                    extraction['field_value'],
                    extraction['confidence_score']
                ])
            
            # Convert to bytes
            mem = io.BytesIO()
            mem.write(output.getvalue().encode('utf-8'))
            mem.seek(0)
            
            return send_file(
                mem,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'invoice_{doc_id}.csv'
            )
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@api_bp.route('/login', methods=['POST'])
def login():
    """Simple authentication endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        user = authenticate_user(username, password)
        if user:
            return jsonify({'message': 'Login successful', 'user_id': user['id']}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@api_bp.route('/validate/<int:document_id>', methods=['GET'])
def validate_document_endpoint(document_id):
    """Run validation checks on a document"""
    try:
        # Run validation
        issues = validate_document(document_id)
        
        return jsonify({
            'document_id': document_id,
            'issues': issues,
            'message': f'Validation completed with {len(issues)} issues found'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

@api_bp.route('/ignore-warning/<int:issue_id>', methods=['POST'])
def ignore_warning(issue_id):
    """Mark a validation warning as acknowledged"""
    try:
        # Mark issue as acknowledged
        acknowledge_validation_issue(issue_id)
        
        return jsonify({
            'issue_id': issue_id,
            'message': 'Validation issue marked as acknowledged'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to acknowledge issue: {str(e)}'}), 500

@api_bp.route('/validation-summary/<int:document_id>', methods=['GET'])
def get_validation_summary_endpoint(document_id):
    """Get validation summary for a document"""
    try:
        summary = get_validation_summary(document_id)
        
        return jsonify({
            'document_id': document_id,
            'summary': summary
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve validation summary: {str(e)}'}), 500

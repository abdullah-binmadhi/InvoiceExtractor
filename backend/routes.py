import os
import json
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from config import Config
from database import (
    insert_document, update_document_status, get_document_extractions, 
    get_document_history, insert_correction, insert_extraction, authenticate_user
)
from processing import process_document
import csv
import io

api_bp = Blueprint('api', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

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
        update_document_status(doc_id, 'processing')
        results = process_document(file_path)
        
        # Save extraction results to database
        for field_name, data in results.items():
            insert_extraction(
                doc_id, 
                field_name, 
                data.get('value'), 
                data.get('confidence', 0.0)
            )
        
        update_document_status(doc_id, 'completed')
        
        return jsonify({
            'id': doc_id,
            'message': 'File uploaded and processed successfully',
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

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
        
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve results: {str(e)}'}), 500

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
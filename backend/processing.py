import os
import re
import PyPDF2
import pytesseract
from PIL import Image
import io
import tempfile

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")
    return text

def extract_text_from_image(image_path):
    """Extract text from image using OCR"""
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from image: {str(e)}")

def pdf_to_images(pdf_path):
    """Convert PDF pages to images"""
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path)
        return images
    except Exception as e:
        raise Exception(f"Failed to convert PDF to images: {str(e)}")

def extract_text_from_file(file_path):
    """Extract text from file (PDF or image)"""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext == '.pdf':
        # Try to extract text directly first
        text = extract_text_from_pdf(file_path)
        # If text extraction failed or text is minimal, use OCR
        if len(text.strip()) < 50:
            # Convert PDF to images and run OCR
            images = pdf_to_images(file_path)
            ocr_text = ""
            for image in images:
                ocr_text += pytesseract.image_to_string(image) + "\n"
            text = ocr_text
        return text
    elif ext in ['.png', '.jpg', '.jpeg']:
        return extract_text_from_image(file_path)
    else:
        raise Exception(f"Unsupported file format: {ext}")

def find_invoice_number(text):
    """Find invoice number in text"""
    patterns = [
        r'invoice\s*[#:]?\s*([A-Z0-9\-]+)',
        r'inv[-\s]*([0-9]+)',
        r'invoice\s*number\s*[:\-]?\s*([A-Z0-9\-]+)',
        r'(?:invoice|inv)[\s.#]*([A-Z0-9]{1,20})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(), 0.9
    
    return None, 0.0

def find_date(text):
    """Find date in text"""
    patterns = [
        r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
        r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1), 0.8
    
    return None, 0.0

def find_total_amount(text):
    """Find total amount in text"""
    # Look for patterns like Total, Amount, etc.
    patterns = [
        r'(?:total|amount)[\s:]*\$?([0-9,]+\.?[0-9]*)',
        r'\$([0-9,]+\.?[0-9]*)',
        r'([0-9,]+\.?[0-9]*)\s*(?:usd|dollars)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Clean the amount
            amount = match.group(1).replace(',', '')
            try:
                float(amount)
                return amount, 0.9
            except ValueError:
                continue
    
    return None, 0.0

def find_vendor_name(text):
    """Find vendor name (simplified approach)"""
    # This is a simplified approach - in a real app, you'd have a more sophisticated method
    lines = text.split('\n')
    if lines:
        # First non-empty line is often the vendor
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line) > 3 and not re.search(r'\d', line):
                return line, 0.7
    
    return None, 0.0

def find_tax_amount(text):
    """Find tax amount in text"""
    patterns = [
        r'(?:tax|gst|hst)[\s:]*\$?([0-9,]+\.?[0-9]*)',
        r'\btax\b.*?\$([0-9,]+\.?[0-9]*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = match.group(1).replace(',', '')
            try:
                float(amount)
                return amount, 0.8
            except ValueError:
                continue
    
    return None, 0.0

def find_line_items(text):
    """Find line items in text (simplified)"""
    # This is a very simplified approach - a real implementation would be much more complex
    lines = text.split('\n')
    items = []
    
    # Look for lines that might contain items (with prices)
    price_pattern = r'\$([0-9,]+\.?[0-9]*)'
    
    for line in lines:
        if re.search(price_pattern, line) and len(line.strip()) > 10:
            # Extract description and amount
            match = re.search(r'^(.*?)(\$[0-9,]+\.?[0-9]*)$', line)
            if match:
                description = match.group(1).strip()
                amount = match.group(2).replace('$', '')
                items.append({
                    'description': description,
                    'amount': amount
                })
    
    if items:
        return items, 0.7
    
    return None, 0.0

def process_document(file_path):
    """Main document processing function"""
    try:
        # Extract text from document
        text = extract_text_from_file(file_path)
        
        if not text.strip():
            raise Exception("No text could be extracted from the document")
        
        # Extract fields
        results = {}
        
        # Invoice number
        invoice_num, confidence = find_invoice_number(text)
        results['invoice_number'] = {
            'value': invoice_num,
            'confidence': confidence
        }
        
        # Date
        date, confidence = find_date(text)
        results['date'] = {
            'value': date,
            'confidence': confidence
        }
        
        # Vendor name
        vendor, confidence = find_vendor_name(text)
        results['vendor'] = {
            'value': vendor,
            'confidence': confidence
        }
        
        # Total amount
        total, confidence = find_total_amount(text)
        results['total'] = {
            'value': total,
            'confidence': confidence
        }
        
        # Tax amount
        tax, confidence = find_tax_amount(text)
        results['tax'] = {
            'value': tax,
            'confidence': confidence
        }
        
        # Line items
        items, confidence = find_line_items(text)
        results['line_items'] = {
            'value': items,
            'confidence': confidence
        }
        
        return results
        
    except Exception as e:
        raise Exception(f"Document processing failed: {str(e)}")
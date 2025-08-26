import os
import re
import PyPDF2
import pytesseract
from PIL import Image
import io
import tempfile
from datetime import datetime

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

def classify_document(text):
    """Classify document as invoice or receipt based on keywords"""
    # Convert to lowercase for matching
    text_lower = text.lower()
    
    # Receipt indicators
    receipt_indicators = [
        'thank you', 'cash', 'credit', 'debit', 'total', 'subtotal', 'tax',
        'change', 'balance', 'paid', 'tender', 'transaction', 'store',
        'grocery', 'gas', 'restaurant', 'tip', 'gratuity'
    ]
    
    # Invoice indicators
    invoice_indicators = [
        'invoice', 'bill to', 'due date', 'terms', 'invoice #', 'inv-',
        'amount due', 'balance due', 'payment due', 'remittance'
    ]
    
    # Count matches
    receipt_matches = sum(1 for indicator in receipt_indicators if indicator in text_lower)
    invoice_matches = sum(1 for indicator in invoice_indicators if indicator in text_lower)
    
    # Determine document type based on higher match count
    if receipt_matches > invoice_matches:
        return 'receipt', max(receipt_matches / len(receipt_indicators), 0.5)
    elif invoice_matches > receipt_matches:
        return 'invoice', max(invoice_matches / len(invoice_indicators), 0.5)
    else:
        # Default to invoice if no clear indicator
        return 'invoice', 0.5

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

def find_time(text):
    """Find time in text (for receipts)"""
    patterns = [
        r'\b(\d{1,2}:\d{2}\s*(?:am|pm)?)\b',
        r'\b(\d{1,2}:\d{2}:\d{2})\b'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
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

def find_subtotal_amount(text):
    """Find subtotal amount in text"""
    patterns = [
        r'(?:subtotal|sub total)[\s:]*\$?([0-9,]+\.?[0-9]*)',
        r'\$([0-9,]+\.?[0-9]*)\s*(?:subtotal|sub total)'
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

def find_merchant_name(text):
    """Find merchant name for receipts (usually at top, all caps)"""
    lines = text.split('\n')
    if lines:
        # Look for merchant name in first few lines (often in all caps)
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            # Check if line is in all caps and not too short
            if len(line) > 3 and line.isupper() and not re.search(r'[0-9]', line):
                # Check if next line also contains address-like info
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if re.search(r'[0-9]', next_line) or re.search(r'[a-zA-Z]{2,}', next_line):
                        return line, 0.8
                return line, 0.7
    
    # Fallback to general vendor name extraction
    return find_vendor_name(text)

def find_location(text):
    """Find store location/address"""
    lines = text.split('\n')
    address_pattern = r'\d+\s+[a-zA-Z0-9\s]+(?:st|street|ave|avenue|rd|road|blvd|boulevard|dr|drive|ln|lane|ct|court|pl|place|way|pkwy|parkway|cir|circle)\.?\s*[a-zA-Z]{2,}'
    
    for line in lines:
        line = line.strip()
        match = re.search(address_pattern, line, re.IGNORECASE)
        if match:
            return match.group(0), 0.8
    
    return None, 0.0

def find_payment_method(text):
    """Find payment method"""
    text_lower = text.lower()
    payment_methods = {
        'cash': ['cash', 'cashier'],
        'credit': ['credit', 'visa', 'mastercard', 'amex', 'discover'],
        'debit': ['debit'],
        'check': ['check', 'cheque']
    }
    
    for method, keywords in payment_methods.items():
        for keyword in keywords:
            if keyword in text_lower:
                return method, 0.9
    
    return None, 0.0

def find_tip_amount(text):
    """Find tip amount in text"""
    patterns = [
        r'(?:tip|gratuity)[\s:]*\$?([0-9,]+\.?[0-9]*)',
        r'\$([0-9,]+\.?[0-9]*)\s*(?:tip|gratuity)'
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

def find_cashier_name(text):
    """Find cashier/server name"""
    patterns = [
        r'(?:cashier|server)[\s:]*([a-zA-Z\s]+)',
        r'([a-zA-Z\s]+)\s*(?:cashier|server)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Check if it looks like a name (not too long, no numbers)
            if 2 < len(name) < 30 and not re.search(r'\d', name):
                return name, 0.7
    
    return None, 0.0

def find_receipt_number(text):
    """Find receipt/transaction number"""
    patterns = [
        r'(?:receipt|transaction)[\s#:]*(?:no\.?)?[\s:]*([A-Z0-9\-]+)',
        r'([A-Z0-9]{4,20})\s*(?:receipt|transaction)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(), 0.8
    
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

def find_detailed_line_items(text):
    """Find detailed line items with quantities and unit prices for receipts"""
    lines = text.split('\n')
    items = []
    
    # Pattern for items with quantity x unit price = total
    # e.g., "2 x $5.99 = $11.98" or "2 @ $5.99 $11.98"
    detailed_pattern = r'(\d+(?:\.\d+)?)\s*[x@]\s*\$?([0-9,]+\.?[0-9]*)\s*(?:=\s*)?\$?([0-9,]+\.?[0-9]*)'
    
    for line in lines:
        match = re.search(detailed_pattern, line)
        if match:
            quantity = float(match.group(1))
            unit_price = float(match.group(2).replace(',', ''))
            total_price = float(match.group(3).replace(',', ''))
            
            # Extract item name (text before the pattern)
            name_match = re.search(r'^(.*?)\s*\d', line)
            item_name = name_match.group(1).strip() if name_match else "Unknown Item"
            
            items.append({
                'item_name': item_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price
            })
    
    # Fallback to simple line items if detailed pattern not found
    if not items:
        simple_items, confidence = find_line_items(text)
        if simple_items:
            for item in simple_items:
                items.append({
                    'item_name': item['description'],
                    'quantity': 1.0,
                    'unit_price': float(item['amount']),
                    'total_price': float(item['amount'])
                })
            return items, 0.5
    
    if items:
        return items, 0.8
    
    return None, 0.0

def categorize_expense(text, merchant_name=None):
    """Categorize expense based on keywords"""
    text_lower = text.lower()
    
    categories = {
        'Food & Dining': ['restaurant', 'cafe', 'coffee', 'food', 'dining', 'meal', 'burger', 'pizza', 'steak'],
        'Grocery': ['grocery', 'market', 'supermarket', 'food store', 'whole foods', 'kroger', 'walmart', 'costco'],
        'Transportation': ['gas', 'fuel', 'station', 'parking', 'uber', 'taxi', 'bus', 'train', 'airline'],
        'Office Supplies': ['office', 'staples', 'office depot', 'paper', 'pen', 'printer'],
        'Travel': ['hotel', 'motel', 'airbnb', 'flight', 'airline', 'travel', 'booking'],
        'Entertainment': ['movie', 'cinema', 'theater', 'concert', 'event', 'ticket', 'amusement']
    }
    
    # Check merchant name first
    if merchant_name:
        merchant_lower = merchant_name.lower()
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in merchant_lower:
                    return category, 0.9
    
    # Check document text
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category, 0.8
    
    return 'Other', 0.5

def process_invoice(text):
    """Process invoice-specific fields"""
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

def process_receipt(text):
    """Process receipt-specific fields"""
    results = {}
    
    # Merchant/store name
    merchant, confidence = find_merchant_name(text)
    results['merchant_name'] = {
        'value': merchant,
        'confidence': confidence
    }
    
    # Store location/address
    location, confidence = find_location(text)
    results['location'] = {
        'value': location,
        'confidence': confidence
    }
    
    # Receipt number/transaction ID
    receipt_num, confidence = find_receipt_number(text)
    results['receipt_number'] = {
        'value': receipt_num,
        'confidence': confidence
    }
    
    # Payment method
    payment_method, confidence = find_payment_method(text)
    results['payment_method'] = {
        'value': payment_method,
        'confidence': confidence
    }
    
    # Date and time
    date, date_confidence = find_date(text)
    time, time_confidence = find_time(text)
    results['date'] = {
        'value': date,
        'confidence': date_confidence
    }
    results['time'] = {
        'value': time,
        'confidence': time_confidence
    }
    
    # Subtotal, tax, tip, total
    subtotal, confidence = find_subtotal_amount(text)
    results['subtotal'] = {
        'value': subtotal,
        'confidence': confidence
    }
    
    tax, confidence = find_tax_amount(text)
    results['tax'] = {
        'value': tax,
        'confidence': confidence
    }
    
    tip, confidence = find_tip_amount(text)
    results['tip'] = {
        'value': tip,
        'confidence': confidence
    }
    
    total, confidence = find_total_amount(text)
    results['total'] = {
        'value': total,
        'confidence': confidence
    }
    
    # Cashier/server name
    cashier, confidence = find_cashier_name(text)
    results['cashier_name'] = {
        'value': cashier,
        'confidence': confidence
    }
    
    # Detailed line items
    items, confidence = find_detailed_line_items(text)
    results['line_items'] = {
        'value': items,
        'confidence': confidence
    }
    
    # Expense category
    category, confidence = categorize_expense(text, merchant)
    results['category'] = {
        'value': category,
        'confidence': confidence
    }
    
    return results

def process_document(file_path):
    """Main document processing function"""
    try:
        # Extract text from document
        text = extract_text_from_file(file_path)
        
        if not text.strip():
            raise Exception("No text could be extracted from the document")
        
        # Classify document type
        doc_type, confidence = classify_document(text)
        
        # Process based on document type
        if doc_type == 'receipt':
            results = process_receipt(text)
        else:
            results = process_invoice(text)
        
        # Add document type to results
        results['document_type'] = {
            'value': doc_type,
            'confidence': confidence
        }
        
        return results
        
    except Exception as e:
        raise Exception(f"Document processing failed: {str(e)}")
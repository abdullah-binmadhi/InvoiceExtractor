import re
from datetime import datetime
from database import (
    get_document_extractions, get_receipt_items, get_receipt_details, 
    insert_validation_issue, get_validation_issues
)

# Standard tax rates to check against
STANDARD_TAX_RATES = [0.05, 0.075, 0.10, 0.15]  # 5%, 7.5%, 10%, 15%

def validate_document(document_id):
    """Run all validation checks on a document"""
    # Clear any existing validation issues for this document
    # (In a real implementation, you might want to be more selective about this)
    
    # Get document data
    extractions = get_document_extractions(document_id)
    receipt_items = get_receipt_items(document_id)
    receipt_details = get_receipt_details(document_id)
    
    # Convert extractions to a dictionary for easier access
    extracted_data = {}
    for extraction in extractions:
        extracted_data[extraction['field_name']] = {
            'value': extraction['field_value'],
            'confidence': extraction['confidence_score']
        }
    
    # Run validation checks
    validation_issues = []
    
    # 1. Mathematical validation
    math_issues = validate_mathematical_rules(extracted_data, receipt_items, receipt_details)
    validation_issues.extend(math_issues)
    
    # 2. Business logic validation
    business_issues = validate_business_rules(extracted_data, receipt_details)
    validation_issues.extend(business_issues)
    
    # 3. Data quality checks
    quality_issues = validate_data_quality(extracted_data)
    validation_issues.extend(quality_issues)
    
    # Store validation issues in database
    for issue in validation_issues:
        insert_validation_issue(
            document_id,
            issue['issue_type'],
            issue['severity'],
            issue['description']
        )
    
    return validation_issues

def validate_mathematical_rules(extracted_data, receipt_items, receipt_details):
    """Validate mathematical relationships in the document"""
    issues = []
    
    try:
        # Check if line items sum to subtotal
        if receipt_items and receipt_details:
            calculated_subtotal = sum(item.get('total_price', 0) for item in receipt_items)
            extracted_subtotal = float(receipt_details.get('subtotal', 0) or 0)
            
            if calculated_subtotal > 0 and abs(calculated_subtotal - extracted_subtotal) > 0.01:
                issues.append({
                    'issue_type': 'MATH_ERROR',
                    'severity': 'ERROR',
                    'description': f'Line items sum (${calculated_subtotal:.2f}) does not match subtotal (${extracted_subtotal:.2f})'
                })
        
        # Check tax calculations
        subtotal = float(receipt_details.get('subtotal', 0) or 0)
        tax_amount = float(receipt_details.get('tax_amount', 0) or 0)
        total_amount = float(receipt_details.get('total_amount', 0) or 0)
        
        if subtotal > 0 and tax_amount > 0:
            calculated_total_with_tax = subtotal + tax_amount
            # Check if tax amount matches standard rates
            tax_rate = tax_amount / subtotal
            if not any(abs(tax_rate - rate) < 0.005 for rate in STANDARD_TAX_RATES):  # Allow 0.5% tolerance
                # Find closest standard rate
                closest_rate = min(STANDARD_TAX_RATES, key=lambda x: abs(x - tax_rate))
                issues.append({
                    'issue_type': 'MATH_ERROR',
                    'severity': 'WARNING',
                    'description': f'Unusual tax rate: {tax_rate:.2%} (expected rates: {", ".join(f"{r:.0%}" for r in STANDARD_TAX_RATES)})'
                })
            
            # Check if total matches subtotal + tax
            if abs(calculated_total_with_tax - total_amount) > 0.01:
                issues.append({
                    'issue_type': 'MATH_ERROR',
                    'severity': 'ERROR',
                    'description': f'Total (${total_amount:.2f}) does not match subtotal + tax (${calculated_total_with_tax:.2f})'
                })
        
        # Validate tip percentages (for receipts)
        if receipt_details and receipt_details.get('tip_amount'):
            tip_amount = float(receipt_details.get('tip_amount', 0) or 0)
            if tip_amount > 0 and subtotal > 0:
                tip_percentage = tip_amount / subtotal
                if tip_percentage < 0.10 or tip_percentage > 0.25:  # 10-25% range
                    issues.append({
                        'issue_type': 'MATH_ERROR',
                        'severity': 'WARNING',
                        'description': f'Unusual tip percentage: {tip_percentage:.2%} (expected range: 10-25%)'
                    })
    
    except (ValueError, TypeError) as e:
        issues.append({
            'issue_type': 'MATH_ERROR',
            'severity': 'ERROR',
            'description': f'Error in mathematical validation: {str(e)}'
        })
    
    return issues

def validate_business_rules(extracted_data, receipt_details):
    """Validate business logic rules"""
    issues = []
    
    try:
        # Check for unreasonable amounts
        total_amount = None
        if receipt_details and receipt_details.get('total_amount'):
            total_amount = float(receipt_details.get('total_amount', 0) or 0)
        elif extracted_data.get('total'):
            total_amount = float(extracted_data['total'].get('value', 0) or 0)
        
        if total_amount is not None:
            if total_amount > 10000:
                issues.append({
                    'issue_type': 'SUSPICIOUS_AMOUNT',
                    'severity': 'WARNING',
                    'description': f'Unusually high amount: ${total_amount:.2f} (over $10,000)'
                })
            elif total_amount < 1:
                issues.append({
                    'issue_type': 'SUSPICIOUS_AMOUNT',
                    'severity': 'WARNING',
                    'description': f'Unusually low amount: ${total_amount:.2f} (under $1.00)'
                })
        
        # Check for future dates
        date_value = None
        if extracted_data.get('date'):
            date_value = extracted_data['date'].get('value')
        
        if date_value:
            try:
                # Parse date (handle multiple formats)
                parsed_date = None
                for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d-%m-%Y']:
                    try:
                        parsed_date = datetime.strptime(date_value, fmt)
                        break
                    except ValueError:
                        continue
                
                if parsed_date and parsed_date.date() > datetime.now().date():
                    issues.append({
                        'issue_type': 'SUSPICIOUS_AMOUNT',
                        'severity': 'ERROR',
                        'description': f'Future date detected: {date_value} (today is {datetime.now().date()})'
                    })
            except ValueError:
                # If we can't parse the date, that's a data quality issue, not a business rule issue
                pass
        
        # Check for weekend business hours (for receipts)
        if receipt_details and receipt_details.get('transaction_time'):
            time_value = receipt_details.get('transaction_time')
            date_value = None
            if extracted_data.get('date'):
                date_value = extracted_data['date'].get('value')
            
            # Check if we have both date and time
            if date_value and time_value:
                try:
                    # Parse date
                    parsed_date = None
                    for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d-%m-%Y']:
                        try:
                            parsed_date = datetime.strptime(date_value, fmt)
                            break
                        except ValueError:
                            continue
                    
                    # Check if it's a weekend
                    if parsed_date and parsed_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                        # Parse time (handle multiple formats)
                        parsed_time = None
                        for fmt in ['%H:%M', '%I:%M %p', '%H:%M:%S']:
                            try:
                                parsed_time = datetime.strptime(time_value, fmt).time()
                                break
                            except ValueError:
                                continue
                        
                        # Check if time is outside typical business hours (e.g., before 9am or after 9pm)
                        if parsed_time and (parsed_time.hour < 9 or parsed_time.hour >= 21):
                            issues.append({
                                'issue_type': 'SUSPICIOUS_AMOUNT',
                                'severity': 'INFO',
                                'description': f'Weekend transaction outside typical business hours: {time_value} on {date_value}'
                            })
                except ValueError:
                    pass
    
    except (ValueError, TypeError) as e:
        issues.append({
            'issue_type': 'SUSPICIOUS_AMOUNT',
            'severity': 'INFO',
            'description': f'Error in business rule validation: {str(e)}'
        })
    
    return issues

def validate_data_quality(extracted_data):
    """Validate data quality"""
    issues = []
    
    # Check for missing critical fields
    critical_fields = ['vendor', 'merchant_name', 'date', 'total']
    missing_fields = []
    
    for field in critical_fields:
        if field in extracted_data and not extracted_data[field].get('value'):
            missing_fields.append(field)
        elif field not in extracted_data:
            missing_fields.append(field)
    
    if missing_fields:
        issues.append({
            'issue_type': 'MISSING_DATA',
            'severity': 'ERROR' if 'total' in missing_fields or 'date' in missing_fields else 'WARNING',
            'description': f'Missing critical fields: {", ".join(missing_fields)}'
        })
    
    # Check for low confidence OCR extractions
    low_confidence_fields = []
    for field_name, field_data in extracted_data.items():
        confidence = field_data.get('confidence', 0)
        if confidence < 0.70 and field_data.get('value'):  # Only check fields that have values
            low_confidence_fields.append(f"{field_name} ({confidence:.2f})")
    
    if low_confidence_fields:
        issues.append({
            'issue_type': 'LOW_CONFIDENCE',
            'severity': 'WARNING',
            'description': f'Low confidence OCR extractions: {", ".join(low_confidence_fields)}'
        })
    
    # Check for malformed data
    # Check for negative amounts
    amount_fields = ['total', 'subtotal', 'tax', 'tip']
    negative_amounts = []
    
    for field in amount_fields:
        if field in extracted_data and extracted_data[field].get('value'):
            try:
                value = float(extracted_data[field]['value'])
                if value < 0:
                    negative_amounts.append(field)
            except (ValueError, TypeError):
                # This would be caught by another validation
                pass
    
    if negative_amounts:
        issues.append({
            'issue_type': 'MISSING_DATA',
            'severity': 'ERROR',
            'description': f'Negative amounts detected in fields: {", ".join(negative_amounts)}'
        })
    
    # Check for invalid date formats
    if 'date' in extracted_data and extracted_data['date'].get('value'):
        date_value = extracted_data['date']['value']
        valid_formats = ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d-%m-%Y']
        is_valid = False
        
        for fmt in valid_formats:
            try:
                datetime.strptime(date_value, fmt)
                is_valid = True
                break
            except ValueError:
                continue
        
        if not is_valid:
            issues.append({
                'issue_type': 'MISSING_DATA',
                'severity': 'WARNING',
                'description': f'Invalid date format: {date_value}'
            })
    
    return issues

def get_validation_summary(document_id):
    """Get a summary of validation issues for a document"""
    issues = get_validation_issues(document_id)
    
    summary = {
        'total_issues': len(issues),
        'errors': 0,
        'warnings': 0,
        'info': 0,
        'unacknowledged': 0,
        'issues_by_type': {}
    }
    
    for issue in issues:
        # Count by severity
        severity = issue['severity'].lower()
        if severity in summary:
            summary[severity] += 1
        
        # Count unacknowledged
        if not issue.get('acknowledged', False):
            summary['unacknowledged'] += 1
        
        # Count by type
        issue_type = issue['issue_type']
        if issue_type not in summary['issues_by_type']:
            summary['issues_by_type'][issue_type] = 0
        summary['issues_by_type'][issue_type] += 1
    
    return summary
import sqlite3
import os
from config import Config

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'uploaded',
            document_type TEXT DEFAULT 'unknown'  -- 'invoice' or 'receipt'
        )
    ''')
    
    # Create extractions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS extractions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            field_name TEXT NOT NULL,
            field_value TEXT,
            confidence_score REAL,
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
    ''')
    
    # Create corrections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS corrections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            extraction_id INTEGER NOT NULL,
            original_value TEXT,
            corrected_value TEXT,
            correction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (extraction_id) REFERENCES extractions (id)
        )
    ''')
    
    # Create users table for simple authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Create receipt_items table for receipt-specific line items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS receipt_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            item_name TEXT,
            quantity REAL,
            unit_price REAL,
            total_price REAL,
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
    ''')
    
    # Create receipt_details table for receipt-specific details
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS receipt_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            merchant_name TEXT,
            location TEXT,
            payment_method TEXT,
            tip_amount REAL,
            subtotal REAL,
            tax_amount REAL,
            total_amount REAL,
            cashier_name TEXT,
            transaction_time TEXT,
            category TEXT,
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
    ''')
    
    # Create a default admin user if none exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Default user: admin / password
        import hashlib
        password_hash = hashlib.sha256('password'.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ('admin', password_hash)
        )
    
    conn.commit()
    conn.close()

def insert_document(filename, document_type='unknown'):
    """Insert a new document record"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO documents (filename, document_type) VALUES (?, ?)",
        (filename, document_type)
    )
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def update_document_status(doc_id, status):
    """Update document status"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE documents SET status = ? WHERE id = ?",
        (status, doc_id)
    )
    conn.commit()
    conn.close()

def insert_extraction(document_id, field_name, field_value, confidence_score):
    """Insert an extraction result"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO extractions (document_id, field_name, field_value, confidence_score) VALUES (?, ?, ?, ?)",
        (document_id, field_name, field_value, confidence_score)
    )
    extraction_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return extraction_id

def get_document_extractions(document_id):
    """Get all extractions for a document"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM extractions WHERE document_id = ?",
        (document_id,)
    )
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def get_document_history():
    """Get processing history"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.id, d.filename, d.upload_date, d.status, 
               COUNT(e.id) as extraction_count
        FROM documents d
        LEFT JOIN extractions e ON d.id = e.document_id
        GROUP BY d.id
        ORDER BY d.upload_date DESC
    ''')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def insert_correction(extraction_id, original_value, corrected_value):
    """Insert a correction"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO corrections (extraction_id, original_value, corrected_value) VALUES (?, ?, ?)",
        (extraction_id, original_value, corrected_value)
    )
    correction_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return correction_id

def authenticate_user(username, password):
    """Authenticate a user"""
    import hashlib
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password_hash = ?",
        (username, password_hash)
    )
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def insert_receipt_item(document_id, item_name, quantity, unit_price, total_price):
    """Insert a receipt item"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO receipt_items (document_id, item_name, quantity, unit_price, total_price) VALUES (?, ?, ?, ?, ?)",
        (document_id, item_name, quantity, unit_price, total_price)
    )
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return item_id

def get_receipt_items(document_id):
    """Get all receipt items for a document"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM receipt_items WHERE document_id = ?",
        (document_id,)
    )
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def insert_receipt_details(document_id, merchant_name=None, location=None, payment_method=None, 
                          tip_amount=None, subtotal=None, tax_amount=None, total_amount=None, 
                          cashier_name=None, transaction_time=None, category=None):
    """Insert receipt details"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO receipt_details 
           (document_id, merchant_name, location, payment_method, tip_amount, 
            subtotal, tax_amount, total_amount, cashier_name, transaction_time, category) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (document_id, merchant_name, location, payment_method, tip_amount, 
         subtotal, tax_amount, total_amount, cashier_name, transaction_time, category)
    )
    details_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return details_id

def get_receipt_details(document_id):
    """Get receipt details for a document"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM receipt_details WHERE document_id = ?",
        (document_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None

def update_document_type(doc_id, document_type):
    """Update document type"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE documents SET document_type = ? WHERE id = ?",
        (document_type, doc_id)
    )
    conn.commit()
    conn.close()

def get_document_type(doc_id):
    """Get document type"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT document_type FROM documents WHERE id = ?",
        (doc_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 'unknown'

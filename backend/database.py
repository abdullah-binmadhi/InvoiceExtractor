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
            document_type TEXT DEFAULT 'unknown',  -- 'invoice' or 'receipt'
            batch_id INTEGER DEFAULT NULL,  -- Link to batch_jobs table
            FOREIGN KEY (batch_id) REFERENCES batch_jobs (id)
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
    
    # Create batch_jobs table for batch processing
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',  -- pending, processing, completed, failed
            total_files INTEGER DEFAULT 0,
            processed_files INTEGER DEFAULT 0,
            failed_files INTEGER DEFAULT 0,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_date TIMESTAMP NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
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

def insert_document(filename, document_type='unknown', batch_id=None):
    """Insert a new document record"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO documents (filename, document_type, batch_id) VALUES (?, ?, ?)",
        (filename, document_type, batch_id)
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

def insert_batch_job(user_id, total_files):
    """Insert a new batch job record"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO batch_jobs (user_id, total_files) VALUES (?, ?)",
        (user_id, total_files)
    )
    batch_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return batch_id

def update_batch_status(batch_id, status, processed_files=None, failed_files=None):
    """Update batch job status"""
    conn = get_db()
    cursor = conn.cursor()
    
    if status == 'completed':
        cursor.execute(
            "UPDATE batch_jobs SET status = ?, processed_files = ?, failed_files = ?, completed_date = CURRENT_TIMESTAMP WHERE id = ?",
            (status, processed_files, failed_files, batch_id)
        )
    else:
        if processed_files is not None and failed_files is not None:
            cursor.execute(
                "UPDATE batch_jobs SET status = ?, processed_files = ?, failed_files = ? WHERE id = ?",
                (status, processed_files, failed_files, batch_id)
            )
        elif processed_files is not None:
            cursor.execute(
                "UPDATE batch_jobs SET status = ?, processed_files = ? WHERE id = ?",
                (status, processed_files, batch_id)
            )
        elif failed_files is not None:
            cursor.execute(
                "UPDATE batch_jobs SET status = ?, failed_files = ? WHERE id = ?",
                (status, failed_files, batch_id)
            )
        else:
            cursor.execute(
                "UPDATE batch_jobs SET status = ? WHERE id = ?",
                (status, batch_id)
            )
    
    conn.commit()
    conn.close()

def get_batch_job(batch_id):
    """Get batch job details"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM batch_jobs WHERE id = ?",
        (batch_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None

def get_batch_documents(batch_id):
    """Get all documents in a batch"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM documents WHERE batch_id = ?",
        (batch_id,)
    )
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def get_batch_history(user_id):
    """Get batch processing history for a user"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT bj.*, u.username
        FROM batch_jobs bj
        JOIN users u ON bj.user_id = u.id
        WHERE bj.user_id = ?
        ORDER BY bj.created_date DESC
    ''', (user_id,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

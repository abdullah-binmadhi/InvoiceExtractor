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
            status TEXT DEFAULT 'uploaded'
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

def insert_document(filename):
    """Insert a new document record"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO documents (filename) VALUES (?)",
        (filename,)
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
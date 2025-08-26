import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-for-invoice-extractor'
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'invoice_extractor.db')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size (for batch uploads)
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'zip'}
    BATCH_MAX_FILES = 20  # Maximum files per batch
    BATCH_MAX_SIZE = 50 * 1024 * 1024  # 50MB total size limit for batch
    
    # Create upload folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
@echo off
echo Setting up InvoiceExtractor...

echo Setting up backend...
cd backend

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Please ensure you have installed:
echo 1. Tesseract OCR - https://github.com/UB-Mannheim/tesseract/wiki
echo 2. Poppler - https://github.com/oschwartz10612/poppler-windows/releases/
echo.

echo Backend setup complete!
echo To run the backend:
echo 1. cd backend
echo 2. call venv\Scripts\activate
echo 3. python app.py

echo.
echo Setting up frontend...
cd ..\frontend

echo Frontend setup complete!
echo To run the frontend:
echo 1. cd frontend
echo 2. python -m http.server 8000
echo 3. Open http://localhost:8000 in your browser

echo.
echo Deployment script completed!
pause
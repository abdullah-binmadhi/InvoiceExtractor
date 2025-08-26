#!/bin/bash

# Install system dependencies
apt-get update
apt-get install -y tesseract-ocr poppler-utils

# Install Python dependencies (this will be done automatically by Render)
pip install -r backend/requirements.txt
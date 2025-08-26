// DOM Elements
const uploadSection = document.getElementById('upload-section');
const resultsSection = document.getElementById('results-section');
const historySection = document.getElementById('history-section');
const uploadBtn = document.getElementById('upload-btn');
const historyBtn = document.getElementById('history-btn');
const dropArea = document.getElementById('drop-area');
const fileInput = document.getElementById('file-input');
const browseBtn = document.getElementById('browse-btn');
const progressContainer = document.getElementById('progress-container');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const resultsContainer = document.getElementById('results-container');
const historyContainer = document.getElementById('history-container');
const exportJsonBtn = document.getElementById('export-json');
const exportCsvBtn = document.getElementById('export-csv');
const saveCorrectionsBtn = document.getElementById('save-corrections');

// State
let currentDocumentId = null;
let extractedData = {};

// Navigation
function showSection(section) {
    // Hide all sections
    uploadSection.classList.remove('active');
    resultsSection.classList.remove('active');
    historySection.classList.remove('active');
    
    // Show selected section
    section.classList.add('active');
}

// Event Listeners
uploadBtn.addEventListener('click', () => showSection(uploadSection));
historyBtn.addEventListener('click', () => {
    showSection(historySection);
    loadHistory();
});

browseBtn.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', handleFileSelect);

dropArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropArea.classList.add('dragover');
});

dropArea.addEventListener('dragleave', () => {
    dropArea.classList.remove('dragover');
});

dropArea.addEventListener('drop', (e) => {
    e.preventDefault();
    dropArea.classList.remove('dragover');
    
    if (e.dataTransfer.files.length) {
        handleFiles(e.dataTransfer.files);
    }
});

dropArea.addEventListener('click', () => fileInput.click());

exportJsonBtn.addEventListener('click', () => exportResults('json'));
exportCsvBtn.addEventListener('click', () => exportResults('csv'));
saveCorrectionsBtn.addEventListener('click', saveCorrections);

// File Handling
function handleFileSelect(e) {
    if (e.target.files.length) {
        handleFiles(e.target.files);
    }
}

function handleFiles(files) {
    const file = files[0];
    if (!file) return;
    
    // Check file type
    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg'];
    if (!allowedTypes.includes(file.type)) {
        alert('Please upload a PDF, PNG, or JPG file.');
        return;
    }
    
    // Check file size (5MB limit)
    if (file.size > 5 * 1024 * 1024) {
        alert('File size exceeds 5MB limit.');
        return;
    }
    
    uploadFile(file);
}

// API Functions
async function uploadFile(file) {
    // Show progress
    showSection(uploadSection);
    progressContainer.classList.remove('hidden');
    progressFill.style.width = '0%';
    progressText.textContent = 'Uploading...';
    
    // Create FormData
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        // Simulate progress
        simulateProgress(10, 30, 'Uploading...');
        
        // Upload file
        const response = await fetch('http://localhost:5000/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        // Simulate processing progress
        simulateProgress(30, 90, 'Processing document...');
        
        const data = await response.json();
        
        // Complete progress
        progressFill.style.width = '100%';
        progressText.textContent = 'Complete!';
        
        // Store document ID and data
        currentDocumentId = data.id;
        extractedData = data.results;
        
        // Show results after a short delay
        setTimeout(() => {
            displayResults(data.results);
            showSection(resultsSection);
        }, 500);
        
    } catch (error) {
        console.error('Upload error:', error);
        progressText.textContent = `Error: ${error.message}`;
        setTimeout(() => {
            progressContainer.classList.add('hidden');
        }, 3000);
    }
}

function simulateProgress(start, end, text) {
    let progress = start;
    const interval = setInterval(() => {
        progress += 1;
        progressFill.style.width = `${progress}%`;
        progressText.textContent = text;
        
        if (progress >= end) {
            clearInterval(interval);
        }
    }, 50);
}

function displayResults(results) {
    resultsContainer.innerHTML = '';
    
    // Display each extracted field
    for (const [field, data] of Object.entries(results)) {
        if (field === 'line_items') {
            // Special handling for line items
            const itemDiv = document.createElement('div');
            itemDiv.className = 'result-item';
            
            const label = document.createElement('div');
            label.className = 'result-label';
            label.textContent = 'Line Items';
            itemDiv.appendChild(label);
            
            if (data.value && Array.isArray(data.value)) {
                const table = document.createElement('table');
                table.style.width = '100%';
                table.style.borderCollapse = 'collapse';
                table.style.marginTop = '0.5rem';
                
                // Header
                const header = table.createTHead();
                const headerRow = header.insertRow();
                const descHeader = headerRow.insertCell();
                descHeader.textContent = 'Description';
                descHeader.style.fontWeight = 'bold';
                descHeader.style.borderBottom = '1px solid #ddd';
                descHeader.style.padding = '0.5rem';
                const amountHeader = headerRow.insertCell();
                amountHeader.textContent = 'Amount';
                amountHeader.style.fontWeight = 'bold';
                amountHeader.style.borderBottom = '1px solid #ddd';
                amountHeader.style.padding = '0.5rem';
                
                // Rows
                const tbody = table.createTBody();
                data.value.forEach(item => {
                    const row = tbody.insertRow();
                    const descCell = row.insertCell();
                    descCell.textContent = item.description || '';
                    descCell.style.borderBottom = '1px solid #eee';
                    descCell.style.padding = '0.5rem';
                    const amountCell = row.insertCell();
                    amountCell.textContent = item.amount || '';
                    amountCell.style.borderBottom = '1px solid #eee';
                    amountCell.style.padding = '0.5rem';
                });
                
                itemDiv.appendChild(table);
            } else {
                const valueInput = document.createElement('input');
                valueInput.type = 'text';
                valueInput.className = 'result-value';
                valueInput.id = `field-${field}`;
                valueInput.value = data.value || '';
                valueInput.dataset.field = field;
                itemDiv.appendChild(valueInput);
            }
            
            resultsContainer.appendChild(itemDiv);
        } else {
            // Regular fields
            const itemDiv = document.createElement('div');
            itemDiv.className = 'result-item';
            
            const label = document.createElement('div');
            label.className = 'result-label';
            label.textContent = formatFieldName(field);
            itemDiv.appendChild(label);
            
            const valueInput = document.createElement('input');
            valueInput.type = 'text';
            valueInput.className = 'result-value';
            valueInput.id = `field-${field}`;
            valueInput.value = data.value || '';
            valueInput.dataset.field = field;
            itemDiv.appendChild(valueInput);
            
            resultsContainer.appendChild(itemDiv);
        }
    }
}

function formatFieldName(field) {
    // Convert snake_case to Title Case
    return field
        .replace(/_/g, ' ')
        .replace(/\b\w/g, char => char.toUpperCase());
}

async function loadHistory() {
    try {
        const response = await fetch('http://localhost:5000/api/history');
        if (!response.ok) {
            throw new Error(`Failed to load history: ${response.statusText}`);
        }
        
        const history = await response.json();
        displayHistory(history);
    } catch (error) {
        console.error('History load error:', error);
        historyContainer.innerHTML = `<p>Error loading history: ${error.message}</p>`;
    }
}

function displayHistory(history) {
    historyContainer.innerHTML = '';
    
    if (!history.length) {
        historyContainer.innerHTML = '<p>No processing history found.</p>';
        return;
    }
    
    history.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'history-item';
        
        const headerDiv = document.createElement('div');
        headerDiv.className = 'history-header';
        headerDiv.innerHTML = `
            <span>Document #${item.id}</span>
            <span class="status ${item.status}">${item.status}</span>
        `;
        itemDiv.appendChild(headerDiv);
        
        const detailsDiv = document.createElement('div');
        detailsDiv.className = 'history-details';
        detailsDiv.innerHTML = `
            <span>${item.filename}</span>
            <span>${new Date(item.upload_date).toLocaleString()}</span>
        `;
        itemDiv.appendChild(detailsDiv);
        
        historyContainer.appendChild(itemDiv);
    });
}

async function exportResults(format) {
    if (!currentDocumentId) return;
    
    try {
        const response = await fetch(`http://localhost:5000/api/export/${currentDocumentId}/${format}`);
        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }
        
        if (format === 'json') {
            const data = await response.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `invoice_${currentDocumentId}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } else if (format === 'csv') {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `invoice_${currentDocumentId}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    } catch (error) {
        console.error('Export error:', error);
        alert(`Export failed: ${error.message}`);
    }
}

async function saveCorrections() {
    if (!currentDocumentId) return;
    
    // Collect corrections from input fields
    const corrections = {};
    const inputs = resultsContainer.querySelectorAll('.result-value');
    
    inputs.forEach(input => {
        const field = input.dataset.field;
        const value = input.value;
        corrections[field] = value;
    });
    
    try {
        const response = await fetch(`http://localhost:5000/api/correct/${currentDocumentId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(corrections)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to save corrections: ${response.statusText}`);
        }
        
        const data = await response.json();
        alert('Corrections saved successfully!');
    } catch (error) {
        console.error('Save corrections error:', error);
        alert(`Failed to save corrections: ${error.message}`);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the results page with data
    // In a real app, you might use URL parameters or local storage
});
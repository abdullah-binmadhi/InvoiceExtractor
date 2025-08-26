// DOM Elements
const uploadSection = document.getElementById('upload-section');
const batchUploadSection = document.getElementById('batch-upload-section');
const resultsSection = document.getElementById('results-section');
const batchResultsSection = document.getElementById('batch-results-section');
const historySection = document.getElementById('history-section');
const batchHistorySection = document.getElementById('batch-history-section');
const validationModal = document.getElementById('validation-modal');

const uploadBtn = document.getElementById('upload-btn');
const batchUploadBtn = document.getElementById('batch-upload-btn');
const historyBtn = document.getElementById('history-btn');
const batchHistoryBtn = document.getElementById('batch-history-btn');

const dropArea = document.getElementById('drop-area');
const batchDropArea = document.getElementById('batch-drop-area');
const fileInput = document.getElementById('file-input');
const batchFileInput = document.getElementById('batch-file-input');
const browseBtn = document.getElementById('browse-btn');
const batchBrowseBtn = document.getElementById('batch-browse-btn');

const progressContainer = document.getElementById('progress-container');
const batchProgressContainer = document.getElementById('batch-progress-container');
const progressFill = document.getElementById('progress-fill');
const batchProgressFill = document.getElementById('batch-progress-fill');
const progressText = document.getElementById('progress-text');
const batchProgressText = document.getElementById('batch-progress-text');
const batchProgressDetails = document.getElementById('batch-progress-details');

const resultsContainer = document.getElementById('results-container');
const batchResultsContainer = document.getElementById('batch-results-container');
const historyContainer = document.getElementById('history-container');
const batchHistoryContainer = document.getElementById('batch-history-container');
const validationAlerts = document.getElementById('validation-alerts');
const validationSummary = document.getElementById('validation-summary');
const validationIssuesList = document.getElementById('validation-issues-list');
const viewValidationReportBtn = document.getElementById('view-validation-report');

const exportJsonBtn = document.getElementById('export-json');
const exportCsvBtn = document.getElementById('export-csv');
const exportBatchJsonBtn = document.getElementById('export-batch-json');
const exportBatchCsvBtn = document.getElementById('export-batch-csv');
const saveCorrectionsBtn = document.getElementById('save-corrections');
const acknowledgeAllBtn = document.getElementById('acknowledge-all-btn');

const documentTypeIndicator = document.querySelector('.document-type-indicator');
const expenseCategorySelect = document.getElementById('expense-category');

const batchIdElement = document.getElementById('batch-id');
const totalFilesElement = document.getElementById('total-files');
const processedFilesElement = document.getElementById('processed-files');
const failedFilesElement = document.getElementById('failed-files');

// Modal elements
const closeModalButtons = document.querySelectorAll('.close-modal, .close-modal-btn');

// State
let currentDocumentId = null;
let currentBatchId = null;
let extractedData = {};
let documentType = 'unknown';
let validationIssues = [];

// Navigation
function showSection(section) {
    // Hide all sections
    uploadSection.classList.remove('active');
    batchUploadSection.classList.remove('active');
    resultsSection.classList.remove('active');
    batchResultsSection.classList.remove('active');
    historySection.classList.remove('active');
    batchHistorySection.classList.remove('active');
    
    // Show selected section
    section.classList.add('active');
}

// Event Listeners
uploadBtn.addEventListener('click', () => showSection(uploadSection));
batchUploadBtn.addEventListener('click', () => showSection(batchUploadSection));
historyBtn.addEventListener('click', () => {
    showSection(historySection);
    loadHistory();
});
batchHistoryBtn.addEventListener('click', () => {
    showSection(batchHistorySection);
    loadBatchHistory();
});

browseBtn.addEventListener('click', () => fileInput.click());
batchBrowseBtn.addEventListener('click', () => batchFileInput.click());

fileInput.addEventListener('change', handleFileSelect);
batchFileInput.addEventListener('change', handleBatchFileSelect);

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

batchDropArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    batchDropArea.classList.add('dragover');
});

batchDropArea.addEventListener('dragleave', () => {
    batchDropArea.classList.remove('dragover');
});

batchDropArea.addEventListener('drop', (e) => {
    e.preventDefault();
    batchDropArea.classList.remove('dragover');
    
    if (e.dataTransfer.files.length) {
        handleBatchFiles(e.dataTransfer.files);
    }
});

dropArea.addEventListener('click', () => fileInput.click());
batchDropArea.addEventListener('click', () => batchFileInput.click());

exportJsonBtn.addEventListener('click', () => exportResults('json'));
exportCsvBtn.addEventListener('click', () => exportResults('csv'));
exportBatchJsonBtn.addEventListener('click', () => exportBatchResults('json'));
exportBatchCsvBtn.addEventListener('click', () => exportBatchResults('csv'));
saveCorrectionsBtn.addEventListener('click', saveCorrections);
viewValidationReportBtn.addEventListener('click', showValidationModal);

// Modal event listeners
closeModalButtons.forEach(button => {
    button.addEventListener('click', () => {
        validationModal.classList.add('hidden');
    });
});

acknowledgeAllBtn.addEventListener('click', acknowledgeAllWarnings);

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target === validationModal) {
        validationModal.classList.add('hidden');
    }
});

// File Handling
function handleFileSelect(e) {
    if (e.target.files.length) {
        handleFiles(e.target.files);
    }
}

function handleBatchFileSelect(e) {
    if (e.target.files.length) {
        handleBatchFiles(e.target.files);
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

function handleBatchFiles(files) {
    if (files.length === 0) return;
    
    // Check batch size limits
    if (files.length > 20) {
        alert('Maximum 20 files allowed per batch.');
        return;
    }
    
    // Check total size (50MB limit)
    let totalSize = 0;
    for (let file of files) {
        totalSize += file.size;
    }
    
    if (totalSize > 50 * 1024 * 1024) {
        alert('Total batch size exceeds 50MB limit.');
        return;
    }
    
    // Check file types
    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'application/zip'];
    for (let file of files) {
        if (!allowedTypes.includes(file.type)) {
            alert(`File ${file.name} has an unsupported type. Only PDF, PNG, JPG, and ZIP files are allowed.`);
            return;
        }
    }
    
    uploadBatchFiles(files);
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
        const response = await fetch(`${window.APP_CONFIG.apiUrl}/api/upload`, {
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
        documentType = data.document_type;
        extractedData = data.results;
        
        // Show results after a short delay
        setTimeout(() => {
            displayResults(data.results);
            loadValidationIssues(data.id);
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

async function uploadBatchFiles(files) {
    // Show batch progress
    showSection(batchUploadSection);
    batchProgressContainer.classList.remove('hidden');
    batchProgressFill.style.width = '0%';
    batchProgressText.textContent = 'Uploading batch...';
    batchProgressDetails.innerHTML = '';
    
    // Create FormData
    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }
    
    try {
        // Upload batch
        const response = await fetch(`${window.APP_CONFIG.apiUrl}/api/upload-batch`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Batch upload failed: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Store batch ID
        currentBatchId = data.batch_id;
        
        // Show batch results
        displayBatchResults(data.batch_id);
        
    } catch (error) {
        console.error('Batch upload error:', error);
        batchProgressText.textContent = `Error: ${error.message}`;
        setTimeout(() => {
            batchProgressContainer.classList.add('hidden');
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
    
    // Update document type indicator
    const docType = results.document_type?.value || 'unknown';
    documentTypeIndicator.querySelector('strong').textContent = 
        docType.charAt(0).toUpperCase() + docType.slice(1);
    documentTypeIndicator.className = 'document-type-indicator ' + docType;
    
    // Display each extracted field
    for (const [field, data] of Object.entries(results)) {
        // Skip document_type as it's displayed separately
        if (field === 'document_type') continue;
        
        if (field === 'line_items') {
            // Special handling for line items
            const itemDiv = document.createElement('div');
            itemDiv.className = 'result-item';
            
            const label = document.createElement('div');
            label.className = 'result-label';
            label.textContent = docType === 'receipt' ? 'Receipt Items' : 'Line Items';
            itemDiv.appendChild(label);
            
            if (data.value && Array.isArray(data.value)) {
                const table = document.createElement('table');
                table.style.width = '100%';
                table.style.borderCollapse = 'collapse';
                table.style.marginTop = '0.5rem';
                
                if (docType === 'receipt') {
                    // Receipt items with quantity, unit price, total
                    // Header
                    const header = table.createTHead();
                    const headerRow = header.insertRow();
                    const nameHeader = headerRow.insertCell();
                    nameHeader.textContent = 'Item';
                    nameHeader.style.fontWeight = 'bold';
                    nameHeader.style.borderBottom = '1px solid #ddd';
                    nameHeader.style.padding = '0.5rem';
                    const qtyHeader = headerRow.insertCell();
                    qtyHeader.textContent = 'Qty';
                    qtyHeader.style.fontWeight = 'bold';
                    qtyHeader.style.borderBottom = '1px solid #ddd';
                    qtyHeader.style.padding = '0.5rem';
                    const priceHeader = headerRow.insertCell();
                    priceHeader.textContent = 'Unit Price';
                    priceHeader.style.fontWeight = 'bold';
                    priceHeader.style.borderBottom = '1px solid #ddd';
                    priceHeader.style.padding = '0.5rem';
                    const totalHeader = headerRow.insertCell();
                    totalHeader.textContent = 'Total';
                    totalHeader.style.fontWeight = 'bold';
                    totalHeader.style.borderBottom = '1px solid #ddd';
                    totalHeader.style.padding = '0.5rem';
                    
                    // Rows
                    const tbody = table.createTBody();
                    for (const item of data.value) {
                        const row = tbody.insertRow();
                        const nameCell = row.insertCell();
                        nameCell.textContent = item.item_name || '';
                        nameCell.style.padding = '0.5rem';
                        nameCell.style.borderBottom = '1px solid #eee';
                        const qtyCell = row.insertCell();
                        qtyCell.textContent = item.quantity || '';
                        qtyCell.style.padding = '0.5rem';
                        qtyCell.style.borderBottom = '1px solid #eee';
                        qtyCell.style.textAlign = 'right';
                        const priceCell = row.insertCell();
                        priceCell.textContent = item.unit_price ? `$${parseFloat(item.unit_price).toFixed(2)}` : '';
                        priceCell.style.padding = '0.5rem';
                        priceCell.style.borderBottom = '1px solid #eee';
                        priceCell.style.textAlign = 'right';
                        const totalCell = row.insertCell();
                        totalCell.textContent = item.total_price ? `$${parseFloat(item.total_price).toFixed(2)}` : '';
                        totalCell.style.padding = '0.5rem';
                        totalCell.style.borderBottom = '1px solid #eee';
                        totalCell.style.textAlign = 'right';
                    }
                } else {
                    // Invoice line items
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
                    for (const item of data.value) {
                        const row = tbody.insertRow();
                        const descCell = row.insertCell();
                        descCell.textContent = item.description || item.item_name || '';
                        descCell.style.padding = '0.5rem';
                        descCell.style.borderBottom = '1px solid #eee';
                        const amountCell = row.insertCell();
                        amountCell.textContent = item.amount || item.total_price ? `$${parseFloat(item.amount || item.total_price).toFixed(2)}` : '';
                        amountCell.style.padding = '0.5rem';
                        amountCell.style.borderBottom = '1px solid #eee';
                        amountCell.style.textAlign = 'right';
                    }
                }
                
                itemDiv.appendChild(table);
            } else {
                const valueDiv = document.createElement('div');
                valueDiv.className = 'result-value';
                valueDiv.textContent = 'No items found';
                itemDiv.appendChild(valueDiv);
            }
            
            resultsContainer.appendChild(itemDiv);
        } else {
            // Regular field
            const itemDiv = document.createElement('div');
            itemDiv.className = 'result-item';
            
            const label = document.createElement('div');
            label.className = 'result-label';
            
            // Format field name for display
            const formattedFieldName = field.replace(/_/g, ' ')
                .replace(/\b\w/g, l => l.toUpperCase());
            label.textContent = formattedFieldName;
            itemDiv.appendChild(label);
            
            const valueDiv = document.createElement('div');
            valueDiv.className = 'result-value';
            
            // Format value for display
            let displayValue = data.value;
            if (field.includes('amount') || field.includes('price') || field.includes('total')) {
                if (displayValue && !isNaN(displayValue)) {
                    displayValue = `$${parseFloat(displayValue).toFixed(2)}`;
                }
            }
            
            // Add confidence indicator
            if (data.confidence !== undefined) {
                const confidenceSpan = document.createElement('span');
                confidenceSpan.className = 'confidence';
                confidenceSpan.textContent = ` (${(data.confidence * 100).toFixed(0)}%)`;
                confidenceSpan.style.fontSize = '0.8em';
                confidenceSpan.style.color = data.confidence > 0.8 ? 'green' : data.confidence > 0.5 ? 'orange' : 'red';
                valueDiv.innerHTML = `${displayValue || 'N/A'} `;
                valueDiv.appendChild(confidenceSpan);
            } else {
                valueDiv.textContent = displayValue || 'N/A';
            }
            
            itemDiv.appendChild(valueDiv);
            resultsContainer.appendChild(itemDiv);
        }
    }
    
    // Set expense category if available
    if (results.category?.value) {
        expenseCategorySelect.value = results.category.value;
    }
}

async function loadValidationIssues(documentId) {
    try {
        const response = await fetch(`${window.APP_CONFIG.apiUrl}/api/validation-summary/${documentId}`);
        if (!response.ok) {
            throw new Error('Failed to load validation issues');
        }
        
        const summary = await response.json();
        
        if (summary.total_issues > 0) {
            validationAlerts.classList.remove('hidden');
            
            // Set alert style based on severity
            validationAlerts.className = 'validation-alerts';
            if (summary.errors > 0) {
                validationAlerts.classList.add('error');
            } else if (summary.warnings > 0) {
                validationAlerts.classList.add('warning');
            } else {
                validationAlerts.classList.add('info');
            }
            
            // Update summary text
            let summaryText = `${summary.total_issues} issue${summary.total_issues !== 1 ? 's' : ''} found`;
            if (summary.errors > 0) {
                summaryText += ` (${summary.errors} error${summary.errors !== 1 ? 's' : ''})`;
            }
            if (summary.warnings > 0) {
                summaryText += ` (${summary.warnings} warning${summary.warnings !== 1 ? 's' : ''})`;
            }
            if (summary.info > 0) {
                summaryText += ` (${summary.info} info)`;
            }
            
            validationSummary.textContent = summaryText;
            
            // Store validation issues for detailed view
            validationIssues = summary;
        } else {
            validationAlerts.classList.add('hidden');
        }
    } catch (error) {
        console.error('Error loading validation issues:', error);
        validationAlerts.classList.add('hidden');
    }
}

function showValidationModal() {
    // Populate validation issues list
    validationIssuesList.innerHTML = '';
    
    // This would typically fetch detailed issues from the API
    // For now, we'll just show the summary
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'validation-summary-detail';
    summaryDiv.innerHTML = `
        <h3>Validation Summary</h3>
        <p>Total Issues: ${validationIssues.total_issues}</p>
        <p>Errors: ${validationIssues.errors}</p>
        <p>Warnings: ${validationIssues.warnings}</p>
        <p>Info: ${validationIssues.info}</p>
        <p>Unacknowledged: ${validationIssues.unacknowledged}</p>
    `;
    validationIssuesList.appendChild(summaryDiv);
    
    // Show issues by type
    const issuesByTypeDiv = document.createElement('div');
    issuesByTypeDiv.className = 'validation-issues-by-type';
    issuesByTypeDiv.innerHTML = '<h3>Issues by Type</h3>';
    
    for (const [type, count] of Object.entries(validationIssues.issues_by_type)) {
        const typeDiv = document.createElement('div');
        typeDiv.className = 'validation-issue-type';
        typeDiv.innerHTML = `<strong>${type}:</strong> ${count}`;
        issuesByTypeDiv.appendChild(typeDiv);
    }
    
    validationIssuesList.appendChild(issuesByTypeDiv);
    
    validationModal.classList.remove('hidden');
}

async function acknowledgeIssue(issueId) {
    try {
        const response = await fetch(`${window.APP_CONFIG.apiUrl}/api/ignore-warning/${issueId}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to acknowledge issue: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Acknowledge error:', error);
        alert(`Failed to acknowledge issue: ${error.message}`);
    }
}

async function acknowledgeAllWarnings() {
    try {
        // Acknowledge all warning issues
        const warningIssues = validationIssues.filter(issue => issue.severity === 'WARNING');
        
        for (const issue of warningIssues) {
            await acknowledgeIssue(issue.id);
        }
        
        // Refresh the validation display
        showValidationModal();
        
        alert('All warnings acknowledged successfully!');
    } catch (error) {
        console.error('Acknowledge all error:', error);
        alert(`Failed to acknowledge all warnings: ${error.message}`);
    }
}

async function displayBatchResults(batchId) {
    try {
        // Fetch batch results
        const response = await fetch(`${window.APP_CONFIG.apiUrl}/api/batch-results/${batchId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch batch results: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Update batch summary
        batchIdElement.textContent = batchId;
        totalFilesElement.textContent = data.results.length;
        
        // Count processed and failed files
        let processedCount = 0;
        let failedCount = 0;
        
        data.results.forEach(result => {
            if (result.status === 'completed') {
                processedCount++;
            } else if (result.status === 'failed') {
                failedCount++;
            }
        });
        
        processedFilesElement.textContent = processedCount;
        failedFilesElement.textContent = failedCount;
        
        // Display results for each document
        batchResultsContainer.innerHTML = '';
        
        data.results.forEach(result => {
            const docDiv = document.createElement('div');
            docDiv.className = 'result-item';
            
            const header = document.createElement('div');
            header.className = 'history-header';
            header.innerHTML = `
                <span>${result.filename}</span>
                <span class="status ${result.status}">${result.status}</span>
            `;
            docDiv.appendChild(header);
            
            if (result.status === 'completed' && result.results) {
                const resultsDiv = document.createElement('div');
                resultsDiv.style.marginTop = '1rem';
                
                // Display key fields
                const fieldsToShow = ['merchant_name', 'vendor', 'total', 'date'];
                fieldsToShow.forEach(field => {
                    if (result.results[field] && result.results[field].value) {
                        const fieldDiv = document.createElement('div');
                        fieldDiv.style.marginBottom = '0.5rem';
                        fieldDiv.innerHTML = `
                            <strong>${formatFieldName(field)}:</strong> 
                            ${result.results[field].value}
                        `;
                        resultsDiv.appendChild(fieldDiv);
                    }
                });
                
                docDiv.appendChild(resultsDiv);
            }
            
            batchResultsContainer.appendChild(docDiv);
        });
        
        showSection(batchResultsSection);
        
    } catch (error) {
        console.error('Batch results error:', error);
        alert(`Failed to load batch results: ${error.message}`);
    }
}

function formatFieldName(field) {
    // Convert snake_case to Title Case
    const formatted = field
        .replace(/_/g, ' ')
        .replace(/\b\w/g, char => char.toUpperCase());
    
    // Special formatting for certain fields
    const fieldNames = {
        'merchant_name': 'Merchant Name',
        'receipt_number': 'Receipt Number',
        'payment_method': 'Payment Method',
        'cashier_name': 'Cashier Name',
        'tip': 'Tip Amount',
        'subtotal': 'Subtotal',
        'tax': 'Tax Amount',
        'total': 'Total Amount'
    };
    
    return fieldNames[field] || formatted;
}

async function loadHistory() {
    try {
        const response = await fetch(`${window.APP_CONFIG.apiUrl}/api/history`);
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

async function loadBatchHistory() {
    try {
        // For now, we'll simulate batch history
        // In a real implementation, this would fetch from the backend
        batchHistoryContainer.innerHTML = '<p>Batch history will be available in a future update.</p>';
    } catch (error) {
        console.error('Batch history load error:', error);
        batchHistoryContainer.innerHTML = `<p>Error loading batch history: ${error.message}</p>`;
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
        
        // Get document type for this item
        const docType = item.document_type || 'unknown';
        const typeTag = `<span class="document-type-tag ${docType}">${docType}</span>`;
        
        headerDiv.innerHTML = `
            <span>Document #${item.id} ${typeTag}</span>
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
        const response = await fetch(`${window.APP_CONFIG.apiUrl}/api/export/${currentDocumentId}/${format}`);
        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }
        
        if (format === 'json') {
            const data = await response.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `document_${currentDocumentId}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } else if (format === 'csv') {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `document_${currentDocumentId}.csv`;
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

async function exportBatchResults(format) {
    if (!currentBatchId) return;
    
    try {
        const response = await fetch(`${window.APP_CONFIG.apiUrl}/api/download-batch/${currentBatchId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ format: format })
        });
        
        if (!response.ok) {
            throw new Error(`Batch export failed: ${response.statusText}`);
        }
        
        if (format === 'json') {
            const data = await response.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `batch_${currentBatchId}_results.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } else if (format === 'csv') {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `batch_${currentBatchId}_results.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    } catch (error) {
        console.error('Batch export error:', error);
        alert(`Batch export failed: ${error.message}`);
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
    
    // Add expense category
    corrections['category'] = expenseCategorySelect.value;
    
    try {
        const response = await fetch(`${window.APP_CONFIG.apiUrl}/api/correct/${currentDocumentId}`, {
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
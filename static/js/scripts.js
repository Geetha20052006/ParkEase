// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Flash message auto-dismissal
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            // Create and trigger bootstrap dismiss
            const bsAlert = new bootstrap.Alert(alert);
            setTimeout(() => {
                bsAlert.close();
            }, 5000); // Auto dismiss after 5 seconds
        });
    }, 500);
    //added from here
    const startScannerBtn = document.getElementById('startScannerBtn');
if (startScannerBtn) {
    startScannerBtn.addEventListener('click', () => {
        const scannerContainer = document.getElementById('barcodeScanner');
        const resultDiv = document.getElementById('cameraResult');

        if (Quagga.initialized) {
            Quagga.stop();
            Quagga.initialized = false;
            startScannerBtn.textContent = "Scan Barcode with Camera";
            return;
        }

        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: scannerContainer,
                constraints: {
                    facingMode: "environment" // Rear camera
                }
            },
            decoder: {
                readers: ["code_128_reader", "ean_reader", "ean_8_reader", "upc_reader"]
            }
        }, function(err) {
            if (err) {
                console.error(err);
                resultDiv.innerHTML = '<div class="alert alert-danger">Failed to start scanner.</div>';
                return;
            }
            Quagga.start();
            Quagga.initialized = true;
            startScannerBtn.textContent = "Stop Scanner";
        });

        Quagga.onDetected(data => {
            const barcode = data.codeResult.code;
            resultDiv.innerHTML = `<div class="alert alert-info">Scanned: ${barcode}</div>`;

            // Auto fill barcode input and trigger verify
            document.getElementById('barcodeInput').value = barcode;
            document.getElementById('verifyBarcodeBtn').click();

            // Stop scanner
            Quagga.stop();
            Quagga.initialized = false;
            startScannerBtn.textContent = "Scan Barcode with Camera";
        });
    });
}
    //added till here

    // Entry QR generation
    const generateEntryQRBtn = document.getElementById('generateEntryQRBtn');
    if (generateEntryQRBtn) {
        generateEntryQRBtn.addEventListener('click', generateEntryQR);
    }

    // Exit QR generation
    const generateExitQRBtn = document.getElementById('generateExitQRBtn');
    if (generateExitQRBtn) {
        generateExitQRBtn.addEventListener('click', generateExitQR);
    }

    // Add funds form validation
    const addFundsForm = document.getElementById('addFundsForm');
    if (addFundsForm) {
        addFundsForm.addEventListener('submit', validateAddFunds);
    }

    // Bill verification success handling
    const proceedToExitBtn = document.getElementById('proceedToExitBtn');
    if (proceedToExitBtn) {
        proceedToExitBtn.addEventListener('click', function() {
            window.location.href = '/parking/exit';
        });
    }
});

// Generate entry QR code
function generateEntryQR() {
    // Show loading spinner
    const qrContainer = document.getElementById('qrContainer');
    qrContainer.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Generating QR code...</p></div>';
    
    // Disable button
    const generateBtn = document.getElementById('generateEntryQRBtn');
    generateBtn.disabled = true;
    
    // Make API request
    fetch('/generate_entry_qr', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Display QR code
            qrContainer.innerHTML = `
                <div class="text-center">
                    <div class="alert alert-success">
                        <strong>Success!</strong> Your parking slot number is <span class="badge bg-primary">${data.slot_number}</span>
                    </div>
                    <div class="card qr-card mb-3 mx-auto" style="max-width: 300px;">
                        <div class="card-header bg-primary text-white">
                            <strong>Entry QR Code</strong>
                        </div>
                        <div class="card-body p-3">
                            <img src="data:image/png;base64,${data.qr_code}" class="img-fluid" alt="Entry QR Code">
                        </div>
                        <div class="card-footer text-muted">
                            <small>Valid for 10 minutes</small>
                        </div>
                    </div>
                    <form action="/confirm_entry/${data.qr_id}" method="post">
                        <button type="submit" class="btn btn-success">Confirm Entry</button>
                    </form>
                </div>
            `;
        } else {
            // Display error
            qrContainer.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Error!</strong> ${data.message}
                </div>
                <button id="retryEntryQRBtn" class="btn btn-primary">Retry</button>
            `;
            
            // Add retry button listener
            document.getElementById('retryEntryQRBtn').addEventListener('click', generateEntryQR);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        qrContainer.innerHTML = `
            <div class="alert alert-danger">
                <strong>Error!</strong> An unexpected error occurred.
            </div>
            <button id="retryEntryQRBtn" class="btn btn-primary">Retry</button>
        `;
        
        // Add retry button listener
        document.getElementById('retryEntryQRBtn').addEventListener('click', generateEntryQR);
    })
    .finally(() => {
        // Re-enable button
        generateBtn.disabled = false;
    });
}

// Generate exit QR code
function generateExitQR() {
    // Get inputs
    const isFreeExit = document.getElementById('isFreeExit') ? 
                      document.getElementById('isFreeExit').value === 'true' : false;
    const charges = document.getElementById('parkingCharges') ? 
                  document.getElementById('parkingCharges').value : 0;
    
    // Show loading spinner
    const qrContainer = document.getElementById('exitQrContainer');
    qrContainer.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Generating QR code...</p></div>';
    
    // Disable button
    const generateBtn = document.getElementById('generateExitQRBtn');
    generateBtn.disabled = true;
    
    // Create form data
    const formData = new FormData();
    formData.append('is_free_exit', isFreeExit);
    formData.append('charges', charges);
    
    // Make API request
    fetch('/generate_exit_qr', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Display QR code
            qrContainer.innerHTML = `
                <div class="text-center">
                    <div class="alert alert-success">
                        <strong>Success!</strong> ${data.message}
                    </div>
                    <div class="card qr-card mb-3 mx-auto" style="max-width: 300px;">
                        <div class="card-header bg-primary text-white">
                            <strong>Exit QR Code</strong>
                        </div>
                        <div class="card-body p-3">
                            <img src="data:image/png;base64,${data.qr_code}" class="img-fluid" alt="Exit QR Code">
                        </div>
                        <div class="card-footer text-muted">
                            <small>Valid for 10 minutes</small>
                        </div>
                    </div>
                    <form action="/confirm_exit/${data.qr_id}" method="post">
                        <button type="submit" class="btn btn-success">Confirm Exit</button>
                    </form>
                </div>
            `;
        } else {
            // Display error
            qrContainer.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Error!</strong> ${data.message}
                </div>
                <button id="retryExitQRBtn" class="btn btn-primary">Retry</button>
            `;
            
            // Add retry button listener
            document.getElementById('retryExitQRBtn').addEventListener('click', generateExitQR);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        qrContainer.innerHTML = `
            <div class="alert alert-danger">
                <strong>Error!</strong> An unexpected error occurred.
            </div>
            <button id="retryExitQRBtn" class="btn btn-primary">Retry</button>
        `;
        
        // Add retry button listener
        document.getElementById('retryExitQRBtn').addEventListener('click', generateExitQR);
    })
    .finally(() => {
        // Re-enable button
        generateBtn.disabled = false;
    });
}

// Validate add funds form
function validateAddFunds(event) {
    const amountInput = document.getElementById('fundAmount');
    const amount = parseFloat(amountInput.value);
    
    if (isNaN(amount) || amount <= 0) {
        event.preventDefault();
        
        // Show error message
        const errorDiv = document.getElementById('amountError');
        errorDiv.textContent = 'Please enter a valid positive amount';
        errorDiv.classList.remove('d-none');
        
        // Focus on input
        amountInput.focus();
        return false;
    }
    
    // Clear error message
    const errorDiv = document.getElementById('amountError');
    errorDiv.textContent = '';
    errorDiv.classList.add('d-none');
    
    return true;
}

// Update real-time parking status for admin dashboard
function updateParkingStatus() {
    const statusContainer = document.getElementById('parkingStatusContainer');
    
    if (!statusContainer) return;
    
    // In a real application, we would fetch the latest status from the server
    // For now, this is just a placeholder
    
    // Count available and occupied slots
    const availableSlots = document.querySelectorAll('.slot-available').length;
    const occupiedSlots = document.querySelectorAll('.slot-occupied').length;
    
    // Update the status
    const totalSlots = availableSlots + occupiedSlots;
    document.getElementById('totalSlots').textContent = totalSlots;
    document.getElementById('availableSlots').textContent = availableSlots;
    document.getElementById('occupiedSlots').textContent = occupiedSlots;
}

// Call updateParkingStatus when page loads
document.addEventListener('DOMContentLoaded', function() {
    updateParkingStatus();
    
    // Update status every 30 seconds
    setInterval(updateParkingStatus, 30000);
});

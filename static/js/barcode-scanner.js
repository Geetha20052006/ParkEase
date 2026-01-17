
// Barcode Scanner implementation using ZXing and mediaDevices API

// Global variables
let selectedDeviceId;
let codeReader;
let videoElement;

// Initialize the code reader when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the barcode scanner component if present on the page
    const barcodeScanner = document.getElementById('barcode-scanner');
    if (barcodeScanner) {
        initBarcodeScanner();
    }
});

async function initBarcodeScanner() {
    console.log('Initializing barcode scanner...');
    
    // Check if ZXing library is loaded
    if (typeof ZXing === 'undefined') {
        console.error('ZXing library not loaded');
        showError('Barcode scanning library not loaded. Please refresh the page or use the test mode below.');
        return;
    }
    
    // Check for camera support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.warn('Camera access not supported');
        showError("Your browser doesn't support camera access. Please use the test mode below.");
        return;
    }
    // added from here
    try {
        const devices = await ZXing.BrowserMultiFormatReader.listVideoInputDevices();
        if (devices.length === 0) {
            showError("No camera devices found.");
            return;
        }
        selectedDeviceId = devices[0].deviceId;
    } catch (err) {
        console.error("Camera initialization failed:", err);
        showError("Failed to access camera. Please check permissions.");
    }
    // added till here

    // Get reference to video element
    videoElement = document.getElementById('video');
    const startButton = document.getElementById('startScan');
    const stopButton = document.getElementById('stopScan');
    const resultContainer = document.getElementById('scanResult');
    const deviceSelect = document.getElementById('cameraSelect');
    
    try {
        // Create instance of BarcodeScanner
        codeReader = new ZXing.BrowserMultiFormatReader();
        console.log('Created BrowserMultiFormatReader');
        
        // Get list of available video devices
        const videoInputDevices = await codeReader.listVideoInputDevices();
        console.log('Available video devices:', videoInputDevices);
        
        // Populate device selection dropdown
        deviceSelect.innerHTML = '';
        if (videoInputDevices && videoInputDevices.length > 0) {
            videoInputDevices.forEach((device) => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.text = device.label || `Camera ${deviceSelect.length + 1}`;
                deviceSelect.appendChild(option);
            });
            
            // Set first device as selected
            selectedDeviceId = videoInputDevices[0].deviceId;
        } else {
            const option = document.createElement('option');
            option.text = 'No cameras found';
            deviceSelect.appendChild(option);
            console.warn('No camera devices found');
            showError("No camera devices found. Please use the test mode below.");
            return;
        }
    } catch (err) {
        console.error('Camera initialization error:', err);
        showError('Failed to access camera: ' + (err.message || 'Unknown error') + 
                 '. Please use the test mode below.');
        return;
    }
    
    // Event listeners
    deviceSelect.addEventListener('change', (event) => {
        selectedDeviceId = event.target.value;
    });
    
    startButton.addEventListener('click', () => {
        startScan();
    });
    
    stopButton.addEventListener('click', () => {
        stopScan();
    });
    
    console.log('Barcode scanner initialized successfully');
}

function startScan() {
    // Get elements
    // const startButton = document.getElementById('startScan');
    // const stopButton = document.getElementById('stopScan');
    // const resultContainer = document.getElementById('scanResult');
    // const scannerContainer = document.getElementById('scanner-container');
    
    // // Reset previous result
    // resultContainer.innerHTML = '';
    // document.getElementById('barcodeValue').value = '';
    
    // // Show video and stop button, hide start button
    // scannerContainer.classList.remove('d-none');
    // startButton.classList.add('d-none');
    // stopButton.classList.remove('d-none');
    
    // // Start decoding from video device
    // codeReader.decodeFromVideoDevice(selectedDeviceId, 'video', (result, err) => {
    //     if (result) {
    //         // We found a barcode
    //         console.log('Found barcode:', result.getText());
            
    //         // Display result and stop scanner
    //         const barcodeValue = result.getText();
    //         document.getElementById('barcodeValue').value = barcodeValue;
            
    //         resultContainer.innerHTML = `
    //             <div class="alert alert-success">
    //                 <strong>Barcode Detected!</strong><br>
    //                 <span>${barcodeValue}</span>
    //             </div>
    //             <button id="verifyBarcodeBtn" class="btn btn-primary">Verify Bill</button>
    //         `;
            
    //         // Add verify button listener
    //         document.getElementById('verifyBarcodeBtn').addEventListener('click', verifyBarcode);
            
    //         // Stop scanning
    //         stopScan();
    //     }
        
    //     if (err && !(err instanceof ZXing.NotFoundException)) {
    //         console.error(err);
    //         showError('Error during scanning: ' + err.message);
    //     }
    // }).catch((err) => {
    //     console.error(err);
    //     showError('Failed to start scanner: ' + err.message);
    //     stopScan();
    // });
    const startButton = document.getElementById('startScan');
    const stopButton = document.getElementById('stopScan');
    const resultContainer = document.getElementById('scanResult');
    const scannerContainer = document.getElementById('scanner-container');

    resultContainer.innerHTML = '';
    document.getElementById('barcodeValue').value = '';

    scannerContainer.classList.remove('d-none');
    startButton.classList.add('d-none');
    stopButton.classList.remove('d-none');

    console.log("Starting scan with device ID:", selectedDeviceId);

    codeReader.decodeFromVideoDevice(selectedDeviceId, 'video', (result, err) => {
        if (result) {
            const barcodeValue = result.getText();
            console.log('Barcode detected:', barcodeValue);
            document.getElementById('barcodeValue').value = barcodeValue;

            resultContainer.innerHTML = `
                <div class="alert alert-success">
                    <strong>Barcode Detected!</strong><br>
                    <span>${barcodeValue}</span>
                </div>
                <button id="verifyBarcodeBtn" class="btn btn-primary mt-2">Verify Bill</button>
            `;

            document.getElementById('verifyBarcodeBtn').addEventListener('click', () => {
                verifyBarcode(barcodeValue);
            });

            stopScan(); // Optional: stop after detection
        }

        if (err && !(err instanceof ZXing.NotFoundException)) {
            console.error(err);
            showError('Error during scanning: ' + err.message);
        }
    }).catch((err) => {
        console.error('Start scanner error:', err);
        showError('Scanner error: ' + err.message);
    });
}

function stopScan() {
    // const startButton = document.getElementById('startScan');
    // const stopButton = document.getElementById('stopScan');
    
    // // Show start button, hide stop button
    // startButton.classList.remove('d-none');
    // stopButton.classList.add('d-none');
    
    // // Reset video stream
    // if (codeReader) {
    //     codeReader.reset();
    // }
    const startButton = document.getElementById('startScan');
    const stopButton = document.getElementById('stopScan');

    startButton.classList.remove('d-none');
    stopButton.classList.add('d-none');

    if (codeReader) {
        codeReader.reset();
    }

    if (videoElement && videoElement.srcObject) {
        videoElement.srcObject.getTracks().forEach(track => track.stop());
        videoElement.srcObject = null;
    }
}

function showError(message) {
    // const resultContainer = document.getElementById('scanResult');
    // resultContainer.innerHTML = `
    //     <div class="alert alert-danger">
    //         <strong>Error!</strong><br>
    //         <span>${message}</span>
    //     </div>
    // `;
    const resultContainer = document.getElementById('scanResult');
    resultContainer.innerHTML = `
        <div class="alert alert-danger">
            <strong>Error:</strong><br>
            <span>${message}</span>
        </div>
    `;
}

function verifyBarcode() {
    const barcodeValue = document.getElementById('barcodeValue').value;
    const resultContainer = document.getElementById('scanResult');
    
    if (!barcodeValue) {
        showError('No barcode detected. Please scan again.');
        return;
    }
    
    console.log('Verifying barcode:', barcodeValue);
    
    // Show loading spinner
    resultContainer.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Verifying bill...</p>
        </div>
    `;
    
    // Create form data
    const formData = new FormData();
    formData.append('barcode', barcodeValue);
    
    // First, let's process directly to mark the bill as used and generate exit QR
    fetch('/verify_bill', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Process response status:', response.status);
        return response.json();
    })
    .then(processData => {
        console.log('Process response:', processData);
        
        if (processData.success) {
            // Successfully processed the bill
            const isFreeExit = processData.free_exit;
            
            let alertClass = isFreeExit ? 'success' : 'info';
            let exitMessage = isFreeExit ? 'You qualify for free exit!' : 'This bill does not qualify for free exit.';
            
            let html = `
                <div class="alert alert-${alertClass}">
                    <strong>Bill Verified!</strong><br>
                    <p>Amount: ₹${processData.amount}</p>
                    <p>${exitMessage}</p>
                </div>
            `;
            
            // If we have a QR code (for free exit)
            if (processData.qr_code) {
                html += `
                    <div class="mt-3 text-center">
                        <h4>Exit QR Code</h4>
                        <img src="data:image/png;base64,${processData.qr_code}" class="img-fluid qr-code-img" alt="Exit QR Code">
                        <p class="mt-2 small">This QR code is valid for 10 minutes and can be used only once.</p>
                    </div>
                    <div class="mt-3 text-center">
                        <a href="/dashboard" class="btn btn-primary">Return to Dashboard</a>
                
                    </div>
                `;
            } else {
                // No QR code yet, so provide button to proceed to exit page
                html += `
                    <div class="mt-3 text-center">
                        <input type="hidden" id="isFreeExit" value="${isFreeExit}">
                        <button id="proceedToExitBtn" class="btn btn-primary">Proceed to Exit</button>
                    </div>
                `;
            }
            
            resultContainer.innerHTML = html;
            
            // Add event listener for proceed button if present
            const proceedBtn = document.getElementById('proceedToExitBtn');
            if (proceedBtn) {
                proceedBtn.addEventListener('click', function() {
                    window.location.href = '/parking/exit';
                });
            }
        } else {
            // Fall back to verification only
            // This is useful if the barcode exists but processing fails
            console.log('Direct processing failed, falling back to verification only');
            verifyBarcodeOnly();
        }
    })
    .catch(error => {
        console.error('Processing error:', error);
        // Fall back to verification only
        verifyBarcodeOnly();
    });
}

function verifyBarcodeOnly() {
    const barcodeValue = document.getElementById('barcodeValue').value;
    const resultContainer = document.getElementById('scanResult');
    
    // Create form data
    const formData = new FormData();
    formData.append('barcode', barcodeValue);
    
    // Make API request to verify without processing
    fetch('/bill/verify_bill', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Verify response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Verify response:', data);
        
        if (data.success) {
            // If bill is valid, show details
            let freeExitClass = data.bill.free_exit ? 'success' : 'warning';
            let freeExitText = data.bill.free_exit ? 'You qualify for free exit!' : 'Bill does not qualify for free exit.';
            
            resultContainer.innerHTML = `
                <div class="alert alert-success">
                    <strong>Bill Verified!</strong><br>
                    <p>Bill Amount: ₹${data.bill.amount}</p>
                    <p class="text-${freeExitClass}">${freeExitText}</p>
                </div>
                <div class="mt-3">
                    <button id="processBillBtn" class="btn btn-primary">Process Bill</button>
                </div>
            `;
            
            // Add process button listener
            document.getElementById('processBillBtn').addEventListener('click', function() {
                // Call original verify_bill to process
                const processFormData = new FormData();
                processFormData.append('barcode', barcodeValue);
                
                resultContainer.innerHTML = `
                    <div class="text-center">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Processing...</span>
                        </div>
                        <p class="mt-2">Processing bill...</p>
                    </div>
                `;
                
                fetch('/verify_bill', {
                    method: 'POST',
                    body: processFormData
                })
                .then(response => response.json())
                .then(processData => {
                    if (processData.success) {
                        if (processData.qr_code) {
                            // Show QR code
                            resultContainer.innerHTML = `
                                <div class="alert alert-success">
                                    <strong>Success!</strong><br>
                                    <p>${processData.message}</p>
                                </div>
                                <div class="mt-3 text-center">
                                    <h4>Exit QR Code</h4>
                                    <img src="data:image/png;base64,${processData.qr_code}" class="img-fluid qr-code-img" alt="Exit QR Code">
                                    <p class="mt-2 small">This QR code is valid for 10 minutes and can be used only once.</p>
                                </div>
                                <div class="mt-3 text-center">
                                    <a href="/dashboard" class="btn btn-primary">Return to Dashboard</a>
                                    
                                </div>
                            `;
                        } else {
                            // Redirect to exit page
                            resultContainer.innerHTML = `
                                <div class="alert alert-success">
                                    <strong>Success!</strong><br>
                                    <p>${processData.message}</p>
                                </div>
                                <div class="mt-3">
                                    <button id="proceedToExitBtn" class="btn btn-primary">Proceed to Exit</button>
                                </div>
                            `;
                            
                            document.getElementById('proceedToExitBtn').addEventListener('click', function() {
                                window.location.href = '/parking/exit';
                            });
                        }
                    } else {
                        resultContainer.innerHTML = `
                            <div class="alert alert-danger">
                                <strong>Error!</strong><br>
                                <p>${processData.message}</p>
                            </div>
                            <button id="reScanBtn" class="btn btn-primary">Scan Again</button>
                        `;
                        
                        document.getElementById('reScanBtn').addEventListener('click', startScan);
                    }
                })
                .catch(error => {
                    console.error('Process error:', error);
                    showError('Failed to process bill. Please try again.');
                });
            });
        } else {
            // Display error
            resultContainer.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Error!</strong><br>
                    <p>${data.message}</p>
                </div>
                <button id="reScanBtn" class="btn btn-primary">Scan Again</button>
            `;
            
            // Add rescan button listener
            document.getElementById('reScanBtn').addEventListener('click', startScan);
        }
    })
    .catch(error => {
        console.error('Verification error:', error);
        resultContainer.innerHTML = `
            <div class="alert alert-danger">
                <strong>Error!</strong><br>
                <p>An unexpected error occurred.</p>
            </div>
            <button id="reScanBtn" class="btn btn-primary">Scan Again</button>
        `;
        
        // Add rescan button listener
        document.getElementById('reScanBtn').addEventListener('click', startScan);
    });
    // const resultContainer = document.getElementById('scanResult');

    // fetch('/verify-barcode', {
    //     method: 'POST',
    //     headers: {
    //         'Content-Type': 'application/json'
    //     },
    //     body: JSON.stringify({ barcode: barcodeNumber })
    // })
    // .then(response => response.json())
    // .then(data => {
    //     if (data.valid) {
    //         resultContainer.innerHTML += `
    //             <div class="alert alert-success mt-2">
    //                 ✅ Bill verified. Free parking granted.
    //             </div>`;
    //     } else {
    //         resultContainer.innerHTML += `
    //             <div class="alert alert-warning mt-2">
    //                 ❌ Bill not found. Please proceed to payment.
    //             </div>`;
    //     }
    // })
    // .catch(err => {
    //     console.error('Verification error:', err);
    //     showError('Could not verify barcode. Try again later.');
    // });
}



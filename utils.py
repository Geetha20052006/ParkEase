import qrcode
from io import BytesIO
import base64
import json
from datetime import datetime, timedelta
import secrets

def generate_qr_code(data):
    """
    Generate a QR code image from the given data
    
    Args:
        data (dict): The data to encode in the QR code
    
    Returns:
        str: Base64 encoded QR code image
    """
    # Convert data to JSON
    json_data = json.dumps(data)
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(json_data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffered = BytesIO()
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return img_str

def calculate_parking_charges(entry_time, exit_time=None):
    """
    Calculate parking charges based on duration
    
    Args:
        entry_time (datetime): Entry time
        exit_time (datetime, optional): Exit time. If None, current time is used.
    
    Returns:
        float: Parking charges (₹50 per hour)
    """
    if exit_time is None:
        exit_time = datetime.utcnow()
    
    duration = exit_time - entry_time
    hours = duration.total_seconds() / 3600
    
    # ₹50 per hour
    charges = round(50 * hours, 2)
    
    return charges

def is_valid_bill_amount(amount):
    """
    Check if bill amount qualifies for free exit (>= ₹500)
    
    Args:
        amount (float): Bill amount
    
    Returns:
        bool: True if amount qualifies for free exit, False otherwise
    """
    return amount >= 500

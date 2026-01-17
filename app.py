import os
import logging
from datetime import datetime, timedelta
import secrets
import qrcode
from io import BytesIO
import base64
import json

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize SQLAlchemy base class
class Base(DeclarativeBase):
    pass

# Initialize database
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", secrets.token_hex(16))
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///database.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize app with SQLAlchemy
db.init_app(app)

# Import models after db initialization
with app.app_context():
    from models import User, ParkingSlot, Transaction, QRCode, Bill
    
    # Create all tables
    db.create_all()
    
    # Check if we need to pre-populate database with initial data
    if ParkingSlot.query.count() == 0:
        # Create 50 parking slots
        for i in range(1, 51):
            slot = ParkingSlot(slot_number=i, status="Available")
            db.session.add(slot)
        
        # Add sample bills for testing
        sample_bills = [
            {"barcode": "123456789012", "bill_number": "BILL-001", "amount": 500, "status": "Active"},
            {"barcode": "987654321", "bill_number": "BILL-002", "amount": 1000, "status": "Active"},
            {"barcode": "456789123", "bill_number": "BILL-003", "amount": 750, "status": "Active"},
            {"barcode": "111222333", "bill_number": "BILL-004", "amount": 1500, "status": "Active"},
            {"barcode": "999888777", "bill_number": "BILL-005", "amount": 2000, "status": "Active"},
            {"barcode": "123123123", "bill_number": "BILL-006", "amount": 300, "status": "Active"},
            {"barcode": "456456456", "bill_number": "BILL-007", "amount": 450, "status": "Active"},
            {"barcode": "789789789", "bill_number": "BILL-008", "amount": 1200, "status": "Active"},
            {"barcode": "321321321", "bill_number": "BILL-009", "amount": 850, "status": "Active"},
            {"barcode": "654654654", "bill_number": "BILL-010", "amount": 950, "status": "Active"}
        ]
        
        for bill_data in sample_bills:
            bill = Bill(barcode=bill_data["barcode"], 
                      bill_number=bill_data["bill_number"], 
                      amount=bill_data["amount"], 
                      status=bill_data["status"],
                      is_used=False)
            db.session.add(bill)
        
        db.session.commit()
        logging.debug("Database initialized with sample data")

# JWT token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # JWT can be passed in session or in Authorization header
        if 'x-access-token' in session:
            token = session['x-access-token']
        elif 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            flash('Authentication required. Please login.', 'danger')
            return redirect(url_for('login'))
        
        try:
            data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                flash('User not found.', 'danger')
                return redirect(url_for('login'))
        except Exception as e:
            logging.error(f"Token error: {str(e)}")
            flash('Session expired. Please login again.', 'danger')
            return redirect(url_for('login'))
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Admin check decorator
def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(current_user, *args, **kwargs)
    
    return decorated

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        car_number = request.form.get('car_number')
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        
        # Validate inputs
        if not all([name, car_number, mobile, password]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        
        # Check if car number already exists
        if User.query.filter_by(car_number=car_number).first():
            flash('Car number already registered.', 'danger')
            return render_template('register.html')
        
        # Check if mobile already exists
        if User.query.filter_by(mobile=mobile).first():
            flash('Mobile number already registered.', 'danger')
            return render_template('register.html')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            name=name,
            car_number=car_number,
            mobile=mobile,
            password_hash=hashed_password,
            wallet_balance=0,
            is_admin=False
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        car_number = request.form.get('car_number')
        password = request.form.get('password')
        
        user = User.query.filter_by(car_number=car_number).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Please check your login details and try again.', 'danger')
            return render_template('login.html')
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.secret_key, algorithm="HS256")
        
        # Store token in session
        session['x-access-token'] = token
        session['user_id'] = user.id
        
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('x-access-token', None)
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# User dashboard
@app.route('/dashboard')
@token_required
def dashboard(current_user):
    # Get active parking session if any
    active_qr = QRCode.query.filter_by(
        user_id=current_user.id, 
        type='entry', 
        is_used=True, 
        is_active=True
    ).first()
    
    parking_data = None
    if active_qr:
        # Get parking slot
        slot = ParkingSlot.query.get(active_qr.slot_id)
        if slot:
            entry_time = active_qr.created_at
            current_time = datetime.utcnow()
            duration = current_time - entry_time
            hours = duration.total_seconds() / 3600
            
            # Calculate parking charges (₹50 per hour)
            charges = round(50 * hours, 2)
            
            parking_data = {
                'slot_number': slot.slot_number,
                'entry_time': entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration': f"{int(hours)} hours {int((hours % 1) * 60)} minutes",
                'charges': charges
            }
    
    return render_template('dashboard.html', user=current_user, parking_data=parking_data)

# Wallet routes
@app.route('/wallet')
@token_required
def wallet(current_user):
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(10).all()
    return render_template('wallet.html', user=current_user, transactions=transactions)

@app.route('/add_funds', methods=['POST'])
@token_required
def add_funds(current_user):
    amount = request.form.get('amount')
    
    try:
        amount = float(amount)
        if amount <= 0:
            flash('Amount must be positive.', 'danger')
            return redirect(url_for('wallet'))
        
        # Update wallet balance
        current_user.wallet_balance += amount
        
        # Add transaction record
        transaction = Transaction(
            user_id=current_user.id,
            amount=amount,
            type='credit',
            description='Wallet top-up',
            timestamp=datetime.utcnow()
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'₹{amount} added to your wallet successfully.', 'success')
    except ValueError:
        flash('Invalid amount.', 'danger')
    
    return redirect(url_for('wallet'))

# Parking entry
@app.route('/parking/entry')
@token_required
def parking_entry(current_user):
    # Check if user already has an active parking session
    active_qr = QRCode.query.filter_by(
        user_id=current_user.id, 
        type='entry', 
        is_used=True, 
        is_active=True
    ).first()
    
    if active_qr:
        flash('You already have an active parking session.', 'warning')
        return redirect(url_for('dashboard'))
    
    # Check if user has minimum required balance
    if current_user.wallet_balance < 100:
        flash('Minimum wallet balance of ₹100 required for parking entry.', 'danger')
        return redirect(url_for('wallet'))
    
    return render_template('parking_entry.html', user=current_user)

@app.route('/generate_entry_qr', methods=['POST'])
@token_required
def generate_entry_qr(current_user):
    # Find nearest available parking slot
    available_slot = ParkingSlot.query.filter_by(status='Available').first()
    
    if not available_slot:
        return jsonify({'success': False, 'message': 'No parking slots available.'})
    
    # Mark slot as occupied
    available_slot.status = 'Occupied'
    available_slot.occupied_by = current_user.id
    available_slot.occupied_at = datetime.utcnow()
    
    # Create QR code data
    qr_data = {
        'user_id': current_user.id,
        'slot_id': available_slot.id,
        'type': 'entry',
        'timestamp': datetime.utcnow().isoformat(),
        'random': secrets.token_hex(8)  # Add some randomness
    }
    
    # Convert to JSON
    qr_json = json.dumps(qr_data)
    
    # Generate QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_json)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert image to base64 string
    buffered = BytesIO()
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # Save QR code entry in database
    db_qr = QRCode(
        user_id=current_user.id,
        slot_id=available_slot.id,
        type='entry',
        data=qr_json,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        is_used=False,
        is_active=False
    )
    
    db.session.add(db_qr)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'qr_code': img_str, 
        'slot_number': available_slot.slot_number,
        'qr_id': db_qr.id
    })

@app.route('/confirm_entry/<int:qr_id>', methods=['POST'])
@token_required
def confirm_entry(current_user, qr_id):
    qr_code = QRCode.query.get_or_404(qr_id)
    
    # Verify QR code belongs to the user
    if qr_code.user_id != current_user.id:
        flash('Invalid QR code.', 'danger')
        return redirect(url_for('parking_entry'))
    
    # Check if QR is already used
    if qr_code.is_used:
        flash('QR code already used.', 'danger')
        return redirect(url_for('parking_entry'))
    
    # Check if QR is expired
    if datetime.utcnow() > qr_code.expires_at:
        flash('QR code expired.', 'danger')
        return redirect(url_for('parking_entry'))
    
    # Mark QR as used and active
    qr_code.is_used = True
    qr_code.is_active = True
    
    db.session.commit()
    
    flash(f'Parking entry confirmed. Your slot number is {ParkingSlot.query.get(qr_code.slot_id).slot_number}.', 'success')
    return redirect(url_for('dashboard'))

# Parking exit
@app.route('/parking/exit')
@token_required
def parking_exit(current_user):
    # Check if user has an active parking session
    active_qr = QRCode.query.filter_by(
        user_id=current_user.id, 
        type='entry', 
        is_used=True, 
        is_active=True
    ).first()
    
    if not active_qr:
        flash('No active parking session found.', 'warning')
        return redirect(url_for('dashboard'))
    
    slot = ParkingSlot.query.get(active_qr.slot_id)
    
    # Calculate parking duration and charges
    entry_time = active_qr.created_at
    current_time = datetime.utcnow()
    duration = current_time - entry_time
    hours = duration.total_seconds() / 3600
    
    # Calculate parking charges (₹50 per hour)
    charges = round(50 * hours, 2)
    
    parking_data = {
        'slot_number': slot.slot_number,
        'entry_time': entry_time.strftime('%Y-%m-%d %H:%M:%S'),
        'duration': f"{int(hours)} hours {int((hours % 1) * 60)} minutes",
        'charges': charges
    }
    
    return render_template('parking_exit.html', user=current_user, parking_data=parking_data)

@app.route('/bill_scanner')
@token_required
def bill_scanner(current_user):
    # Check if user has an active parking session
    active_qr = QRCode.query.filter_by(
        user_id=current_user.id, 
        type='entry', 
        is_used=True, 
        is_active=True
    ).first()
    
    if not active_qr:
        flash('No active parking session found.', 'warning')
        return redirect(url_for('dashboard'))
    
    return render_template('bill_scanner.html', user=current_user)

@app.route('/verify_bill', methods=['POST'])
@token_required
def verify_bill(current_user):
    barcode = request.form.get('barcode')
    
    # Add logging
    print(f"Verifying bill with barcode: {barcode} for user: {current_user.id}")
    
    # Check if barcode exists in the database
    bill = Bill.query.filter_by(barcode=barcode).first()
    
    if not bill:
        print(f"Bill not found: {barcode}")
        return jsonify({'success': False, 'message': 'Invalid bill. Bill not found in database.'})
    
    if bill.is_used or bill.status == 'Used':
        print(f"Bill already used: {barcode}")
        return jsonify({'success': False, 'message': 'This bill has already been used.'})
    
    # Check if the user has an active parking session before processing
    active_qr = QRCode.query.filter_by(
        user_id=current_user.id, 
        type='entry', 
        is_used=True, 
        is_active=True
    ).first()
    
    if not active_qr:
        print(f"No active parking session for user: {current_user.id}")
        return jsonify({'success': False, 'message': 'No active parking session found. Please enter the parking lot first.'})
    
    # Mark bill as used
    bill.is_used = True
    bill.status = 'Used'
    bill.used_by = current_user.id
    bill.used_at = datetime.utcnow()
    
    db.session.commit()
    print(f"Bill marked as used: {barcode}")
    
    # Check if the bill amount qualifies for free exit
    free_exit = bill.amount >= 500
    print(f"Bill amount: {bill.amount}, Free exit: {free_exit}")
    
    # If free exit, generate QR code directly
    qr_code_data = None
    if free_exit:
        # Get the slot from active QR
        slot = ParkingSlot.query.get(active_qr.slot_id)
        
        # Load the QR code generator
        from utils import generate_qr_code
        
        # Create QR code data
        qr_data = {
            'user_id': current_user.id,
            'slot_id': slot.id,
            'type': 'exit',
            'free_exit': True,
            'bill_id': bill.id,
            'timestamp': datetime.utcnow().isoformat(),
            'random': secrets.token_hex(8)  # Add some randomness
        }
        
        # Save QR code to database
        db_qr = QRCode(
            user_id=current_user.id,
            slot_id=slot.id,
            type='exit',
            data=json.dumps(qr_data),
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_used=False,
            is_active=False
        )
        
        db.session.add(db_qr)
        db.session.commit()
        print(f"Exit QR code created with ID: {db_qr.id}")
        
        # Generate QR code image
        qr_code_data = generate_qr_code(qr_data)
    
    return jsonify({
        'success': True, 
        'message': f'Bill verified successfully! Amount: ₹{bill.amount}',
        'amount': bill.amount,
        'free_exit': free_exit,
        'qr_code': qr_code_data  # Will be null if not a free exit
    })

@app.route('/bill/verify_bill', methods=['POST'])
@token_required
def api_verify_bill(current_user):
    barcode = request.form.get('barcode')
    
    if not barcode:
        return jsonify({'success': False, 'message': 'Barcode is required.'})
    
    # Log incoming request
    logging.debug(f"Received barcode verification request for: {barcode}")
    
    # Check if barcode exists in the database
    bill = Bill.query.filter_by(barcode=barcode).first()
    
    if not bill:
        logging.debug(f"Bill not found for barcode: {barcode}")
        return jsonify({'success': False, 'message': 'Bill not found. Please check the barcode and try again.'})
    
    if bill.is_used or bill.status == 'Used':
        logging.debug(f"Bill already used: {barcode}")
        return jsonify({'success': False, 'message': 'This bill has already been used.'})
    
    # Check if the bill amount qualifies for free exit
    free_exit = bill.amount >= 500
    
    # Log successful verification
    logging.debug(f"Bill verified successfully: {barcode}, Amount: {bill.amount}, Free Exit: {free_exit}")
    
    return jsonify({
        'success': True,
        'bill': {
            'id': bill.id,
            'bill_number': bill.bill_number,
            'amount': bill.amount,
            'free_exit': free_exit
        },
        'message': f'Bill verified! Amount: ₹{bill.amount}. {"You qualify for free exit!" if free_exit else "Bill does not qualify for free exit."}'
    })

@app.route('/generate_exit_qr', methods=['POST'])
@token_required
def generate_exit_qr(current_user):
    is_free_exit = request.form.get('is_free_exit') == 'true'
    charges = float(request.form.get('charges', 0))
    
    # Check if user has an active parking session
    active_qr = QRCode.query.filter_by(
        user_id=current_user.id, 
        type='entry', 
        is_used=True, 
        is_active=True
    ).first()
    
    if not active_qr:
        return jsonify({'success': False, 'message': 'No active parking session found.'})
    
    slot = ParkingSlot.query.get(active_qr.slot_id)
    
    # Process payment if not free exit
    if not is_free_exit:
        # Check if user has sufficient balance
        if current_user.wallet_balance < charges:
            return jsonify({'success': False, 'message': 'Insufficient wallet balance.'})
        
        # Deduct charges from wallet
        current_user.wallet_balance -= charges
        
        # Add transaction record
        transaction = Transaction(
            user_id=current_user.id,
            amount=charges,
            type='debit',
            description='Parking charges',
            timestamp=datetime.utcnow()
        )
        
        db.session.add(transaction)
    
    # Create QR code data for exit
    qr_data = {
        'user_id': current_user.id,
        'slot_id': slot.id,
        'type': 'exit',
        'timestamp': datetime.utcnow().isoformat(),
        'is_free_exit': is_free_exit,
        'charges': charges if not is_free_exit else 0,
        'random': secrets.token_hex(8)  # Add some randomness
    }
    
    # Convert to JSON
    qr_json = json.dumps(qr_data)
    
    # Generate QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_json)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert image to base64 string
    buffered = BytesIO()
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # Save QR code exit in database
    db_qr = QRCode(
        user_id=current_user.id,
        slot_id=slot.id,
        type='exit',
        data=qr_json,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        is_used=False,
        is_active=False
    )
    
    db.session.add(db_qr)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'qr_code': img_str, 
        'qr_id': db_qr.id,
        'message': 'Free exit granted!' if is_free_exit else f'₹{charges} deducted from wallet.'
    })

@app.route('/confirm_exit/<int:qr_id>', methods=['POST'])
@token_required
def confirm_exit(current_user, qr_id):
    qr_code = QRCode.query.get_or_404(qr_id)
    
    # Verify QR code belongs to the user
    if qr_code.user_id != current_user.id:
        flash('Invalid QR code.', 'danger')
        return redirect(url_for('parking_exit'))
    
    # Check if QR is already used
    if qr_code.is_used:
        flash('QR code already used.', 'danger')
        return redirect(url_for('parking_exit'))
    
    # Check if QR is expired
    if datetime.utcnow() > qr_code.expires_at:
        flash('QR code expired.', 'danger')
        return redirect(url_for('parking_exit'))
    
    # Get the parking slot
    slot = ParkingSlot.query.get(qr_code.slot_id)
    
    # Mark slot as available
    slot.status = 'Available'
    slot.occupied_by = None
    slot.occupied_at = None
    
    # Mark QR as used
    qr_code.is_used = True
    
    # Mark entry QR as inactive
    entry_qr = QRCode.query.filter_by(
        user_id=current_user.id, 
        type='entry', 
        is_used=True, 
        is_active=True,
        slot_id=slot.id
    ).first()
    
    if entry_qr:
        entry_qr.is_active = False
    
    db.session.commit()
    
    flash('Parking exit confirmed. Thank you for using ParkEase!', 'success')
    return redirect(url_for('dashboard'))

# Admin routes
@app.route('/admin/slots')
@admin_required
def admin_slots(current_user):
    slots = ParkingSlot.query.all()
    
    # Get user info for occupied slots
    slot_data = []
    for slot in slots:
        data = {
            'id': slot.id,
            'slot_number': slot.slot_number,
            'status': slot.status,
            'user': None
        }
        
        if slot.occupied_by:
            user = User.query.get(slot.occupied_by)
            if user:
                data['user'] = {
                    'name': user.name,
                    'car_number': user.car_number,
                    'entry_time': slot.occupied_at.strftime('%Y-%m-%d %H:%M:%S') if slot.occupied_at else None
                }
        
        slot_data.append(data)
    
    return render_template('admin_slots.html', user=current_user, slots=slot_data)

# Create admin user if not exists
@app.route('/create_admin', methods=['GET'])
def create_admin():
    admin = User.query.filter_by(is_admin=True).first()
    
    if admin:
        flash('Admin user already exists.', 'info')
        return redirect(url_for('index'))
    
    # Create admin user
    admin_password = "admin123"  # In production, this would be more secure
    hashed_password = generate_password_hash(admin_password)
    
    admin_user = User(
        name="Admin User",
        car_number="ADMIN001",
        mobile="9999999999",
        password_hash=hashed_password,
        wallet_balance=1000,
        is_admin=True
    )
    
    db.session.add(admin_user)
    db.session.commit()
    
    flash('Admin user created successfully.', 'success')
    return redirect(url_for('index'))


# Create test bills for development
@app.route('/create_test_bills', methods=['GET'])
def create_test_bills():
    # Check if test bills already exist
    existing_bills = Bill.query.filter(Bill.barcode.in_(['123456789', '987654321', '456789123'])).count()
    
    if existing_bills >= 3:
        flash('Test bills already exist.', 'info')
        return redirect(url_for('index'))
    
    # Create test bills with different amounts
    test_bills = [
        Bill(barcode='123456789', bill_number='BILL0001', amount=600, status='Active', is_used=False),  # Qualifies for free exit
        Bill(barcode='987654321', bill_number='BILL0002', amount=250, status='Active', is_used=False),  # Does not qualify
        Bill(barcode='456789123', bill_number='BILL0003', amount=500, status='Active', is_used=False)   # Exactly the threshold
    ]
    
    for bill in test_bills:
        db.session.add(bill)
    
    db.session.commit()
    
    flash('Test bills created successfully. Use barcodes: 123456789, 987654321, 456789123', 'success')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

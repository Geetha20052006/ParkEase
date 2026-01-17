from datetime import datetime
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    car_number = db.Column(db.String(20), unique=True, nullable=False)
    mobile = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    wallet_balance = db.Column(db.Float, default=0.0)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    qr_codes = db.relationship('QRCode', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.name}>'

class ParkingSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slot_number = db.Column(db.Integer, unique=True, nullable=False)
    status = db.Column(db.String(20), default='Available')  # Available, Occupied
    occupied_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    occupied_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    qr_codes = db.relationship('QRCode', backref='slot', lazy=True)
    
    def __repr__(self):
        return f'<ParkingSlot {self.slot_number}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # credit, debit
    description = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transaction {self.id}>'

class QRCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('parking_slot.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # entry, exit
    data = db.Column(db.Text, nullable=False)  # JSON string with QR data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<QRCode {self.id}>'

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(50), unique=True, nullable=False)
    bill_number = db.Column(db.String(50), nullable=True)  # Added bill_number field
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Active')  # Active, Used
    is_used = db.Column(db.Boolean, default=False)  # Keeping for backward compatibility
    used_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Bill {self.bill_number or self.barcode}>'

# 🚗 ParkEase – Smart Parking Management System

ParkEase is a smart parking management system that automates parking slot allocation, shopping bill validation, and vehicle exit using QR codes and barcode scanning. The project aims to reduce manual work, avoid parking congestion, and provide a smooth parking experience.

---

## 📌 Features

- QR code–based parking entry
- Automatic parking slot allocation
- Shopping bill validation using barcode scanning
- Free parking for valid shopping bills
- UPI payment option for invalid bills
- QR code–based exit within 10 minutes
- Database-backed bill verification

---

## 🛠️ Technologies Used

- HTML
- CSS
- JavaScript
- ZXing (JavaScript Barcode Scanner)
- SQLite / SQL Database
- QR Code Generator
- UPI Payment (conceptual)

---

## 🔄 System Workflow

1. User enters the parking area
2. Entry QR code is scanned
3. System assigns an available parking slot
4. User scans shopping bill barcode
5. Bill is validated from database
6. If bill is valid and unused → Free parking
7. If bill is invalid or already used → UPI payment
8. Exit QR code is generated with expiry time
9. User exits parking within allowed time

---

## 🗃️ Database Schema

### 1️⃣ `bill` Table  
Stores shopping bill details and usage status.

| Column Name | Description |
|------------|------------|
| id | Primary key |
| barcode | Bill barcode value |
| bill_number | Bill reference number |
| amount | Bill amount |
| status | Bill validity status |
| is_used | Indicates if bill is already used |
| used_by | User ID who used the bill |
| used_at | Timestamp when bill was used |

---

### 2️⃣ `parking_slot` Table  
Manages parking slot allocation.

| Column Name | Description |
|------------|------------|
| id | Primary key |
| slot_number | Parking slot identifier |
| status | Available / Occupied |
| occupied_by | User ID |
| occupied_at | Slot occupation time |

---

### 3️⃣ `qr_code` Table  
Stores generated QR codes for entry and exit.

| Column Name | Description |
|------------|------------|
| id | Primary key |
| user_id | Associated user |
| slot_id | Assigned parking slot |
| type | Entry / Exit |
| data | QR code data |
| created_at | QR generation time |
| expires_at | QR expiry time |
| is_used | QR usage status |
| is_active | QR activation status |

---

### 4️⃣ `transaction` Table  
Tracks all parking-related payments.

| Column Name | Description |
|------------|------------|
| id | Primary key |
| user_id | User making the payment |
| amount | Paid amount |
| type | Payment type (UPI / Free) |
| description | Transaction details |
| timestamp | Payment time |

---

### 5️⃣ `user` Table  
Stores registered user information.

| Column Name | Description |
|------------|------------|
| id | Primary key |
| name | User name |
| car_number | Vehicle number |
| mobile | Contact number |
| password_hash | Encrypted password |
| wallet_balance | User wallet balance |
| is_admin | Admin flag |
| created_at | Account creation time |
| last_login | Last login timestamp |

---





from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'hospital_management_secret_key_2024'
app.config['DATABASE'] = 'hospital.db'

# Make datetime available to all templates
@app.context_processor
def inject_datetime():
    return dict(datetime=datetime)

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists('hospital.db'):
        conn = get_db_connection()
        # Check if doctors table exists and add password column if missing
        try:
            table_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='doctors'").fetchone()
            if table_exists:
                # Check if password column exists
                columns = [row[1] for row in conn.execute("PRAGMA table_info(doctors)").fetchall()]
                if 'password' not in columns:
                    conn.execute('ALTER TABLE doctors ADD COLUMN password TEXT')
                    conn.commit()
                # Always ensure all doctors have passwords (set default 'doc123' if NULL or empty)
                conn.execute("UPDATE doctors SET password = 'doc123' WHERE password IS NULL OR password = '' OR password IS NOT NULL AND LENGTH(TRIM(password)) = 0")
                conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Database migration error: {e}")
        finally:
            conn.close()
        return
    
    conn = get_db_connection()
    
    # Create tables
    conn.executescript('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT
        );
        
        CREATE TABLE patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            address TEXT,
            date_of_birth TEXT,
            gender TEXT,
            emergency_contact TEXT,
            medical_history TEXT,
            created_at TEXT
        );
        
        CREATE TABLE doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT,
            phone TEXT,
            email TEXT,
            password TEXT NOT NULL,
            availability TEXT DEFAULT 'Available'
        );
        
        CREATE TABLE appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT DEFAULT 'Scheduled',
            notes TEXT,
            created_at TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        );
        
        CREATE TABLE bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            appointment_id INTEGER,
            total_amount REAL NOT NULL,
            payment_status TEXT DEFAULT 'Pending',
            payment_method TEXT,
            created_at TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        );
        
        CREATE TABLE medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price DECIMAL(8,2) NOT NULL,
            stock_quantity INTEGER DEFAULT 0,
            manufacturer TEXT
        );
        
        CREATE TABLE prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER NOT NULL,
            medicine_id INTEGER NOT NULL,
            dosage TEXT,
            duration TEXT,
            instructions TEXT,
            prescribed_date TEXT,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id),
            FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        );
        
        CREATE TABLE alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            alert_type TEXT,
            created_at TEXT
        );
    ''')
    
    # Create Triggers
    conn.executescript('''
        -- Trigger 1: Update doctor availability when appointment is booked
        CREATE TRIGGER update_doctor_availability 
        AFTER INSERT ON appointments
        BEGIN
            UPDATE doctors SET availability = 'Busy' 
            WHERE id = NEW.doctor_id;
        END;
        
        -- Trigger 2: Low stock alert for medicines
        CREATE TRIGGER low_stock_alert 
        AFTER UPDATE ON medicines
        WHEN NEW.stock_quantity < 10
        BEGIN
            INSERT INTO alerts (message, alert_type, created_at) 
            VALUES ('Low stock alert for ' || NEW.name, 'warning', datetime('now'));
        END;
        
        -- Trigger 3: Auto-complete appointment after 24 hours
        CREATE TRIGGER auto_complete_appointment 
        AFTER INSERT ON appointments
        BEGIN
            UPDATE appointments SET status = 'Completed' 
            WHERE id = NEW.id AND datetime(appointment_date || ' ' || appointment_time) < datetime('now', '-1 day');
        END;
    ''')
    
    # Insert sample data
    users = [
        ('admin', 'admin123', 'admin', 'admin@hospital.com'),
        ('doctor1', 'doc123', 'doctor', 'doctor1@hospital.com'),
        ('reception1', 'recep123', 'receptionist', 'reception@hospital.com'),
        ('pharmacy1', 'pharma123', 'pharmacy', 'pharmacy@hospital.com'),
        ('billing1', 'bill123', 'billing', 'billing@hospital.com')
    ]
    
    patients = [
        ('Alice Brown', 'alice@email.com', '9876543201', '123 Main St, Bangalore', '1990-05-15', 'Female', '9876543299', 'No significant history', '2024-01-01 10:00:00'),
        ('Bob Wilson', 'bob@email.com', '9876543202', '456 Oak Ave, Bangalore', '1985-08-22', 'Male', '9876543298', 'Hypertension', '2024-01-01 11:00:00'),
        ('Carol Davis', 'carol@email.com', '9876543203', '789 Pine Rd, Bangalore', '1992-12-10', 'Female', '9876543297', 'Diabetes', '2024-01-01 12:00:00')
    ]
    
    doctors = [
        ('Dr. John Smith', 'Cardiology', '9876543210', 'doctor1@hospital.com', 'doc123', 'Available'),
        ('Dr. Sarah Johnson', 'Pediatrics', '9876543211', 'sarah.j@hospital.com', 'doc123', 'Available'),
        ('Dr. Mike Wilson', 'Orthopedics', '9876543212', 'mike.w@hospital.com', 'doc123', 'Available'),
        ('Dr. Emily Chen', 'Dermatology', '9876543213', 'emily.c@hospital.com', 'doc123', 'Busy')
    ]
    
    appointments = [
        (1, 1, '2024-12-20', '10:00:00', 'Scheduled', 'Regular heart checkup', '2024-01-01 09:00:00'),
        (2, 2, '2024-12-21', '11:00:00', 'Completed', 'Fever and cold', '2024-01-01 10:00:00'),
        (3, 3, '2024-12-22', '14:00:00', 'Scheduled', 'Knee pain consultation', '2024-01-01 11:00:00'),
        (1, 4, '2024-12-23', '15:30:00', 'Scheduled', 'Skin allergy', '2024-01-01 12:00:00')
    ]
    
    bills = [
        (1, 1, 500.00, 'Paid', 'Card', '2024-01-01 12:00:00'),
        (2, 2, 750.00, 'Pending', 'Cash', '2024-01-01 13:00:00'),
        (3, 3, 1200.00, 'Pending', 'Insurance', '2024-01-01 14:00:00'),
        (1, 4, 300.00, 'Paid', 'Online', '2024-01-01 15:00:00')
    ]
    
    medicines = [
        ('Paracetamol', 'Pain and fever relief', 5.00, 100, 'Pharma Corp'),
        ('Amoxicillin', 'Antibiotic for infections', 15.50, 50, 'Medi Labs'),
        ('Vitamin C', 'Immune system booster', 8.75, 200, 'Health Plus'),
        ('Ibuprofen', 'Anti-inflammatory pain reliever', 12.25, 5, 'PainFree Inc')  # Low stock for trigger demo
    ]
    
    conn.executemany('INSERT INTO users (username, password, role, email) VALUES (?,?,?,?)', users)
    conn.executemany('INSERT INTO patients (name, email, phone, address, date_of_birth, gender, emergency_contact, medical_history, created_at) VALUES (?,?,?,?,?,?,?,?,?)', patients)
    conn.executemany('INSERT INTO doctors (name, specialization, phone, email, password, availability) VALUES (?,?,?,?,?,?)', doctors)
    conn.executemany('INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status, notes, created_at) VALUES (?,?,?,?,?,?,?)', appointments)
    conn.executemany('INSERT INTO bills (patient_id, appointment_id, total_amount, payment_status, payment_method, created_at) VALUES (?,?,?,?,?,?)', bills)
    conn.executemany('INSERT INTO medicines (name, description, price, stock_quantity, manufacturer) VALUES (?,?,?,?,?)', medicines)
    
    conn.commit()
    conn.close()
    print("✅ Database created with sample data and triggers!")

# Initialize database
with app.app_context():
    init_db()

# STORED PROCEDURES AND FUNCTIONS
def calculate_patient_age(date_of_birth):
    """Function: Calculate patient age from DOB"""
    from datetime import datetime
    birth_date = datetime.strptime(date_of_birth, '%Y-%m-%d')
    today = datetime.now()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def calculate_total_with_tax(amount):
    """Function: Calculate total with 18% GST"""
    return amount + (amount * 0.18)

def discharge_patient(patient_id):
    """Procedure: Complete patient discharge process"""
    conn = get_db_connection()
    try:
        # Update appointments
        conn.execute("UPDATE appointments SET status = 'Completed' WHERE patient_id = ? AND status = 'Scheduled'", (patient_id,))
        
        # Calculate total charges
        total_charges = conn.execute("SELECT SUM(total_amount) FROM bills WHERE patient_id = ?", (patient_id,)).fetchone()[0] or 0
        
        # Update final bill
        conn.execute("UPDATE bills SET payment_status = 'Pending' WHERE patient_id = ? AND payment_status != 'Paid'", (patient_id,))
        
        conn.commit()
        return f"Patient discharged successfully. Total charges: ₹{total_charges}"
    except Exception as e:
        conn.rollback()
        return f"Error: {str(e)}"
    finally:
        conn.close()

def generate_monthly_report(month, year):
    """Procedure: Generate monthly financial report"""
    conn = get_db_connection()
    report = conn.execute('''
        SELECT 
            COUNT(*) as total_bills,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as average_bill,
            SUM(CASE WHEN payment_status = 'Paid' THEN total_amount ELSE 0 END) as collected_amount
        FROM bills 
        WHERE strftime('%m', created_at) = ? AND strftime('%Y', created_at) = ?
    ''', (str(month).zfill(2), str(year))).fetchone()
    conn.close()
    return report

# ROUTES
@app.route('/')
def home():
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    
    conn = get_db_connection()
    
    if role == 'patient':
        # Check if patient exists
        patient = conn.execute('SELECT * FROM patients WHERE email = ? AND phone = ?', (username, password)).fetchone()
        
        if patient:
            # Existing patient - login normally
            session['user_id'] = patient['id']
            session['username'] = patient['name']
            session['role'] = 'patient'
            session['email'] = patient['email']
            conn.close()
            flash('Login successful! Welcome to Patient Portal.', 'success')
            return redirect(url_for('patient_dashboard'))
        else:
            # Auto-register new patient
            try:
                # Generate a random patient name if not provided
                patient_name = username.split('@')[0].title()  # Use email username as name
                
                conn.execute('''
                    INSERT INTO patients (name, email, phone, address, date_of_birth, gender, emergency_contact, medical_history, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    patient_name,  # name
                    username,      # email
                    password,      # phone (using password as phone for demo)
                    'Not specified',  # address
                    '2000-01-01',     # default DOB
                    'Other',           # default gender
                    password,          # emergency contact (same as phone)
                    'No medical history',  # default medical history
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # created_at
                ))
                conn.commit()
                
                # Get the newly created patient
                new_patient = conn.execute('SELECT * FROM patients WHERE email = ?', (username,)).fetchone()
                
                session['user_id'] = new_patient['id']
                session['username'] = new_patient['name']
                session['role'] = 'patient'
                session['email'] = new_patient['email']
                conn.close()
                
                flash('New patient account created automatically! Welcome to Patient Portal.', 'success')
                return redirect(url_for('patient_dashboard'))
                
            except Exception as e:
                conn.close()
                flash('Error creating patient account. Please try different credentials.', 'error')
                return redirect(url_for('login_page'))
    elif role == 'doctor':
        # Check if doctor exists using name and password
        # Trim whitespace from username and password for matching
        username_trimmed = username.strip()
        password_trimmed = password.strip()
        
        # Ensure all doctors have passwords (migration for existing doctors)
        conn.execute("UPDATE doctors SET password = 'doc123' WHERE password IS NULL OR password = ''")
        conn.commit()
        
        # Try exact match first
        doctor = conn.execute('SELECT * FROM doctors WHERE name = ? AND password = ?', (username_trimmed, password_trimmed)).fetchone()
        
        # If not found, try with trimmed name from database (in case there are extra spaces in DB)
        if not doctor:
            all_doctors = conn.execute('SELECT * FROM doctors').fetchall()
            for doc in all_doctors:
                doc_name = doc['name'].strip() if doc['name'] else ''
                doc_password = doc['password'] if doc['password'] else 'doc123'
                if doc_name == username_trimmed and doc_password == password_trimmed:
                    doctor = doc
                    break
        
        if doctor:
            session['user_id'] = doctor['id']
            session['username'] = doctor['name']
            session['role'] = 'doctor'
            session['email'] = doctor['email']
            conn.close()
            flash(f'Login successful! Welcome {doctor["name"]}.', 'success')
            return redirect(url_for('doctor_dashboard'))
        else:
            conn.close()
            flash('Invalid credentials! Please contact administrator if you need assistance.', 'error')
            return redirect(url_for('login_page'))
    else:
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ? AND role = ?', (username, password, role)).fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['email'] = user['email']
            conn.close()
            flash(f'Login successful! Welcome {user["username"]}.', 'success')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'receptionist':
                return redirect(url_for('receptionist_dashboard'))
            elif user['role'] == 'pharmacy':
                return redirect(url_for('pharmacy_dashboard'))
            elif user['role'] == 'billing':
                return redirect(url_for('billing_dashboard'))
    
    conn.close()
    flash('Invalid credentials! Please try again.', 'error')
    return redirect(url_for('login_page'))

# ADMIN ROUTES
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('Please login as administrator.', 'error')
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    doctors_count = conn.execute('SELECT COUNT(*) FROM doctors').fetchone()[0]
    patients_count = conn.execute('SELECT COUNT(*) FROM patients').fetchone()[0]
    appointments_count = conn.execute("SELECT COUNT(*) FROM appointments WHERE status = 'Scheduled'").fetchone()[0]
    revenue = conn.execute("SELECT SUM(total_amount) FROM bills WHERE payment_status = 'Paid'").fetchone()[0] or 0
    
    appointments = conn.execute('''
        SELECT a.*, p.name as patient_name, d.name as doctor_name 
        FROM appointments a 
        JOIN patients p ON a.patient_id = p.id 
        JOIN doctors d ON a.doctor_id = d.id 
        ORDER BY a.appointment_date DESC LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html',
                         doctors_count=doctors_count,
                         patients_count=patients_count,
                         appointments_count=appointments_count,
                         revenue=revenue,
                         appointments=appointments)

@app.route('/admin/dbms-features')
def admin_dbms_features():
    if session.get('role') != 'admin':
        flash('Please login as administrator.', 'error')
        return redirect(url_for('login_page'))
    conn = get_db_connection()
    patients = conn.execute('SELECT * FROM patients').fetchall()
    patients_with_age = []
    for patient in patients:
        age = calculate_patient_age(patient['date_of_birth']) if patient['date_of_birth'] else 0
        patients_with_age.append({**dict(patient), 'age': age})
    bills = conn.execute('SELECT * FROM bills ORDER BY id DESC').fetchall()
    bills_with_tax = []
    for bill in bills:
        total_with_tax = calculate_total_with_tax(bill['total_amount'])
        bills_with_tax.append({**dict(bill), 'total_with_tax': total_with_tax})
    conn.close()
    return render_template('admin/dbms_features.html', patients=patients_with_age, bills=bills_with_tax)

@app.route('/admin/doctors')
def admin_doctors():
    if session.get('role') != 'admin':
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    doctors = conn.execute('SELECT * FROM doctors').fetchall()
    conn.close()
    return render_template('admin/doctors.html', doctors=doctors)

@app.route('/admin/patients')
def admin_patients():
    if session.get('role') != 'admin':
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    patients = conn.execute('SELECT * FROM patients').fetchall()
    
    patients_with_age = []
    for patient in patients:
        try:
            dob = patient['date_of_birth'] if patient['date_of_birth'] else None
            age = calculate_patient_age(dob) if dob else 0
        except Exception:
            age = 0
        patients_with_age.append({**dict(patient), 'age': age})
    
    conn.close()
    return render_template('admin/patients.html', patients=patients_with_age)

@app.route('/admin/appointments')
def admin_appointments():
    if session.get('role') != 'admin':
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    appointments = conn.execute('''
        SELECT a.*, p.name as patient_name, d.name as doctor_name 
        FROM appointments a 
        JOIN patients p ON a.patient_id = p.id 
        JOIN doctors d ON a.doctor_id = d.id 
        ORDER BY a.appointment_date DESC
    ''').fetchall()
    conn.close()
    return render_template('admin/appointments.html', appointments=appointments)

# PATIENT ROUTES
@app.route('/patient/dashboard')
def patient_dashboard():
    if session.get('role') != 'patient':
        flash('Please login as patient.', 'error')
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    appointments = conn.execute('''
        SELECT a.*, d.name as doctor_name, d.specialization 
        FROM appointments a 
        JOIN doctors d ON a.doctor_id = d.id 
        WHERE a.patient_id = ? 
        ORDER BY a.appointment_date DESC
    ''', (session['user_id'],)).fetchall()
    
    bills = conn.execute('SELECT * FROM bills WHERE patient_id = ? ORDER BY id DESC', (session['user_id'],)).fetchall()
    
    # Demonstrate Function: Calculate tax for bills
    bills_with_tax = []
    for bill in bills:
        total_with_tax = calculate_total_with_tax(bill['total_amount'])
        bills_with_tax.append({**dict(bill), 'total_with_tax': total_with_tax})
    
    conn.close()
    return render_template('patients/dashboard.html', appointments=appointments, bills=bills_with_tax)

@app.route('/patient/appointments')
def patient_appointments():
    if session.get('role') != 'patient':
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    appointments = conn.execute('''
        SELECT a.*, d.name as doctor_name, d.specialization, d.phone as doctor_phone
        FROM appointments a 
        JOIN doctors d ON a.doctor_id = d.id 
        WHERE a.patient_id = ? 
        ORDER BY a.appointment_date DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('patients/appointments.html', appointments=appointments)

@app.route('/patient/book-appointment', methods=['GET', 'POST'])
def book_appointment():
    if session.get('role') != 'patient':
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        notes = request.form['notes']
        
        # Demonstrate Trigger: This will automatically update doctor availability
        conn.execute('''
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], doctor_id, appointment_date, appointment_time, notes, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        
        flash('Appointment booked successfully! Doctor status updated automatically.', 'success')
        return redirect(url_for('patient_dashboard'))
    
    doctors = conn.execute("SELECT * FROM doctors WHERE availability = 'Available'").fetchall()
    conn.close()
    return render_template('patients/book_appointment.html', doctors=doctors)

@app.route('/patient/profile')
def patient_profile():
    if session.get('role') != 'patient':
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    patient = conn.execute('SELECT * FROM patients WHERE id = ?', (session['user_id'],)).fetchone()
    
    try:
        dob = patient['date_of_birth'] if patient and patient['date_of_birth'] else None
        age = calculate_patient_age(dob) if dob else 0
    except Exception:
        age = 0
    
    conn.close()
    return render_template('patients/profile.html', patient=patient, age=age)

@app.route('/patient/profile/update', methods=['POST'])
def patient_profile_update():
    if session.get('role') != 'patient':
        return redirect(url_for('login_page'))
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    date_of_birth = request.form.get('date_of_birth')
    # Normalize DOB to YYYY-MM-DD
    if date_of_birth:
        try:
            from datetime import datetime
            date_of_birth = datetime.strptime(date_of_birth.strip(), '%Y-%m-%d').strftime('%Y-%m-%d')
        except Exception:
            flash('Invalid Date of Birth format. Please use YYYY-MM-DD.', 'error')
            return redirect(url_for('patient_profile'))
    gender = request.form.get('gender')
    emergency_contact = request.form.get('emergency_contact')
    medical_history = request.form.get('medical_history')
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE patients SET 
                name = ?, 
                email = ?, 
                phone = ?, 
                address = ?, 
                date_of_birth = ?, 
                gender = ?, 
                emergency_contact = ?, 
                medical_history = ?
            WHERE id = ?
        ''', (name, email, phone, address, date_of_birth, gender, emergency_contact, medical_history, session['user_id']))
        conn.commit()
        flash('Profile updated successfully.', 'success')
    except Exception as e:
        flash(f'Error updating profile: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('patient_profile'))

# DOCTOR ROUTES
@app.route('/doctor/dashboard')
def doctor_dashboard():
    if session.get('role') != 'doctor':
        flash('Please login as doctor.', 'error')
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    # Find doctor by ID from session
    doctor = conn.execute('SELECT * FROM doctors WHERE id = ?', (session.get('user_id'),)).fetchone()
    
    if not doctor:
        flash('Doctor profile not found. Please contact administrator.', 'error')
        conn.close()
        return redirect(url_for('login_page'))
    
    appointments = conn.execute('''
        SELECT a.*, a.patient_id, p.name as patient_name, p.phone, p.gender, p.date_of_birth
        FROM appointments a 
        JOIN patients p ON a.patient_id = p.id 
        WHERE a.doctor_id = ?
        ORDER BY a.appointment_date DESC
    ''', (doctor['id'],)).fetchall()
    
    conn.close()
    
    return render_template('doctor/dashboard.html', appointments=appointments, doctor=doctor)

@app.route('/doctor/appointments')
def doctor_appointments():
    if session.get('role') != 'doctor':
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    # Find doctor by ID from session
    doctor = conn.execute('SELECT * FROM doctors WHERE id = ?', (session.get('user_id'),)).fetchone()
    
    if not doctor:
        flash('Doctor profile not found. Please contact administrator.', 'error')
        conn.close()
        return redirect(url_for('login_page'))
    
    appointments = conn.execute('''
        SELECT a.*, a.patient_id, p.name as patient_name, p.phone, p.gender, p.medical_history
        FROM appointments a 
        JOIN patients p ON a.patient_id = p.id 
        WHERE a.doctor_id = ?
        ORDER BY a.appointment_date DESC
    ''', (doctor['id'],)).fetchall()
    conn.close()
    return render_template('doctor/appointments.html', appointments=appointments)

@app.route('/doctor/patients')
def doctor_patients():
    if session.get('role') != 'doctor':
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    # Find doctor by ID from session
    doctor = conn.execute('SELECT * FROM doctors WHERE id = ?', (session.get('user_id'),)).fetchone()
    
    if not doctor:
        flash('Doctor profile not found. Please contact administrator.', 'error')
        conn.close()
        return redirect(url_for('login_page'))
    
    patients = conn.execute('''
        SELECT DISTINCT p.* 
        FROM patients p 
        JOIN appointments a ON p.id = a.patient_id 
        WHERE a.doctor_id = ?
    ''', (doctor['id'],)).fetchall()
    
    # Demonstrate Function: Calculate age for patients
    patients_with_age = []
    for patient in patients:
        try:
            dob = patient['date_of_birth'] if patient['date_of_birth'] else None
            age = calculate_patient_age(dob) if dob else 0
        except Exception:
            age = 0
        patients_with_age.append({**dict(patient), 'age': age})
    
    conn.close()
    return render_template('doctor/patients.html', patients=patients_with_age)

# View Patient Medical Records
@app.route('/doctor/patient-records/<int:patient_id>')
def view_patient_records(patient_id):
    role = session.get('role')
    if role not in ['doctor', 'receptionist']:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login_page'))

    conn = get_db_connection()

    # Get patient information
    patient = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    if not patient:
        flash('Patient not found.', 'error')
        conn.close()
        return redirect(url_for('doctor_patients' if role == 'doctor' else 'receptionist_dashboard'))

    try:
        age = calculate_patient_age(patient['date_of_birth']) if patient.get('date_of_birth') else 0
    except Exception:
        age = 0

    doctor = None
    if role == 'doctor':
        doctor = conn.execute('SELECT * FROM doctors WHERE id = ?', (session.get('user_id'),)).fetchone()
        if not doctor:
            flash('Doctor profile not found. Please contact administrator.', 'error')
            conn.close()
            return redirect(url_for('login_page'))
        appointments = conn.execute('''
            SELECT a.*, d.name as doctor_name, d.specialization
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.patient_id = ? AND a.doctor_id = ?
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        ''', (patient_id, doctor['id'])).fetchall()
        try:
            prescriptions = conn.execute('''
                SELECT pr.*, m.name as medicine_name, m.description, m.price, a.appointment_date, a.appointment_time
                FROM prescriptions pr
                JOIN medicines m ON pr.medicine_id = m.id
                JOIN appointments a ON pr.appointment_id = a.id
                WHERE a.patient_id = ? AND a.doctor_id = ?
                ORDER BY pr.prescribed_date DESC
            ''', (patient_id, doctor['id'])).fetchall()
        except Exception:
            prescriptions = []
    else:
        appointments = conn.execute('''
            SELECT a.*, d.name as doctor_name, d.specialization
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.patient_id = ?
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        ''', (patient_id,)).fetchall()
        try:
            prescriptions = conn.execute('''
                SELECT pr.*, m.name as medicine_name, m.description, m.price, a.appointment_date, a.appointment_time
                FROM prescriptions pr
                JOIN medicines m ON pr.medicine_id = m.id
                JOIN appointments a ON pr.appointment_id = a.id
                WHERE a.patient_id = ?
                ORDER BY pr.prescribed_date DESC
            ''', (patient_id,)).fetchall()
        except Exception:
            prescriptions = []

    try:
        bills = conn.execute('''
            SELECT b.*, a.appointment_date
            FROM bills b
            LEFT JOIN appointments a ON b.appointment_id = a.id
            WHERE b.patient_id = ?
            ORDER BY b.created_at DESC
        ''', (patient_id,)).fetchall()
    except Exception:
        bills = conn.execute('SELECT * FROM bills WHERE patient_id = ? ORDER BY created_at DESC', (patient_id,)).fetchall()

    conn.close()

    return render_template('doctor/patient_records.html',
                           patient=patient,
                           age=age,
                           appointments=appointments,
                           prescriptions=prescriptions,
                           bills=bills,
                           doctor=doctor)

# Add Doctor Functionality
@app.route('/admin/add-doctor', methods=['POST'])
def add_doctor():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    name = request.form['name'].strip()  # Trim whitespace
    specialization = request.form['specialization']
    phone = request.form['phone']
    email = request.form['email']
    password = request.form.get('password', '').strip()  # Get password from form
    if not password:  # If empty, use default
        password = 'doc123'
    availability = request.form.get('availability', 'Available')
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO doctors (name, specialization, phone, email, password, availability)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, specialization, phone, email, password, availability))
        conn.commit()
        # Get the newly added doctor to confirm
        new_doctor = conn.execute('SELECT * FROM doctors WHERE name = ?', (name,)).fetchone()
        conn.close()
        
        flash(f'✅ Doctor "{name}" added successfully! Login credentials: Username: "{name}" | Password: "{password}" | Role: Doctor', 'success')
        return redirect(url_for('admin_doctors'))
    except Exception as e:
        conn.close()
        flash(f'Error adding doctor: {str(e)}', 'error')
        return redirect(url_for('admin_doctors'))

# Edit Doctor Functionality
@app.route('/admin/edit-doctor/<int:doctor_id>', methods=['POST'])
def edit_doctor(doctor_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    name = request.form['name']
    specialization = request.form['specialization']
    phone = request.form['phone']
    email = request.form['email']
    password = request.form.get('password', '')  # Optional password update
    availability = request.form['availability']
    
    conn = get_db_connection()
    try:
        if password:
            # Update with password
            conn.execute('''
                UPDATE doctors 
                SET name = ?, specialization = ?, phone = ?, email = ?, password = ?, availability = ?
                WHERE id = ?
            ''', (name, specialization, phone, email, password, availability, doctor_id))
        else:
            # Update without changing password
            conn.execute('''
                UPDATE doctors 
                SET name = ?, specialization = ?, phone = ?, email = ?, availability = ?
                WHERE id = ?
            ''', (name, specialization, phone, email, availability, doctor_id))
        conn.commit()
        flash('Doctor updated successfully!', 'success')
        return redirect(url_for('admin_doctors'))
    except Exception as e:
        flash(f'Error updating doctor: {str(e)}', 'error')
        return redirect(url_for('admin_doctors'))
    finally:
        conn.close()

# Delete Doctor Functionality
@app.route('/admin/delete-doctor/<int:doctor_id>')
def delete_doctor(doctor_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    try:
        # Check if doctor has appointments
        appointments = conn.execute('SELECT COUNT(*) FROM appointments WHERE doctor_id = ?', (doctor_id,)).fetchone()[0]
        
        if appointments > 0:
            flash('Cannot delete doctor with existing appointments!', 'error')
        else:
            conn.execute('DELETE FROM doctors WHERE id = ?', (doctor_id,))
            conn.commit()
            flash('Doctor deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting doctor: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_doctors'))

# View Doctor Credentials
@app.route('/admin/view-doctor-credentials/<int:doctor_id>')
def view_doctor_credentials(doctor_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    doctor = conn.execute('SELECT * FROM doctors WHERE id = ?', (doctor_id,)).fetchone()
    conn.close()
    
    if doctor:
        doctor_password = doctor['password'] if doctor['password'] else 'doc123'
        flash(f'🔑 Doctor Login Credentials - Username: "{doctor["name"]}" | Password: "{doctor_password}" | Role: Doctor', 'info')
    else:
        flash('Doctor not found.', 'error')
    
    return redirect(url_for('admin_doctors'))

# Fix All Doctors Passwords (Migration Helper)
@app.route('/admin/fix-doctors-passwords')
def fix_doctors_passwords():
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    try:
        # Set default password 'doc123' for all doctors with NULL or empty passwords
        result = conn.execute("UPDATE doctors SET password = 'doc123' WHERE password IS NULL OR password = '' OR LENGTH(TRIM(password)) = 0")
        conn.commit()
        updated_count = result.rowcount
        conn.close()
        flash(f'✅ Fixed passwords for {updated_count} doctor(s). All doctors now have password "doc123" (or their custom password).', 'success')
    except Exception as e:
        conn.close()
        flash(f'Error fixing passwords: {str(e)}', 'error')
    
    return redirect(url_for('admin_doctors'))

# RECEPTIONIST ROUTES
@app.route('/receptionist/dashboard')
def receptionist_dashboard():
    if session.get('role') != 'receptionist':
        flash('Please login as receptionist.', 'error')
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    today_appointments = conn.execute('''
        SELECT a.*, p.name as patient_name, d.name as doctor_name 
        FROM appointments a 
        JOIN patients p ON a.patient_id = p.id 
        JOIN doctors d ON a.doctor_id = d.id 
        WHERE date(a.appointment_date) = date('now')
        ORDER BY a.appointment_time
    ''').fetchall()
    
    patients_count = conn.execute('SELECT COUNT(*) FROM patients').fetchone()[0]
    conn.close()
    
    return render_template('receptionist/dashboard.html', 
                         appointments=today_appointments, 
                         patients_count=patients_count)

@app.route('/receptionist/register-patient', methods=['GET', 'POST'])
def register_patient():
    if session.get('role') != 'receptionist':
        return redirect(url_for('login_page'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']
        emergency_contact = request.form['emergency_contact']
        medical_history = request.form['medical_history']
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO patients (name, email, phone, address, date_of_birth, gender, emergency_contact, medical_history, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, email, phone, address, date_of_birth, gender, emergency_contact, medical_history, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            flash('Patient registered successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Email already exists!', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('receptionist_dashboard'))
    
    return render_template('receptionist/register_patient.html')

@app.route('/receptionist/manage-appointments')
def manage_appointments():
    if session.get('role') != 'receptionist':
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    appointments = conn.execute('''
        SELECT a.*, p.name as patient_name, d.name as doctor_name, d.specialization
        FROM appointments a 
        JOIN patients p ON a.patient_id = p.id 
        JOIN doctors d ON a.doctor_id = d.id 
        ORDER BY a.appointment_date DESC
    ''').fetchall()
    conn.close()
    return render_template('receptionist/manage_appointment.html', appointments=appointments)

# PHARMACY ROUTES
@app.route('/pharmacy/dashboard')
def pharmacy_dashboard():
    if session.get('role') != 'pharmacy':
        flash('Please login as pharmacy staff.', 'error')
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    medicines = conn.execute('SELECT * FROM medicines ORDER BY name').fetchall()
    
    # Demonstrate Trigger: Check for low stock alerts
    alerts = conn.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 5").fetchall()
    
    conn.close()
    return render_template('pharmacy/dashboard.html', medicines=medicines, alerts=alerts)

@app.route('/pharmacy/medicines')
def pharmacy_medicines():
    if session.get('role') != 'pharmacy':
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    medicines = conn.execute('SELECT * FROM medicines ORDER BY stock_quantity ASC').fetchall()
    conn.close()
    return render_template('pharmacy/medicines.html', medicines=medicines)

@app.route('/update-stock/<int:medicine_id>', methods=['POST'])
def update_stock(medicine_id):
    if session.get('role') != 'pharmacy':
        return jsonify({'error': 'Unauthorized'}), 401
    
    new_stock = request.json.get('stock_quantity')
    
    conn = get_db_connection()
    conn.execute('UPDATE medicines SET stock_quantity = ? WHERE id = ?', (new_stock, medicine_id))
    conn.commit()
    
    # Demonstrate Trigger: This will create low stock alert if stock < 10
    alerts = conn.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 5").fetchall()
    conn.close()
    
    return jsonify({'message': 'Stock updated successfully', 'alerts': [dict(alert) for alert in alerts]})

# BILLING ROUTES
@app.route('/billing/dashboard')
def billing_dashboard():
    if session.get('role') != 'billing':
        flash('Please login as billing staff.', 'error')
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    bills = conn.execute('''
        SELECT b.*, p.name as patient_name, p.phone 
        FROM bills b 
        JOIN patients p ON b.patient_id = p.id 
        ORDER BY b.id DESC
    ''').fetchall()
    
    total_revenue = conn.execute("SELECT SUM(total_amount) FROM bills WHERE payment_status = 'Paid'").fetchone()[0] or 0
    pending_payments = conn.execute("SELECT SUM(total_amount) FROM bills WHERE payment_status = 'Pending'").fetchone()[0] or 0
    
    # Demonstrate Procedure: Generate monthly report
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_report = generate_monthly_report(current_month, current_year)
    
    medicines_revenue = conn.execute('''
        SELECT SUM(m.price)
        FROM prescriptions pr
        JOIN bills b ON pr.appointment_id = b.appointment_id
        JOIN medicines m ON pr.medicine_id = m.id
        WHERE b.payment_status = 'Paid'
    ''').fetchone()[0] or 0
    consultation_count = conn.execute("SELECT COUNT(*) FROM bills WHERE appointment_id IS NOT NULL AND payment_status = 'Paid'").fetchone()[0]
    consultation_fee = 300
    consultation_revenue = consultation_count * consultation_fee
    other_revenue = max(0, (total_revenue or 0) - (medicines_revenue or 0) - (consultation_revenue or 0))
    conn.close()
    return render_template('billing/dashboard.html', 
                         bills=bills, 
                         total_revenue=total_revenue, 
                         pending_payments=pending_payments,
                         monthly_report=monthly_report,
                         medicines_revenue=medicines_revenue,
                         consultation_revenue=consultation_revenue,
                         other_revenue=other_revenue)

@app.route('/billing/generate-bill', methods=['GET', 'POST'])
def generate_bill():
    if session.get('role') != 'billing':
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        appointment_id = request.form.get('appointment_id')
        total_amount = float(request.form['total_amount'])
        payment_method = request.form['payment_method']
        
        conn.execute('''
            INSERT INTO bills (patient_id, appointment_id, total_amount, payment_status, payment_method, created_at)
            VALUES (?, ?, ?, 'Pending', ?, ?)
        ''', (patient_id, appointment_id, total_amount, payment_method, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        
        flash('Bill generated successfully!', 'success')
        return redirect(url_for('billing_dashboard'))
    
    patients = conn.execute('SELECT id, name FROM patients').fetchall()
    appointments = conn.execute('SELECT id, patient_id FROM appointments WHERE status = "Completed"').fetchall()
    conn.close()
    
    return render_template('billing/generate_bill.html', patients=patients, appointments=appointments)

@app.route('/billing/receive-payment/<int:bill_id>', methods=['POST'])
def billing_receive_payment(bill_id):
    if session.get('role') != 'billing':
        flash('Please login as billing staff.', 'error')
        return redirect(url_for('login_page'))
    method = request.form.get('payment_method', 'Cash')
    conn = get_db_connection()
    try:
        conn.execute("UPDATE bills SET payment_status = 'Paid', payment_method = ? WHERE id = ?", (method, bill_id))
        conn.commit()
        flash('Payment recorded successfully.', 'success')
    except Exception as e:
        flash(f'Error recording payment: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('billing_dashboard'))

@app.route('/billing/reports')
def billing_reports():
    if session.get('role') != 'billing':
        flash('Please login as billing staff.', 'error')
        return redirect(url_for('login_page'))
    month = request.args.get('month', str(datetime.now().month))
    year = request.args.get('year', str(datetime.now().year))
    conn = get_db_connection()
    report = generate_monthly_report(int(month), int(year))
    bills = conn.execute('''
        SELECT b.*, p.name as patient_name, a.appointment_date
        FROM bills b
        LEFT JOIN patients p ON b.patient_id = p.id
        LEFT JOIN appointments a ON b.appointment_id = a.id
        WHERE strftime('%m', b.created_at) = ? AND strftime('%Y', b.created_at) = ?
        ORDER BY b.created_at DESC
    ''', (str(int(month)).zfill(2), year)).fetchall()
    with_tax = []
    for b in bills:
        with_tax.append({**dict(b), 'total_with_tax': calculate_total_with_tax(b['total_amount'])})
    conn.close()
    return render_template('billing/reports.html', month=int(month), year=int(year), report=report, bills=with_tax)
@app.route('/billing/bill/<int:bill_id>')
def billing_bill_detail(bill_id):
    if session.get('role') != 'billing':
        flash('Please login as billing staff.', 'error')
        return redirect(url_for('login_page'))
    conn = get_db_connection()
    bill = conn.execute('''
        SELECT b.*, p.name as patient_name, p.email as patient_email, p.phone as patient_phone,
               a.appointment_date, a.appointment_time, d.name as doctor_name, d.specialization
        FROM bills b
        LEFT JOIN patients p ON b.patient_id = p.id
        LEFT JOIN appointments a ON b.appointment_id = a.id
        LEFT JOIN doctors d ON a.doctor_id = d.id
        WHERE b.id = ?
    ''', (bill_id,)).fetchone()
    if not bill:
        conn.close()
        flash('Bill not found.', 'error')
        return redirect(url_for('billing_dashboard'))
    prescriptions = []
    if bill['appointment_id']:
        prescriptions = conn.execute('''
            SELECT m.name as medicine_name, m.price, pr.dosage, pr.duration, pr.prescribed_date
            FROM prescriptions pr
            JOIN medicines m ON pr.medicine_id = m.id
            WHERE pr.appointment_id = ?
        ''', (bill['appointment_id'],)).fetchall()
    consultation_fee = 300 if bill['appointment_id'] else 0
    medicines_total = sum([row['price'] for row in prescriptions]) if prescriptions else 0
    subtotal = medicines_total + consultation_fee
    tax = round(subtotal * 0.18, 2)
    computed_total = round(subtotal + tax, 2)
    conn.close()
    return render_template('billing/bill_detail.html', bill=bill, prescriptions=prescriptions, consultation_fee=consultation_fee, medicines_total=medicines_total, subtotal=subtotal, tax=tax, computed_total=computed_total)

@app.route('/billing/update-total/<int:bill_id>', methods=['POST'])
def billing_update_total(bill_id):
    if session.get('role') != 'billing':
        flash('Please login as billing staff.', 'error')
        return redirect(url_for('login_page'))
    try:
        new_total = float(request.form.get('computed_total', '0'))
    except ValueError:
        flash('Invalid total amount.', 'error')
        return redirect(url_for('billing_bill_detail', bill_id=bill_id))
    conn = get_db_connection()
    try:
        conn.execute('UPDATE bills SET total_amount = ? WHERE id = ?', (new_total, bill_id))
        conn.commit()
        flash('Bill total updated successfully.', 'success')
    except Exception as e:
        flash(f'Error updating bill: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('billing_bill_detail', bill_id=bill_id))

# DEMONSTRATION ROUTES FOR DBMS FEATURES
@app.route('/demo/discharge-patient/<int:patient_id>')
def demo_discharge_patient(patient_id):
    """Demonstrate Stored Procedure"""
    if session.get('role') not in ['admin', 'receptionist']:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login_page'))
    
    result = discharge_patient(patient_id)
    flash(result, 'success')
    return redirect(url_for('admin_dashboard' if session['role'] == 'admin' else 'receptionist_dashboard'))

@app.route('/discharge-patient', methods=['POST'])
def discharge_patient_action():
    if session.get('role') not in ['admin', 'receptionist']:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login_page'))
    patient_id = request.form.get('patient_id')
    try:
        patient_id = int(patient_id)
    except (TypeError, ValueError):
        flash('Invalid patient ID.', 'error')
        return redirect(url_for('admin_dbms_features' if session.get('role') == 'admin' else 'receptionist_dashboard'))
    result = discharge_patient(patient_id)
    flash(result, 'success')
    ref = request.referrer
    if ref:
        return redirect(ref)
    return redirect(url_for('admin_appointments' if session.get('role') == 'admin' else 'manage_appointments'))

@app.route('/demo/complex-queries')
def demo_complex_queries():
    """Demonstrate Complex Queries"""
    if session.get('role') != 'admin':
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    
    # 1. Nested Query: Patients with busy doctors
    nested_query = conn.execute('''
        SELECT name FROM patients 
        WHERE id IN (
            SELECT patient_id FROM appointments 
            WHERE doctor_id IN (
                SELECT id FROM doctors WHERE availability = 'Busy'
            )
        )
    ''').fetchall()
    
    # 2. Join Query: Detailed appointment info
    join_query = conn.execute('''
        SELECT 
            p.name as patient_name,
            d.name as doctor_name,
            d.specialization,
            a.appointment_date,
            a.status
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        ORDER BY a.appointment_date DESC
    ''').fetchall()
    
    # 3. Aggregate Query: Revenue by doctor
    aggregate_query = conn.execute('''
        SELECT 
            d.name,
            COUNT(a.id) as total_appointments,
            SUM(b.total_amount) as total_revenue
        FROM doctors d
        LEFT JOIN appointments a ON d.id = a.doctor_id
        LEFT JOIN bills b ON a.id = b.appointment_id
        GROUP BY d.id
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin/complex_queries.html',
                         nested_query=nested_query,
                         join_query=join_query,
                         aggregate_query=aggregate_query)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully!', 'info')
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
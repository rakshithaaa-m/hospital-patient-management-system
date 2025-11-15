-- Hospital Management System Database Schema
-- This file contains the complete database structure

-- Create database (run this first)
CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;

-- Users table for staff authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'doctor', 'receptionist', 'pharmacy', 'billing') NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    address TEXT,
    date_of_birth DATE,
    gender ENUM('Male', 'Female', 'Other'),
    emergency_contact VARCHAR(15),
    medical_history TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Doctors table
CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100),
    phone VARCHAR(15),
    email VARCHAR(100),
    availability ENUM('Available', 'Busy', 'On Leave') DEFAULT 'Available'
);

-- Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status ENUM('Scheduled', 'Completed', 'Cancelled', 'No Show') DEFAULT 'Scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

-- Bills table
CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    appointment_id INTEGER,
    bill_date DATE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_status ENUM('Pending', 'Paid', 'Partial') DEFAULT 'Pending',
    payment_method ENUM('Cash', 'Card', 'Insurance', 'Online'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(id)
);

-- Medicines table
CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(8,2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    manufacturer VARCHAR(100)
);

-- Prescriptions table
CREATE TABLE IF NOT EXISTS prescriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id INTEGER NOT NULL,
    medicine_id INTEGER NOT NULL,
    dosage VARCHAR(50),
    duration VARCHAR(50),
    instructions TEXT,
    prescribed_date DATE NOT NULL,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id),
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
);

-- Alerts table for system notifications
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT NOT NULL,
    alert_type VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- DATABASE TRIGGERS
-- =============================================================================

-- Trigger 1: Update doctor availability when appointment is booked
DELIMITER //
CREATE TRIGGER update_doctor_availability 
AFTER INSERT ON appointments
FOR EACH ROW
BEGIN
    UPDATE doctors SET availability = 'Busy' 
    WHERE id = NEW.doctor_id;
END//
DELIMITER ;

-- Trigger 2: Low stock alert for medicines
DELIMITER //
CREATE TRIGGER low_stock_alert 
AFTER UPDATE ON medicines
FOR EACH ROW
BEGIN
    IF NEW.stock_quantity < 10 THEN
        INSERT INTO alerts (message, alert_type) 
        VALUES (CONCAT('Low stock alert for ', NEW.name), 'warning');
    END IF;
END//
DELIMITER ;

-- Trigger 3: Auto-complete old appointments
DELIMITER //
CREATE TRIGGER auto_complete_appointment 
AFTER INSERT ON appointments
FOR EACH ROW
BEGIN
    UPDATE appointments SET status = 'Completed' 
    WHERE id = NEW.id AND TIMESTAMPDIFF(HOUR, CONCAT(appointment_date, ' ', appointment_time), NOW()) > 24;
END//
DELIMITER ;

-- =============================================================================
-- SAMPLE DATA INSERTION
-- =============================================================================

-- Insert sample users
INSERT INTO users (username, password, role, email) VALUES
('admin', 'admin123', 'admin', 'admin@hospital.com'),
('doctor1', 'doc123', 'doctor', 'doctor1@hospital.com'),
('reception1', 'recep123', 'receptionist', 'reception@hospital.com'),
('pharmacy1', 'pharma123', 'pharmacy', 'pharmacy@hospital.com'),
('billing1', 'bill123', 'billing', 'billing@hospital.com');

-- Insert sample patients
INSERT INTO patients (name, email, phone, address, date_of_birth, gender, emergency_contact, medical_history) VALUES
('Alice Brown', 'alice@email.com', '9876543201', '123 Main St, Bangalore', '1990-05-15', 'Female', '9876543299', 'No significant history'),
('Bob Wilson', 'bob@email.com', '9876543202', '456 Oak Ave, Bangalore', '1985-08-22', 'Male', '9876543298', 'Hypertension'),
('Carol Davis', 'carol@email.com', '9876543203', '789 Pine Rd, Bangalore', '1992-12-10', 'Female', '9876543297', 'Diabetes');

-- Insert sample doctors
INSERT INTO doctors (name, specialization, phone, email, availability) VALUES
('Dr. John Smith', 'Cardiology', '9876543210', 'dr.smith@hospital.com', 'Available'),
('Dr. Sarah Johnson', 'Pediatrics', '9876543211', 'sarah.j@hospital.com', 'Available'),
('Dr. Mike Wilson', 'Orthopedics', '9876543212', 'mike.w@hospital.com', 'Available'),
('Dr. Emily Chen', 'Dermatology', '9876543213', 'emily.c@hospital.com', 'Busy');

-- Insert sample appointments
INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status, notes) VALUES
(1, 1, '2024-12-20', '10:00:00', 'Scheduled', 'Regular heart checkup'),
(2, 2, '2024-12-21', '11:00:00', 'Completed', 'Fever and cold'),
(3, 3, '2024-12-22', '14:00:00', 'Scheduled', 'Knee pain consultation'),
(1, 4, '2024-12-23', '15:30:00', 'Scheduled', 'Skin allergy');

-- Insert sample bills
INSERT INTO bills (patient_id, appointment_id, bill_date, total_amount, payment_status, payment_method) VALUES
(1, 1, '2024-12-20', 500.00, 'Paid', 'Card'),
(2, 2, '2024-12-21', 750.00, 'Pending', 'Cash'),
(3, 3, '2024-12-22', 1200.00, 'Pending', 'Insurance'),
(1, 4, '2024-12-23', 300.00, 'Paid', 'Online');

-- Insert sample medicines
INSERT INTO medicines (name, description, price, stock_quantity, manufacturer) VALUES
('Paracetamol', 'Pain and fever relief', 5.00, 100, 'Pharma Corp'),
('Amoxicillin', 'Antibiotic for infections', 15.50, 50, 'Medi Labs'),
('Vitamin C', 'Immune system booster', 8.75, 200, 'Health Plus'),
('Ibuprofen', 'Anti-inflammatory pain reliever', 12.25, 5, 'PainFree Inc');

-- =============================================================================
-- DATABASE INDEXES FOR PERFORMANCE
-- =============================================================================

CREATE INDEX idx_appointments_patient_id ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor_id ON appointments(doctor_id);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_bills_patient_id ON bills(patient_id);
CREATE INDEX idx_bills_payment_status ON bills(payment_status);
CREATE INDEX idx_medicines_stock ON medicines(stock_quantity);

-- =============================================================================
-- DATABASE VIEWS FOR REPORTING
-- =============================================================================

-- View for appointment summary
CREATE VIEW appointment_summary AS
SELECT 
    a.id,
    p.name as patient_name,
    d.name as doctor_name,
    a.appointment_date,
    a.appointment_time,
    a.status
FROM appointments a
JOIN patients p ON a.patient_id = p.id
JOIN doctors d ON a.doctor_id = d.id;

-- View for revenue report
CREATE VIEW revenue_report AS
SELECT 
    b.bill_date,
    COUNT(*) as bill_count,
    SUM(b.total_amount) as total_revenue,
    AVG(b.total_amount) as average_bill
FROM bills b
GROUP BY b.bill_date;

-- View for medicine inventory status
CREATE VIEW medicine_inventory AS
SELECT 
    name,
    stock_quantity,
    CASE 
        WHEN stock_quantity > 20 THEN 'In Stock'
        WHEN stock_quantity > 5 THEN 'Low Stock'
        ELSE 'Critical'
    END as stock_status
FROM medicines;

-- =============================================================================
-- STORED PROCEDURES
-- =============================================================================

-- Procedure for patient discharge process
DELIMITER //
CREATE PROCEDURE DischargePatient(IN patient_id INT)
BEGIN
    -- Update appointment status
    UPDATE appointments SET status = 'Completed' 
    WHERE patient_id = patient_id AND status = 'Scheduled';
    
    -- Generate final bill if not exists
    IF NOT EXISTS (SELECT 1 FROM bills WHERE patient_id = patient_id AND payment_status = 'Pending') THEN
        INSERT INTO bills (patient_id, bill_date, total_amount, payment_status)
        VALUES (patient_id, CURDATE(), CalculateTotalCharges(patient_id), 'Pending');
    END IF;
    
    -- Return success message
    SELECT 'Patient discharged successfully' as result;
END//
DELIMITER ;

-- Procedure for monthly financial report
DELIMITER //
CREATE PROCEDURE GenerateMonthlyReport(IN month INT, IN year INT)
BEGIN
    SELECT 
        COUNT(*) as total_bills,
        SUM(total_amount) as total_revenue,
        AVG(total_amount) as average_bill,
        SUM(CASE WHEN payment_status = 'Paid' THEN total_amount ELSE 0 END) as collected_amount
    FROM bills 
    WHERE MONTH(bill_date) = month AND YEAR(bill_date) = year;
END//
DELIMITER ;

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to calculate patient age
DELIMITER //
CREATE FUNCTION CalculateAge(date_of_birth DATE) 
RETURNS INT
READS SQL DATA
DETERMINISTIC
BEGIN
    RETURN TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE());
END//
DELIMITER ;

-- Function to calculate total with tax
DELIMITER //
CREATE FUNCTION CalculateTotalWithTax(amount DECIMAL(10,2)) 
RETURNS DECIMAL(10,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    RETURN amount + (amount * 0.18); -- 18% GST
END//
DELIMITER ;
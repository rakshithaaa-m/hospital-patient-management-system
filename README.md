# **Hospital Management System**

## **Overview**

The Hospital Management System is a role-based web application built using **Flask + MySQL** to streamline hospital operations such as:

* Patient registration & profile management
* Appointment booking & scheduling
* Doctor dashboard & appointment updates
* Pharmacy inventory and low-stock alerts
* Prescriptions & medicine mapping
* Admin controls
* MySQL triggers, stored procedures, functions & analytical queries

The project implements full **CRUD operations**, **referential integrity**, **constraints**, **ER design**, **normalized schema**, and **server-side logic** with SQL procedures and triggers.

---

## **Features**

### Doctor

* View daily appointments
* Update appointment status (Completed / Cancelled / No-show)
* Create/update prescriptions

### Patient

* Register & manage profile
* Book appointments
* View past & upcoming appointments

### Receptionist

* Book appointments on behalf of patients
* Manage patient info

### Pharmacy

* View and update medicine stock
* Identify low-stock medicines
* Process prescription orders

### Admin

* Add new doctors, medicines, and system users
* Oversee hospital operations

---

## **Database Used**

**MySQL**

Includes:

* 12+ relational tables
* Primary & foreign keys
* Cascading rules
* Unique constraints on appointment time slots
* Stored Procedures (e.g., safe booking)
* Trigger (audit logs on status updates)
* Function (patient age calculation)
* Join, nested & aggregate analytical queries

SQL schema stored in:

```
database.sql
```

---

## 📁 **Project Structure**

```
Hospital-Management-System/
│
├── app.py                   # Flask backend
├── config.py                # Database configuration
├── requirements.txt         # Python dependencies
├── database.sql             # Schema + DDL + procedures + triggers
├── queries.sql              # Analytical SQL queries
│
├── templates/               # HTML Jinja templates
│   ├── patients/
│   ├── doctors/
│   ├── pharmacy/
│   ├── admin/
│   └── receptionist/
│
└── static/                  # CSS, JS, images
```

---

## **How to Run Locally**

### **Install Dependencies**

Make sure Python 3.10+ is installed.

```bash
pip install -r requirements.txt
```

### **Create the Database**

Open MySQL terminal:

```bash
mysql -u root -p < database.sql
```

This will:

* Create `hospitaldb`
* Create all tables
* Insert sample data
* Add triggers, functions, procedures

### **Configure Database Credentials**

Open **config.py**:

```python
db_config = {
    'host': 'localhost',
    'user': 'YOUR_MYSQL_USERNAME',
    'password': 'YOUR_MYSQL_PASSWORD',
    'database': 'hospitaldb'
}
```

### **Run Flask Server**

```bash
flask run
```

or

```bash
python app.py
```

Visit:

**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## **CRUD Operations Implemented**

* Patients: Create, Update, View
* Doctors: Add, Update, Delete
* Medicine: Insert, Update stock, Low stock
* Appointments: Create, List, Update status, Delete
* Prescriptions: Create, map medicines

---

## **Stored Procedures & Functions**

Included in `database.sql`:

### **Procedure: `sp_book_appointment`**

Ensures safe booking without time slot conflicts.

### **Function: `fn_patient_age(pid)`**

Returns age from DOB.

### **Trigger: `trg_appointment_status_change`**

Logs status modifications into `appointment_logs`.

---

## **Sample Analytical Queries**

Stored in `queries.sql`:

* Appointments per doctor (last 7 days)
* Total medicines low in stock
* Patients with more than 3 appointments
* Daily appointments summary

---

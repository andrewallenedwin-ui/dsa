import sqlite3
from datetime import datetime, timedelta
import random
import os
import shutil

# Vercel serverless read-only filesystem workaround
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/admissions.db"
    src_db = os.path.join(os.path.dirname(__file__), "admissions.db")
    if os.path.exists(src_db) and not os.path.exists(DB_PATH):
        try:
            shutil.copyfile(src_db, DB_PATH)
        except Exception as e:
            print(f"Warning: Could not copy seed DB to /tmp: {e}")
else:
    DB_PATH = "admissions.db"

# Comprehensive Arts & Sciences Curriculum (Aided and SFS Streams)
DEFAULT_COURSES = [
    # --- ARTS & HUMANITIES ---
    {"name": "B.A Tamil", "code": "BA-TAM", "category": "Arts & Humanities", "stream": "Aided", "total_seats": 25, "cutoff": 60.0, "tuition_fee": 4850},
    {"name": "B.A English", "code": "BA-ENG-AID", "category": "Arts & Humanities", "stream": "Aided", "total_seats": 30, "cutoff": 78.0, "tuition_fee": 5850},
    {"name": "B.A English (SFS)", "code": "BA-ENG-SFS", "category": "Arts & Humanities", "stream": "SFS", "total_seats": 30, "cutoff": 68.0, "tuition_fee": 19500},
    {"name": "B.A History", "code": "BA-HIS-AID", "category": "Arts & Humanities", "stream": "Aided", "total_seats": 25, "cutoff": 60.0, "tuition_fee": 4850},
    {"name": "B.A History (SFS)", "code": "BA-HIS-SFS", "category": "Arts & Humanities", "stream": "SFS", "total_seats": 25, "cutoff": 55.0, "tuition_fee": 17500},
    {"name": "B.A Political Science", "code": "BA-POL", "category": "Arts & Humanities", "stream": "Aided", "total_seats": 25, "cutoff": 65.0, "tuition_fee": 5150},
    {"name": "B.A Philosophy", "code": "BA-PHIL", "category": "Arts & Humanities", "stream": "Aided", "total_seats": 20, "cutoff": 58.0, "tuition_fee": 4650},
    {"name": "B.A Journalism", "code": "BA-JOURN", "category": "Arts & Humanities", "stream": "SFS", "total_seats": 25, "cutoff": 72.0, "tuition_fee": 23500},

    # --- SCIENCES ---
    {"name": "B.Sc Mathematics", "code": "BSC-MAT-AID", "category": "Sciences", "stream": "Aided", "total_seats": 25, "cutoff": 75.0, "tuition_fee": 6250},
    {"name": "B.Sc Mathematics (SFS)", "code": "BSC-MAT-SFS", "category": "Sciences", "stream": "SFS", "total_seats": 25, "cutoff": 65.0, "tuition_fee": 21500},
    {"name": "B.Sc Physics", "code": "BSC-PHY-AID", "category": "Sciences", "stream": "Aided", "total_seats": 25, "cutoff": 76.0, "tuition_fee": 7850},
    {"name": "B.Sc Physics (SFS)", "code": "BSC-PHY-SFS", "category": "Sciences", "stream": "SFS", "total_seats": 25, "cutoff": 66.0, "tuition_fee": 24000},
    {"name": "B.Sc Chemistry", "code": "BSC-CHE-AID", "category": "Sciences", "stream": "Aided", "total_seats": 25, "cutoff": 74.0, "tuition_fee": 8250},
    {"name": "B.Sc Chemistry (SFS)", "code": "BSC-CHE-SFS", "category": "Sciences", "stream": "SFS", "total_seats": 25, "cutoff": 65.0, "tuition_fee": 25500},
    {"name": "B.Sc Botany", "code": "BSC-BOT", "category": "Sciences", "stream": "Aided", "total_seats": 20, "cutoff": 62.0, "tuition_fee": 7450},
    {"name": "B.Sc Zoology", "code": "BSC-ZOO", "category": "Sciences", "stream": "Aided", "total_seats": 20, "cutoff": 62.0, "tuition_fee": 7450},
    {"name": "B.Sc Statistics", "code": "BSC-STAT", "category": "Sciences", "stream": "Aided", "total_seats": 25, "cutoff": 70.0, "tuition_fee": 6500},
    {"name": "B.Sc Microbiology", "code": "BSC-MIC", "category": "Sciences", "stream": "SFS", "total_seats": 25, "cutoff": 74.0, "tuition_fee": 28000},
    {"name": "B.Sc Computer Science", "code": "BSC-CS-AID", "category": "Sciences", "stream": "Aided", "total_seats": 30, "cutoff": 85.0, "tuition_fee": 11500},
    {"name": "B.Sc Computer Science (SFS)", "code": "BSC-CS-SFS", "category": "Sciences", "stream": "SFS", "total_seats": 30, "cutoff": 78.0, "tuition_fee": 34500},
    {"name": "B.Sc Geography", "code": "BSC-GEO", "category": "Sciences", "stream": "Aided", "total_seats": 20, "cutoff": 60.0, "tuition_fee": 6800},
    {"name": "B.Sc Psychology", "code": "BSC-PSY", "category": "Sciences", "stream": "SFS", "total_seats": 25, "cutoff": 80.0, "tuition_fee": 26000},

    # --- COMMERCE & MANAGEMENT ---
    {"name": "B.Com General", "code": "BCOM-AID", "category": "Commerce & Management", "stream": "Aided", "total_seats": 35, "cutoff": 86.0, "tuition_fee": 6950},
    {"name": "B.Com General (SFS)", "code": "BCOM-SFS", "category": "Commerce & Management", "stream": "SFS", "total_seats": 35, "cutoff": 80.0, "tuition_fee": 32000},
    {"name": "B.Com Accounting and Finance", "code": "BCOM-AF", "category": "Commerce & Management", "stream": "SFS", "total_seats": 35, "cutoff": 82.0, "tuition_fee": 34000},
    {"name": "B.Com Professional Accounting", "code": "BCOM-PA", "category": "Commerce & Management", "stream": "SFS", "total_seats": 30, "cutoff": 84.0, "tuition_fee": 36000},
    {"name": "BBA Business Administration", "code": "BBA-SFS", "category": "Commerce & Management", "stream": "SFS", "total_seats": 30, "cutoff": 78.0, "tuition_fee": 35000},

    # --- PROFESSIONAL & SPECIAL STREAMS ---
    {"name": "B.S.W Social Work", "code": "BSW-AID", "category": "Professional & Special Streams", "stream": "Aided", "total_seats": 20, "cutoff": 60.0, "tuition_fee": 6500},
    {"name": "B.S.W Social Work (SFS)", "code": "BSW-SFS", "category": "Professional & Special Streams", "stream": "SFS", "total_seats": 20, "cutoff": 58.0, "tuition_fee": 21000},
    {"name": "B.C.A Computer Applications", "code": "BCA-SFS", "category": "Professional & Special Streams", "stream": "SFS", "total_seats": 30, "cutoff": 80.0, "tuition_fee": 36500},
    {"name": "B.Sc Visual Communication", "code": "BSC-VISCOM", "category": "Professional & Special Streams", "stream": "SFS", "total_seats": 25, "cutoff": 76.0, "tuition_fee": 38000},
    {"name": "B.Sc Data Science", "code": "BSC-DS", "category": "Professional & Special Streams", "stream": "SFS", "total_seats": 25, "cutoff": 83.0, "tuition_fee": 37500},
    {"name": "B.Sc Physical Education", "code": "BSC-PED", "category": "Professional & Special Streams", "stream": "Aided", "total_seats": 20, "cutoff": 55.0, "tuition_fee": 5800},
]


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_no TEXT UNIQUE,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            department TEXT NOT NULL,
            stream TEXT DEFAULT 'Aided',
            course_code TEXT DEFAULT '',
            marks REAL NOT NULL,
            m1 REAL DEFAULT 0,
            m2 REAL DEFAULT 0,
            m3 REAL DEFAULT 0,
            m4 REAL DEFAULT 0,
            m5 REAL DEFAULT 0,
            m6 REAL DEFAULT 0,
            marks_total REAL DEFAULT 0,
            gender TEXT DEFAULT 'Not Specified',
            status TEXT DEFAULT 'pending',
            queue_position INTEGER,
            cert_status TEXT DEFAULT 'pending',
            cert_remarks TEXT DEFAULT '',
            cert_docs TEXT DEFAULT '',
            rejection_reason TEXT DEFAULT '',
            application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration check: ensure new columns exist if table was already created
    cursor.execute("PRAGMA table_info(students)")
    existing_cols = {col["name"] for col in cursor.fetchall()}
    columns_to_add = [
        ("m1", "REAL DEFAULT 0"),
        ("m2", "REAL DEFAULT 0"),
        ("m3", "REAL DEFAULT 0"),
        ("m4", "REAL DEFAULT 0"),
        ("m5", "REAL DEFAULT 0"),
        ("m6", "REAL DEFAULT 0"),
        ("marks_total", "REAL DEFAULT 0"),
        ("course_code", "TEXT DEFAULT ''"),
        ("cert_status", "TEXT DEFAULT 'pending'"),
        ("cert_remarks", "TEXT DEFAULT ''"),
        ("cert_docs", "TEXT DEFAULT ''"),
        ("rejection_reason", "TEXT DEFAULT ''")
    ]
    for col_name, col_def in columns_to_add:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE students ADD COLUMN {col_name} {col_def}")

    # Backfill realistic rejection reasons for existing rejected records
    cursor.execute("SELECT id, marks, department, cert_status FROM students WHERE status = 'rejected'")
    rej_rows = cursor.fetchall()
    for idx, row in enumerate(rej_rows):
        s_id = row["id"]
        s_marks = row["marks"]
        if idx % 3 == 0:
            reason = "Certificate Pending: Original Transfer Certificate (TC) & 12th Marksheet verification unfulfilled"
        elif idx % 3 == 1:
            reason = f"Marks Below Cutoff: HSC aggregate ({s_marks}%) did not meet minimum department cutoff"
        else:
            reason = "Admission Fees Issue: Prescribed first semester tuition fee remittance deadline expired"
        cursor.execute("UPDATE students SET rejection_reason = ? WHERE id = ?", (reason, s_id))

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            seat_number TEXT NOT NULL,
            department TEXT NOT NULL,
            stream TEXT NOT NULL,
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL,
            student_id INTEGER,
            admin_note TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            undone INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            stream TEXT NOT NULL,
            total_seats INTEGER NOT NULL,
            cutoff REAL NOT NULL,
            tuition_fee INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Check if courses table needs migration or seeding
    cursor.execute("PRAGMA table_info(courses)")
    c_cols = {col["name"] for col in cursor.fetchall()}
    if "tuition_fee" not in c_cols:
        cursor.execute("ALTER TABLE courses ADD COLUMN tuition_fee INTEGER DEFAULT 0")

    cursor.execute("SELECT COUNT(*) as cnt FROM courses")
    existing_count = cursor.fetchone()["cnt"]
    if existing_count < len(DEFAULT_COURSES):
        cursor.execute("DELETE FROM courses")
        for c in DEFAULT_COURSES:
            cursor.execute("""
                INSERT OR REPLACE INTO courses (name, code, category, stream, total_seats, cutoff, tuition_fee)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (c["name"], c["code"], c["category"], c["stream"], c["total_seats"], c["cutoff"], c.get("tuition_fee", 0)))
        total_course_seats = sum(c["total_seats"] for c in DEFAULT_COURSES)
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value)
            VALUES ('total_seats', ?)
        """, (str(total_course_seats),))
        conn.commit()

    conn.close()

    # Seed 1000+ demo applicants if database has fewer than 1000 students
    seed_demo_if_empty()


def generate_alphanumeric_id(stream, department, seq_num):
    """
    Generates a realistic Alphanumeric Unique Application ID:
    Format: ABC26-{STREAM_CODE}-{COURSE_ABBR}-{SEQ:04d}
    Examples: ABC26-AID-CS-1001, ABC26-SFS-BCOM-2042
    """
    stream_prefix = "AID" if "aided" in stream.lower() else "SFS"
    
    # Extract concise abbreviation from department
    clean_dept = department.replace("B.Sc ", "").replace("B.A ", "").replace("B.Com ", "").replace("B.S.W ", "").replace("B.C.A ", "")
    words = clean_dept.split()
    abbr = "".join([w[0].upper() for w in words[:2]]) if len(words) >= 2 else clean_dept[:3].upper()
    
    return f"ABC26-{stream_prefix}-{abbr}-{seq_num:04d}"


def seed_demo_if_empty(force=False):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM students")
    count = cursor.fetchone()["count"]

    if count < 2000 or force:
        # Reset tables for clean 2,475+ competitive Chennai overfilling cohort generation
        cursor.execute("DELETE FROM admissions")
        cursor.execute("DELETE FROM admin_actions")
        cursor.execute("DELETE FROM students")

        first_names = [
            "Aarav", "Aditi", "Akash", "Ananya", "Arjun", "Ashwin", "Bala", "Bhavani",
            "Deepak", "Deepika", "Dinesh", "Divya", "Gautam", "Harish", "Ishwarya",
            "Karthik", "Kavitha", "Keerthana", "Madhav", "Manoj", "Meera", "Mithun",
            "Nandini", "Naveen", "Nithya", "Pavithra", "Pooja", "Pradeep", "Priya",
            "Rahul", "Rajesh", "Rithanya", "Rohan", "Rohit", "Sandhya", "Sanjay",
            "Saravanan", "Shalini", "Siddharth", "Sneha", "Subhash", "Surya", "Swathi",
            "Tarun", "Varun", "Vignesh", "Vijay", "Vikram", "Vinoth", "Vishnu", "Kalyani",
            "Mukund", "Swaminathan", "Preethi", "Vasanth", "Shruti", "Gopinath", "Revathi",
            "Anirudh", "Archana", "Bharath", "Charanya", "Dhruv", "Gayathri", "Hemant"
        ]

        last_names = [
            "Sharma", "Ramanathan", "Menon", "Sundaram", "Verma", "Iyer", "Kumar",
            "Patil", "Rao", "Nambiar", "Deshmukh", "Natarajan", "Chandran", "Balaji",
            "Venkatesh", "Selvam", "Panicker", "Krishnan", "Subramanian", "Mohan",
            "Raj", "Sankar", "Prasad", "Murali", "Nair", "Pillai", "Reddy", "Naidu",
            "Chettiar", "Gounder", "Anand", "Chari", "Raghavan", "Srinivasan", "Sridhar",
            "Swamy", "Acharya", "Chopra", "Kulkarni", "Bhatt"
        ]

        # 33 courses * 75 applicants = 2,475 realistic competitive applicants (290% Overfill Ratio)
        students_per_course = 75
        base_time = datetime.now() - timedelta(days=4)
        hours_pool = ["09", "10", "11", "12", "13", "14", "15", "16", "17"]

        admissions_to_insert = []
        students_to_insert = []

        student_counter = 1
        for c_idx, course in enumerate(DEFAULT_COURSES):
            course_name = course["name"]
            course_code = course["code"]
            stream = course["stream"]
            cutoff = course["cutoff"]
            total_seats = course["total_seats"]

            # Overfilling admission: 95%-100% capacity filled, leaving tiny margin for queue waitlist
            admitted_count = total_seats if (c_idx % 4 == 0) else max(1, total_seats - (1 if c_idx % 2 == 0 else 2))
            rejected_count = 3

            for i in range(students_per_course):
                fn = first_names[(c_idx * students_per_course + i) % len(first_names)]
                ln = last_names[(c_idx * 5 + i) % len(last_names)]
                student_name = f"{fn} {ln}"
                email = f"{fn.lower()}.{ln.lower()}.{student_counter:04d}@abcadmissions.edu"
                phone = f"9840{100000 + (student_counter % 900000):06d}"
                gender = "Female" if i % 2 == 0 else "Male"

                # Generate 6 realistic subject marks centered on cutoff & stream
                rejection_reason = ""
                if i < admitted_count:
                    # Admitted cohort (high marks, verified certificates)
                    base_m = min(98.5, max(cutoff + 1.0, cutoff + (admitted_count - i) * 0.8 + random.uniform(-1.0, 2.0)))
                    status = "admitted"
                    cert_status = "verified"
                    queue_pos = None
                elif i < admitted_count + rejected_count:
                    # Disqualified / Rejected cohort (below cutoff, certs pending, or fee deadline passed)
                    base_m = max(42.0, cutoff - 12.0 - random.uniform(0.5, 8.0))
                    status = "rejected"
                    rej_type_idx = i - admitted_count
                    if rej_type_idx == 0:
                        cert_status = "flagged"
                        rejection_reason = "Certificate Pending: Original Transfer Certificate (TC) & 12th Marksheet verification unfulfilled"
                    elif rej_type_idx == 1:
                        cert_status = "rejected"
                        rejection_reason = f"Marks Below Cutoff: HSC aggregate ({round(base_m, 1)}%) below minimum cutoff of {cutoff}%"
                    else:
                        cert_status = "verified"
                        rejection_reason = "Admission Fees Issue: Prescribed first semester tuition fee remittance deadline expired"
                    queue_pos = None
                else:
                    # Overflowing Waitlist Cohort in FIFO Subject Queue
                    base_m = min(96.0, max(50.0, cutoff + random.uniform(-10.0, 8.0)))
                    status = "pending"
                    cert_status = "verified" if (i % 3 != 0) else "pending"
                    queue_pos = (i - (admitted_count + rejected_count)) + 1

                m1 = round(min(100.0, max(40.0, base_m + random.uniform(-3.0, 3.5))), 1)
                m2 = round(min(100.0, max(40.0, base_m + random.uniform(-3.0, 3.5))), 1)
                m3 = round(min(100.0, max(40.0, base_m + random.uniform(-4.0, 4.0))), 1)
                m4 = round(min(100.0, max(40.0, base_m + random.uniform(-4.0, 4.0))), 1)
                m5 = round(min(100.0, max(40.0, base_m + random.uniform(-4.0, 4.0))), 1)
                m6 = round(min(100.0, max(40.0, base_m + random.uniform(-3.5, 3.5))), 1)
                marks_total = round(m1 + m2 + m3 + m4 + m5 + m6, 1)
                marks_avg = round(marks_total / 6.0, 2)

                app_no = generate_alphanumeric_id(stream, course_name, student_counter + 1000)
                app_date = (base_time + timedelta(minutes=student_counter * 2)).strftime("%Y-%m-%d %H:%M:%S")

                cert_docs = '{"marksheet_10":true,"marksheet_12":true,"tc":true,"community_cert":true}'
                cert_remarks = "All 4 original certificates verified" if cert_status == "verified" else ("Community certificate unclear" if cert_status == "flagged" else "")

                students_to_insert.append((
                    student_counter, app_no, student_name, email, phone, course_name, stream, course_code,
                    marks_avg, m1, m2, m3, m4, m5, m6, marks_total, gender, status, queue_pos,
                    cert_status, cert_remarks, cert_docs, rejection_reason, app_date
                ))

                if status == "admitted":
                    seat_num = f"{course_code}-{i + 1:02d}"
                    hr = hours_pool[(student_counter + i) % len(hours_pool)]
                    allocated_time = f"2026-09-18 {hr}:{((student_counter * 7) % 60):02d}:00"
                    admissions_to_insert.append((
                        student_counter, seat_num, course_name, stream, allocated_time, "active"
                    ))

                student_counter += 1

        cursor.executemany("""
            INSERT INTO students
            (id, app_no, name, email, phone, department, stream, course_code,
             marks, m1, m2, m3, m4, m5, m6, marks_total, gender, status, queue_position,
             cert_status, cert_remarks, cert_docs, rejection_reason, application_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, students_to_insert)

        cursor.executemany("""
            INSERT INTO admissions
            (student_id, seat_number, department, stream, allocated_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, admissions_to_insert)

        conn.commit()

    conn.close()


def add_student(data):
    conn = get_db()
    cursor = conn.cursor()

    dept = data["department"]
    cursor.execute("SELECT code, stream FROM courses WHERE name = ?", (dept,))
    c_row = cursor.fetchone()
    if c_row:
        stream = data.get("stream") or c_row["stream"]
        course_code = c_row["code"]
    else:
        stream = data.get("stream", "Aided")
        course_code = "GEN"

    # Handle 6 subject marks calculation
    m1 = float(data.get("m1", 0))
    m2 = float(data.get("m2", 0))
    m3 = float(data.get("m3", 0))
    m4 = float(data.get("m4", 0))
    m5 = float(data.get("m5", 0))
    m6 = float(data.get("m6", 0))

    if m1 > 0 or m2 > 0 or m3 > 0 or m4 > 0 or m5 > 0 or m6 > 0:
        marks_total = round(m1 + m2 + m3 + m4 + m5 + m6, 1)
        marks = round(marks_total / 6.0, 2)
    else:
        marks = float(data.get("marks", 0))
        marks_total = round(marks * 6.0, 1)
        m1 = m2 = m3 = m4 = m5 = m6 = marks

    cursor.execute("SELECT COUNT(*) as count FROM students")
    total_count = cursor.fetchone()["count"]
    app_no = generate_alphanumeric_id(stream, dept, total_count + 1001)

    cert_status = data.get("cert_status", "pending")
    cert_remarks = data.get("cert_remarks", "")
    cert_docs = data.get("cert_docs", '{"marksheet_10":true,"marksheet_12":true,"tc":true,"community_cert":true}')

    cursor.execute("""
        INSERT INTO students
        (app_no, name, email, phone, department, stream, course_code, marks,
         m1, m2, m3, m4, m5, m6, marks_total, gender, queue_position,
         cert_status, cert_remarks, cert_docs, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (
        app_no,
        data["name"].strip(),
        data["email"].strip().lower(),
        data["phone"].strip(),
        dept,
        stream,
        course_code,
        marks,
        m1, m2, m3, m4, m5, m6, marks_total,
        data.get("gender", "Not Specified"),
        data.get("queue_position", 1),
        cert_status,
        cert_remarks,
        str(cert_docs)
    ))

    student_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return student_id, app_no


def update_certificate_status(student_id, status, remarks=""):
    """
    Updates the certificate verification status of an applicant.
    Status can be 'verified', 'flagged', or 'pending'.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students
        SET cert_status = ?, cert_remarks = ?
        WHERE id = ?
    """, (status, remarks, student_id))
    conn.commit()
    conn.close()
    return True


def get_course_by_code(code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE UPPER(code) = UPPER(?)", (str(code).strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_course_by_name(name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE UPPER(name) = UPPER(?)", (str(name).strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_pending_students_by_course(course_code=None):
    conn = get_db()
    cursor = conn.cursor()
    if course_code and str(course_code).strip().upper() != "ALL":
        cursor.execute("""
            SELECT * FROM students 
            WHERE status = 'pending' AND UPPER(course_code) = UPPER(?)
            ORDER BY queue_position ASC, id ASC
        """, (str(course_code).strip(),))
    else:
        cursor.execute("""
            SELECT * FROM students 
            WHERE status = 'pending'
            ORDER BY queue_position ASC, id ASC
        """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_student_by_identifier(query):
    """
    Search student by numeric ID or alphanumeric Application Number (app_no).
    Supports e.g. 5, #5, or 'ABC26-AID-CS-1001'.
    """
    conn = get_db()
    cursor = conn.cursor()

    cleaned = str(query).strip().replace("#", "")

    if cleaned.isdigit():
        cursor.execute("SELECT * FROM students WHERE id = ?", (int(cleaned),))
    else:
        cursor.execute("SELECT * FROM students WHERE UPPER(app_no) = UPPER(?)", (cleaned,))
    
    row = cursor.fetchone()

    admission_info = None
    if row:
        student_id = row["id"]
        cursor.execute("SELECT seat_number, allocated_at, department, stream FROM admissions WHERE student_id = ? AND status = 'active'", (student_id,))
        ad_row = cursor.fetchone()
        if ad_row:
            admission_info = dict(ad_row)

    conn.close()
    if not row:
        return None
    res = dict(row)
    if admission_info:
        res["seat_number"] = admission_info["seat_number"]
        res["allocated_at"] = admission_info["allocated_at"]
    return res


def get_student_by_id(student_id):
    return get_student_by_identifier(student_id)


def get_all_students():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.*, a.seat_number
        FROM students s
        LEFT JOIN admissions a ON s.id = a.student_id AND a.status = 'active'
        ORDER BY s.id ASC
    """)
    rows = cursor.fetchall()

    conn.close()
    return [dict(row) for row in rows]


def get_pending_students():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE status = 'pending' ORDER BY queue_position ASC")
    rows = cursor.fetchall()

    conn.close()
    return [dict(row) for row in rows]


def update_student_status(student_id, status, rejection_reason=None):
    conn = get_db()
    cursor = conn.cursor()

    if status == "rejected":
        reason = rejection_reason or "Disqualified: Eligibility cutoff or document verification requirements not fulfilled"
        cursor.execute(
            "UPDATE students SET status = ?, rejection_reason = ? WHERE id = ?",
            (status, reason, student_id)
        )
    else:
        cursor.execute(
            "UPDATE students SET status = ?, rejection_reason = '' WHERE id = ?",
            (status, student_id)
        )

    conn.commit()
    conn.close()


def get_rejection_stats():
    """
    Returns aggregated rejection metrics, reason categorization breakdown,
    and the full list of disqualified/rejected student records.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, app_no, name, email, phone, department, stream, course_code,
               marks, marks_total, gender, status, cert_status, cert_remarks,
               rejection_reason, application_date
        FROM students
        WHERE status = 'rejected'
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    rejected_list = [dict(r) for r in rows]
    marks_count = 0
    cert_count = 0
    fees_count = 0
    other_count = 0

    for r in rejected_list:
        reason = (r.get("rejection_reason") or "").lower()
        if "cert" in reason or "document" in reason or "tc" in reason:
            cert_count += 1
            r["reason_category"] = "Certificate Pending / Issue"
        elif "fee" in reason:
            fees_count += 1
            r["reason_category"] = "Admission Fee Issue"
        elif "mark" in reason or "cutoff" in reason:
            marks_count += 1
            r["reason_category"] = "Marks Below Cutoff"
        else:
            other_count += 1
            r["reason_category"] = "Application Discrepancy"

    return {
        "total_rejected": len(rejected_list),
        "marks_count": marks_count,
        "cert_count": cert_count,
        "fees_count": fees_count,
        "other_count": other_count,
        "students": rejected_list
    }


def get_total_seats():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(total_seats) AS total FROM courses")
    row = cursor.fetchone()
    conn.close()
    return int(row["total"]) if row and row["total"] else 1800


def get_filled_seats():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM admissions
        WHERE status = 'active'
    """)

    row = cursor.fetchone()
    conn.close()
    return row["total"] if row else 0


def get_course_stats():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            c.id,
            c.name,
            c.code,
            c.category,
            c.stream,
            c.total_seats,
            c.cutoff,
            c.tuition_fee,
            COUNT(CASE WHEN s.status = 'admitted' AND a.status = 'active' THEN 1 END) as filled_seats,
            COUNT(CASE WHEN s.status = 'pending' THEN 1 END) as queue_waiting,
            COUNT(s.id) as total_applicants
        FROM courses c
        LEFT JOIN students s ON s.department = c.name
        LEFT JOIN admissions a ON a.student_id = s.id AND a.status = 'active'
        GROUP BY c.id
        ORDER BY c.stream ASC, c.category ASC, c.name ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        filled = r["filled_seats"] or 0
        total = r["total_seats"]
        waiting = r["queue_waiting"] or 0
        apps = r["total_applicants"] or 0
        demand_pct = round((apps / total) * 100, 1) if total > 0 else 0
        result.append({
            "id": r["id"],
            "name": r["name"],
            "code": r["code"],
            "category": r["category"],
            "stream": r["stream"],
            "total_seats": total,
            "cutoff": r["cutoff"],
            "tuition_fee": r["tuition_fee"] or 0,
            "filled_seats": filled,
            "available_seats": max(0, total - filled),
            "fill_percentage": round((filled / total) * 100, 1) if total > 0 else 0,
            "queue_waiting": waiting,
            "total_applicants": apps,
            "demand_percentage": demand_pct,
            "is_overfilled": apps > total
        })
    return result


def allocate_course_seat(student_id, department, stream):
    """
    Allocates a departmental seat with formatted seat number:
    e.g. AID-CS-01, SFS-BCOM-04
    """
    conn = get_db()
    cursor = conn.cursor()

    # Get course code
    cursor.execute("SELECT code FROM courses WHERE name = ?", (department,))
    c_row = cursor.fetchone()
    code = c_row["code"] if c_row else "GEN"

    # Count existing active seats in this specific course
    cursor.execute("""
        SELECT COUNT(*) as current_count
        FROM admissions
        WHERE department = ? AND status = 'active'
    """, (department,))
    count = cursor.fetchone()["current_count"] + 1

    formatted_seat = f"{code}-{count:02d}"

    cursor.execute("""
        INSERT INTO admissions (student_id, seat_number, department, stream, status)
        VALUES (?, ?, ?, ?, 'active')
    """, (student_id, formatted_seat, department, stream))

    conn.commit()
    conn.close()
    return formatted_seat


def cancel_active_seat(student_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE admissions
        SET status = 'cancelled'
        WHERE student_id = ? AND status = 'active'
    """, (student_id,))

    conn.commit()
    conn.close()


def record_admin_action(action_type, student_id=None, note=None):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO admin_actions (action_type, student_id, admin_note)
        VALUES (?, ?, ?)
    """, (action_type, student_id, note))

    conn.commit()
    conn.close()


def mark_last_action_undone():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM admin_actions
        WHERE undone = 0
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    if row:
        cursor.execute(
            "UPDATE admin_actions SET undone = 1 WHERE id = ?",
            (row["id"],)
        )
        conn.commit()

    conn.close()


def get_hourly_admissions():
    """
    Returns admission counts grouped by hour of the day
    for the Master Board Hourly Seat Filling Monitor.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT strftime('%H:00', allocated_at) as hour_slot, COUNT(*) as count
        FROM admissions
        WHERE status = 'active'
        GROUP BY hour_slot
        ORDER BY hour_slot ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    data = {dict(r)["hour_slot"]: dict(r)["count"] for r in rows}

    hourly_distribution = []
    base_hours = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
    for hour in base_hours:
        hourly_distribution.append({
            "hour": hour,
            "count": data.get(hour, 0)
        })

    return hourly_distribution



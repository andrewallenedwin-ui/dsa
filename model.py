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
    {"name": "B.A Tamil", "code": "BA-TAM", "category": "Arts & Humanities", "stream": "Aided", "total_seats": 50, "cutoff": 60.0},
    {"name": "B.A English", "code": "BA-ENG-AID", "category": "Arts & Humanities", "stream": "Aided", "total_seats": 60, "cutoff": 78.0},
    {"name": "B.A English (SFS)", "code": "BA-ENG-SFS", "category": "Arts & Humanities", "stream": "SFS", "total_seats": 60, "cutoff": 68.0},
    {"name": "B.A History", "code": "BA-HIS-AID", "category": "Arts & Humanities", "stream": "Aided", "total_seats": 50, "cutoff": 60.0},
    {"name": "B.A History (SFS)", "code": "BA-HIS-SFS", "category": "Arts & Humanities", "stream": "SFS", "total_seats": 50, "cutoff": 55.0},
    {"name": "B.A Political Science", "code": "BA-POL", "category": "Arts & Humanities", "stream": "Aided", "total_seats": 50, "cutoff": 65.0},
    {"name": "B.A Philosophy", "code": "BA-PHIL", "category": "Arts & Humanities", "stream": "Aided", "total_seats": 40, "cutoff": 58.0},
    {"name": "B.A Journalism", "code": "BA-JOURN", "category": "Arts & Humanities", "stream": "SFS", "total_seats": 50, "cutoff": 72.0},

    # --- SCIENCES ---
    {"name": "B.Sc Mathematics", "code": "BSC-MAT-AID", "category": "Sciences", "stream": "Aided", "total_seats": 50, "cutoff": 75.0},
    {"name": "B.Sc Mathematics (SFS)", "code": "BSC-MAT-SFS", "category": "Sciences", "stream": "SFS", "total_seats": 50, "cutoff": 65.0},
    {"name": "B.Sc Physics", "code": "BSC-PHY-AID", "category": "Sciences", "stream": "Aided", "total_seats": 50, "cutoff": 76.0},
    {"name": "B.Sc Physics (SFS)", "code": "BSC-PHY-SFS", "category": "Sciences", "stream": "SFS", "total_seats": 50, "cutoff": 66.0},
    {"name": "B.Sc Chemistry", "code": "BSC-CHE-AID", "category": "Sciences", "stream": "Aided", "total_seats": 50, "cutoff": 74.0},
    {"name": "B.Sc Chemistry (SFS)", "code": "BSC-CHE-SFS", "category": "Sciences", "stream": "SFS", "total_seats": 50, "cutoff": 65.0},
    {"name": "B.Sc Botany", "code": "BSC-BOT", "category": "Sciences", "stream": "Aided", "total_seats": 45, "cutoff": 62.0},
    {"name": "B.Sc Zoology", "code": "BSC-ZOO", "category": "Sciences", "stream": "Aided", "total_seats": 45, "cutoff": 62.0},
    {"name": "B.Sc Statistics", "code": "BSC-STAT", "category": "Sciences", "stream": "Aided", "total_seats": 50, "cutoff": 70.0},
    {"name": "B.Sc Microbiology", "code": "BSC-MIC", "category": "Sciences", "stream": "SFS", "total_seats": 50, "cutoff": 74.0},
    {"name": "B.Sc Computer Science", "code": "BSC-CS-AID", "category": "Sciences", "stream": "Aided", "total_seats": 60, "cutoff": 85.0},
    {"name": "B.Sc Computer Science (SFS)", "code": "BSC-CS-SFS", "category": "Sciences", "stream": "SFS", "total_seats": 60, "cutoff": 78.0},
    {"name": "B.Sc Geography", "code": "BSC-GEO", "category": "Sciences", "stream": "Aided", "total_seats": 45, "cutoff": 60.0},
    {"name": "B.Sc Psychology", "code": "BSC-PSY", "category": "Sciences", "stream": "SFS", "total_seats": 50, "cutoff": 80.0},

    # --- COMMERCE & MANAGEMENT ---
    {"name": "B.Com General", "code": "BCOM-AID", "category": "Commerce & Management", "stream": "Aided", "total_seats": 70, "cutoff": 86.0},
    {"name": "B.Com General (SFS)", "code": "BCOM-SFS", "category": "Commerce & Management", "stream": "SFS", "total_seats": 70, "cutoff": 80.0},
    {"name": "B.Com Accounting and Finance", "code": "BCOM-AF", "category": "Commerce & Management", "stream": "SFS", "total_seats": 70, "cutoff": 82.0},
    {"name": "B.Com Professional Accounting", "code": "BCOM-PA", "category": "Commerce & Management", "stream": "SFS", "total_seats": 60, "cutoff": 84.0},
    {"name": "BBA Business Administration", "code": "BBA-SFS", "category": "Commerce & Management", "stream": "SFS", "total_seats": 60, "cutoff": 78.0},

    # --- PROFESSIONAL & SPECIAL STREAMS ---
    {"name": "B.S.W Social Work", "code": "BSW-AID", "category": "Professional & Special Streams", "stream": "Aided", "total_seats": 40, "cutoff": 60.0},
    {"name": "B.S.W Social Work (SFS)", "code": "BSW-SFS", "category": "Professional & Special Streams", "stream": "SFS", "total_seats": 40, "cutoff": 58.0},
    {"name": "B.C.A Computer Applications", "code": "BCA-SFS", "category": "Professional & Special Streams", "stream": "SFS", "total_seats": 60, "cutoff": 80.0},
    {"name": "B.Sc Visual Communication", "code": "BSC-VISCOM", "category": "Professional & Special Streams", "stream": "SFS", "total_seats": 50, "cutoff": 76.0},
    {"name": "B.Sc Data Science", "code": "BSC-DS", "category": "Professional & Special Streams", "stream": "SFS", "total_seats": 50, "cutoff": 83.0},
    {"name": "B.Sc Physical Education", "code": "BSC-PED", "category": "Professional & Special Streams", "stream": "Aided", "total_seats": 40, "cutoff": 55.0},
]


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
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
            marks REAL NOT NULL,
            gender TEXT DEFAULT 'Not Specified',
            status TEXT DEFAULT 'pending',
            queue_position INTEGER,
            application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

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
            cutoff REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Check if courses table needs migration or seeding
    cursor.execute("SELECT COUNT(*) as cnt FROM courses")
    existing_count = cursor.fetchone()["cnt"]
    if existing_count < len(DEFAULT_COURSES):
        cursor.execute("DELETE FROM courses")
        for c in DEFAULT_COURSES:
            cursor.execute("""
                INSERT OR REPLACE INTO courses (name, code, category, stream, total_seats, cutoff)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (c["name"], c["code"], c["category"], c["stream"], c["total_seats"], c["cutoff"]))

    total_course_seats = sum(c["total_seats"] for c in DEFAULT_COURSES)
    cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value)
        VALUES ('total_seats', ?)
    """, (str(total_course_seats),))

    conn.commit()
    conn.close()

    # Seed demo applicants if table is empty or sparse
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


def seed_demo_if_empty():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM students")
    count = cursor.fetchone()["count"]

    if count < 10:
        demo_cohort = [
            {"name": "Aarav Sharma", "email": "aarav.sharma@example.com", "phone": "9840112345", "department": "B.Sc Computer Science", "stream": "Aided", "marks": 96.5, "gender": "Male"},
            {"name": "Priya Ramanathan", "email": "priya.r@example.com", "phone": "9840223456", "department": "B.Com General", "stream": "Aided", "marks": 94.2, "gender": "Female"},
            {"name": "Siddharth Menon", "email": "siddharth.m@example.com", "phone": "9840334567", "department": "B.Sc Data Science", "stream": "SFS", "marks": 91.0, "gender": "Male"},
            {"name": "Kavitha Sundaram", "email": "kavitha.s@example.com", "phone": "9840445678", "department": "B.Sc Mathematics", "stream": "Aided", "marks": 95.0, "gender": "Female"},
            {"name": "Rahul Verma", "email": "rahul.v@example.com", "phone": "9840556789", "department": "BBA Business Administration", "stream": "SFS", "marks": 83.5, "gender": "Male"},
            {"name": "Ananya Iyer", "email": "ananya.iyer@example.com", "phone": "9840667890", "department": "B.A English", "stream": "Aided", "marks": 92.5, "gender": "Female"},
            {"name": "Dinesh Kumar", "email": "dinesh.k@example.com", "phone": "9840778901", "department": "B.Sc Physics", "stream": "Aided", "marks": 79.5, "gender": "Male"},
            {"name": "Sneha Patil", "email": "sneha.p@example.com", "phone": "9840889012", "department": "B.Com Accounting and Finance", "stream": "SFS", "marks": 89.0, "gender": "Female"},
            {"name": "Vikramaditya Rao", "email": "vikram.rao@example.com", "phone": "9840990123", "department": "B.C.A Computer Applications", "stream": "SFS", "marks": 86.5, "gender": "Male"},
            {"name": "Meera Nambiar", "email": "meera.n@example.com", "phone": "9840101234", "department": "B.Sc Psychology", "stream": "SFS", "marks": 93.0, "gender": "Female"},
            {"name": "Rohan Deshmukh", "email": "rohan.d@example.com", "phone": "9840212345", "department": "B.Sc Chemistry", "stream": "Aided", "marks": 84.0, "gender": "Male"},
            {"name": "Keerthana Natarajan", "email": "keerthana.n@example.com", "phone": "9840323456", "department": "B.Sc Visual Communication", "stream": "SFS", "marks": 88.5, "gender": "Female"},
            {"name": "Gautam Chandran", "email": "gautam.c@example.com", "phone": "9840434567", "department": "B.A Political Science", "stream": "Aided", "marks": 77.0, "gender": "Male"},
            {"name": "Swathi Balaji", "email": "swathi.b@example.com", "phone": "9840545678", "department": "B.Sc Microbiology", "stream": "SFS", "marks": 81.5, "gender": "Female"},
            {"name": "Harish Venkatesh", "email": "harish.v@example.com", "phone": "9840656789", "department": "B.Com Professional Accounting", "stream": "SFS", "marks": 90.0, "gender": "Male"},
            {"name": "Deepika Selvam", "email": "deepika.s@example.com", "phone": "9840767890", "department": "B.A Journalism", "stream": "SFS", "marks": 85.0, "gender": "Female"},
            {"name": "Arjun Panicker", "email": "arjun.p@example.com", "phone": "9840878901", "department": "B.Sc Computer Science (SFS)", "stream": "SFS", "marks": 87.0, "gender": "Male"},
            {"name": "Divya Krishnan", "email": "divya.k@example.com", "phone": "9840989012", "department": "B.A Tamil", "stream": "Aided", "marks": 82.0, "gender": "Female"},
            {"name": "Karthik Subramanian", "email": "karthik.s@example.com", "phone": "9840090123", "department": "B.Sc Statistics", "stream": "Aided", "marks": 89.5, "gender": "Male"},
            {"name": "Pavithra Mohan", "email": "pavithra.m@example.com", "phone": "9840111222", "department": "B.S.W Social Work", "stream": "Aided", "marks": 75.0, "gender": "Female"},
            {"name": "Ashwin Raj", "email": "ashwin.r@example.com", "phone": "9840222333", "department": "B.Sc Botany", "stream": "Aided", "marks": 71.5, "gender": "Male"},
            {"name": "Bhavani Sankar", "email": "bhavani.s@example.com", "phone": "9840333444", "department": "B.Sc Zoology", "stream": "Aided", "marks": 73.0, "gender": "Female"},
            {"name": "Naveen Prasad", "email": "naveen.p@example.com", "phone": "9840444555", "department": "B.Sc Geography", "stream": "Aided", "marks": 69.5, "gender": "Male"},
            {"name": "Sandhya Murali", "email": "sandhya.m@example.com", "phone": "9840555666", "department": "B.A Philosophy", "stream": "Aided", "marks": 68.0, "gender": "Female"},
            {"name": "Manoj Kumar", "email": "manoj.k@example.com", "phone": "9840666777", "department": "B.Sc Physical Education", "stream": "Aided", "marks": 66.0, "gender": "Male"}
        ]

        now = datetime.now()
        for idx, s in enumerate(demo_cohort):
            q_pos = idx + 1
            app_no = generate_alphanumeric_id(s["stream"], s["department"], q_pos + 100)
            app_time = (now - timedelta(minutes=(len(demo_cohort) - idx) * 12)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT OR IGNORE INTO students 
                (app_no, name, email, phone, department, stream, marks, gender, queue_position, application_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (app_no, s["name"], s["email"], s["phone"], s["department"], s["stream"], s["marks"], s["gender"], q_pos, app_time))

        conn.commit()

    conn.close()


def add_student(data):
    conn = get_db()
    cursor = conn.cursor()

    # Determine stream if not explicitly provided
    stream = data.get("stream")
    if not stream:
        cursor.execute("SELECT stream FROM courses WHERE name = ?", (data["department"],))
        c_row = cursor.fetchone()
        stream = c_row["stream"] if c_row else ("SFS" if "(sfs)" in data["department"].lower() else "Aided")

    cursor.execute("SELECT COUNT(*) as count FROM students")
    total_count = cursor.fetchone()["count"]
    app_no = generate_alphanumeric_id(stream, data["department"], total_count + 101)

    cursor.execute("""
        INSERT INTO students
        (app_no, name, email, phone, department, stream, marks, gender, queue_position)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        app_no,
        data["name"],
        data["email"],
        data["phone"],
        data["department"],
        stream,
        data["marks"],
        data.get("gender", "Not Specified"),
        data["queue_position"]
    ))

    student_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return student_id, app_no


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


def update_student_status(student_id, status):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE students SET status = ? WHERE id = ?",
        (status, student_id)
    )

    conn.commit()
    conn.close()


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
            COUNT(CASE WHEN s.status = 'admitted' AND a.status = 'active' THEN 1 END) as filled_seats
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
        result.append({
            "id": r["id"],
            "name": r["name"],
            "code": r["code"],
            "category": r["category"],
            "stream": r["stream"],
            "total_seats": total,
            "cutoff": r["cutoff"],
            "filled_seats": filled,
            "available_seats": max(0, total - filled),
            "fill_percentage": round((filled / total) * 100, 1) if total > 0 else 0
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



from flask import Flask, render_template, request, jsonify, send_file, Response
from dsa_structures import AdmissionQueue, AdminActionStack, SelectionSort, SubjectQueueManager
from datetime import datetime
import json
import io
import csv
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import os
import models

import jinja2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

tpl_candidates = [
    os.path.join(BASE_DIR, 'templates'),
    os.path.join(BASE_DIR, 'api', 'templates'),
    os.path.join(os.getcwd(), 'templates'),
    os.path.join(os.getcwd(), 'api', 'templates')
]
valid_tpl_dirs = [d for d in tpl_candidates if os.path.isdir(d)]
if valid_tpl_dirs:
    app.jinja_loader = jinja2.ChoiceLoader([jinja2.FileSystemLoader(d) for d in valid_tpl_dirs])

admission_queue = AdmissionQueue()
subject_queues = SubjectQueueManager()
admin_stack = AdminActionStack()

# Initialize DB and pre-populate queues with pending students
models.init_db()

def hydrate_queue_from_db():
    admission_queue.clear()
    subject_queues.clear()
    pending = models.get_pending_students()
    for s in pending:
        c_code = s.get("course_code") or "GEN"
        admission_queue.enqueue(s)
        subject_queues.enqueue(c_code, s)

hydrate_queue_from_db()


@app.route("/", methods=["GET", "POST"])
@app.route("/api/index", methods=["GET", "POST"])
@app.route("/api/index.py", methods=["GET", "POST"])
def index():
    route_param = (
        request.args.get("route") or
        request.args.get("__page") or
        request.args.get("__vercel_path") or
        ""
    ).strip().strip("/")

    # Strip api/ prefix if present for uniform routing
    clean_route = route_param[4:] if route_param.startswith("api/") else route_param

    if clean_route:
        if "admin" in clean_route.lower():
            return admin_page()

        if clean_route == "courses":
            return get_courses()

        if clean_route == "students":
            return students()

        if clean_route == "dashboard":
            return dashboard()

        if clean_route == "rejections":
            return get_rejections()

        if clean_route == "export-students":
            return export_students()

        if clean_route == "merit-sort":
            return merit_sort()

        if clean_route.startswith("queue/"):
            code = clean_route.split("/", 1)[1]
            return get_subject_queue(code)

        if clean_route.startswith("student/") and "verify-cert" not in clean_route:
            ident = clean_route.split("/", 1)[1]
            return student_status(ident)

        if clean_route.startswith("static/"):
            filename = clean_route[7:]
            return serve_static_file(filename)

        if request.method == "POST":
            if clean_route == "apply":
                return apply()
            if clean_route == "admit-next":
                return admit_next()
            if clean_route == "undo":
                return undo()
            if clean_route == "reset-demo":
                return reset_demo()
            if clean_route == "chat":
                return chat()
            if clean_route.startswith("reject/"):
                sid = int(clean_route.split("/", 1)[1])
                return reject_student(sid)
            if "verify-cert" in clean_route:
                parts = clean_route.split("/")
                sid = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                return verify_certificate(sid)

    return render_template("index.html")


@app.route("/debug-env")
@app.route("/api/debug-env")
def debug_env():
    return jsonify({
        "PATH_INFO": request.environ.get("PATH_INFO"),
        "REQUEST_URI": request.environ.get("REQUEST_URI"),
        "RAW_URI": request.environ.get("RAW_URI"),
        "HTTP_X_MATCHED_PATH": request.environ.get("HTTP_X_MATCHED_PATH"),
        "HTTP_X_VERCEL_MATCHED_PATH": request.environ.get("HTTP_X_VERCEL_MATCHED_PATH"),
        "HTTP_X_FORWARDED_URI": request.environ.get("HTTP_X_FORWARDED_URI"),
        "QUERY_STRING": request.environ.get("QUERY_STRING"),
        "all_keys": [k for k in request.environ.keys() if 'PATH' in k or 'URI' in k or 'VERCEL' in k or 'ROUTE' in k]
    })


@app.route("/admin")
@app.route("/api/index/admin")
@app.route("/api/index.py/admin")
def admin_page():
    return render_template("admin.html")


@app.route("/static/<path:filename>")
@app.route("/api/index/static/<path:filename>")
@app.route("/api/index.py/static/<path:filename>")
def serve_static_file(filename):
    for dir_path in [
        os.path.join(BASE_DIR, "static"),
        os.path.join(BASE_DIR, "public", "static"),
        os.path.join(BASE_DIR, "api", "static"),
        os.path.join(BASE_DIR, "public"),
    ]:
        target = os.path.join(dir_path, filename)
        if os.path.isfile(target):
            mime = "text/css; charset=utf-8" if filename.endswith(".css") else None
            return send_file(target, mimetype=mime)
    return "Static file not found", 404


@app.route("/api/courses")
def get_courses():
    return jsonify({
        "success": True,
        "courses": models.get_course_stats()
    })


@app.route("/api/apply", methods=["POST"])
def apply():
    data = request.get_json()

    required_fields = ["name", "email", "phone", "department"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                "success": False,
                "error": f"{field.capitalize()} is required"
            }), 400

    # 6 Subject Marks validation
    m1 = float(data.get("m1", 0))
    m2 = float(data.get("m2", 0))
    m3 = float(data.get("m3", 0))
    m4 = float(data.get("m4", 0))
    m5 = float(data.get("m5", 0))
    m6 = float(data.get("m6", 0))

    has_6_marks = any(x > 0 for x in [m1, m2, m3, m4, m5, m6])

    if has_6_marks:
        marks_list = [m1, m2, m3, m4, m5, m6]
        for idx, m in enumerate(marks_list):
            if m < 0 or m > 100:
                return jsonify({
                    "success": False,
                    "error": f"Subject {idx + 1} mark must be between 0 and 100"
                }), 400
        marks_total = round(sum(marks_list), 1)
        marks = round(marks_total / 6.0, 2)
    else:
        # Fallback to single aggregate marks
        try:
            marks = float(data.get("marks", 0))
            if marks < 0 or marks > 100:
                return jsonify({
                    "success": False,
                    "error": "Marks percentage must be between 0 and 100"
                }), 400
            marks_total = round(marks * 6.0, 1)
            m1 = m2 = m3 = m4 = m5 = m6 = marks
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": "Please provide valid marks"
            }), 400

    # Resolve course code
    dept = data["department"]
    c_info = models.get_course_by_name(dept)
    course_code = c_info["code"] if c_info else "GEN"
    stream = data.get("stream") or (c_info["stream"] if c_info else "Aided")

    subject_queue_pos = subject_queues.size(course_code) + 1
    global_queue_pos = admission_queue.size() + 1

    cert_docs = data.get("cert_docs", '{"marksheet_10":true,"marksheet_12":true,"tc":true,"community_cert":true}')
    if isinstance(cert_docs, dict):
        cert_docs = json.dumps(cert_docs)

    student_data = {
        "name": data["name"].strip(),
        "email": data["email"].strip().lower(),
        "phone": data["phone"].strip(),
        "department": dept,
        "stream": stream,
        "course_code": course_code,
        "marks": marks,
        "m1": m1,
        "m2": m2,
        "m3": m3,
        "m4": m4,
        "m5": m5,
        "m6": m6,
        "marks_total": marks_total,
        "gender": data.get("gender", "Not Specified"),
        "queue_position": subject_queue_pos,
        "cert_status": "pending",
        "cert_remarks": "Certificates uploaded, pending physical/online desk verification",
        "cert_docs": cert_docs
    }

    try:
        student_id, app_no = models.add_student(student_data)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "This email is already registered for an application."
        }), 400

    student_data["id"] = student_id
    student_data["app_no"] = app_no
    student_data["status"] = "pending"

    # Enqueue into both global queue and dedicated subject queue
    admission_queue.enqueue(student_data)
    subject_queues.enqueue(course_code, student_data)

    models.record_admin_action(
        "APPLICATION",
        student_id,
        f"Applied for {dept} ({course_code}) with {marks}% ({app_no}, Subject Queue #{subject_queue_pos})"
    )

    return jsonify({
        "success": True,
        "student_id": student_id,
        "app_no": app_no,
        "course_code": course_code,
        "queue_position": subject_queue_pos,
        "global_queue_position": global_queue_pos,
        "marks": marks,
        "marks_total": marks_total,
        "student": student_data
    })


@app.route("/api/student/<path:identifier>")
def student_status(identifier):
    student = models.get_student_by_identifier(identifier)

    if not student:
        return jsonify({
            "success": False,
            "error": f"Application '{identifier}' not found"
        }), 404

    # Calculate real-time positions
    subject_queue_pos = None
    course_code = student.get("course_code")
    if course_code:
        sub_queue = subject_queues.get_all(course_code)
        for idx, s in enumerate(sub_queue):
            if s.get("id") == student["id"]:
                subject_queue_pos = idx + 1
                break

    global_queue_pos = None
    all_queue = admission_queue.get_all()
    for idx, s in enumerate(all_queue):
        if s.get("id") == student["id"]:
            global_queue_pos = idx + 1
            break

    student["current_queue_position"] = subject_queue_pos or global_queue_pos
    student["current_subject_queue_position"] = subject_queue_pos
    student["current_global_queue_position"] = global_queue_pos

    return jsonify({
        "success": True,
        "student": student
    })


@app.route("/api/admit-next", methods=["POST"])
def admit_next():
    # Check if a specific course queue was requested
    course_code = request.args.get("course_code")
    if not course_code and request.is_json:
        course_code = (request.get_json(silent=True) or {}).get("course_code")

    if course_code and str(course_code).strip().upper() != "ALL":
        student = subject_queues.dequeue(course_code)
        if student:
            admission_queue.remove_by_id(student["id"])
    else:
        student = admission_queue.dequeue()
        if student:
            c_code = student.get("course_code") or "GEN"
            subject_queues.remove_by_id(student["id"])

    if not student:
        return jsonify({
            "success": False,
            "error": "Admission Queue is empty. No students waiting."
        }), 400

    total_seats = models.get_total_seats()
    filled_seats = models.get_filled_seats()

    if filled_seats >= total_seats:
        # Put back in queue front if no seats available
        admission_queue.queue.appendleft(student)
        return jsonify({
            "success": False,
            "error": "College admission quota full. All seats have been filled."
        }), 400

    student_id = student["id"]
    dept = student.get("department", "General")
    stream = student.get("stream", "Aided")

    # Allocate course-specific seat number (e.g. BSC-CS-AID-01)
    seat_number = models.allocate_course_seat(student_id, dept, stream)
    models.update_student_status(student_id, "admitted")

    action_record = {
        "type": "ADMIT",
        "student_id": student_id,
        "app_no": student.get("app_no", f"#{student_id}"),
        "student_name": student["name"],
        "department": dept,
        "stream": stream,
        "seat_number": seat_number,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    admin_stack.push(action_record)

    models.record_admin_action(
        "ADMIT",
        student_id,
        f"Seat {seat_number} allocated in {dept} ({stream})"
    )

    return jsonify({
        "success": True,
        "message": f"Student '{student['name']}' admitted to {dept} ({stream})!",
        "seat_number": seat_number,
        "app_no": student.get("app_no", f"#{student_id}"),
        "student": student
    })


@app.route("/api/reject/<int:student_id>", methods=["POST"])
def reject_student(student_id):
    student = models.get_student_by_id(student_id)
    if not student:
        return jsonify({
            "success": False,
            "error": "Student not found"
        }), 404

    data = request.get_json(silent=True) or {}
    reason = data.get("reason") or data.get("rejection_reason")
    if not reason:
        reason = "Disqualified: Mandatory document verification or minimum eligibility cutoff not fulfilled"

    # Remove from both global queue and department queue if present
    admission_queue.remove_by_id(student_id)
    c_code = student.get("course_code") or "GEN"
    subject_queues.remove_by_id(student_id)

    models.update_student_status(student_id, "rejected", rejection_reason=reason)

    action_record = {
        "type": "REJECT",
        "student_id": student_id,
        "app_no": student.get("app_no", f"#{student_id}"),
        "student_name": student["name"],
        "department": student.get("department", ""),
        "stream": student.get("stream", "Aided"),
        "rejection_reason": reason,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    admin_stack.push(action_record)

    models.record_admin_action(
        "REJECT",
        student_id,
        f"Application rejected for {student['name']}: {reason}"
    )

    return jsonify({
        "success": True,
        "message": f"Application for '{student['name']}' has been rejected. Reason: {reason}",
        "student_id": student_id,
        "rejection_reason": reason
    })


@app.route("/api/student/<int:student_id>/verify-cert", methods=["POST"])
def verify_certificate(student_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status", "verified")
    remarks = data.get("remarks", "Documents verified by admission officer")

    if status not in ["verified", "pending", "flagged"]:
        return jsonify({
            "success": False,
            "error": "Invalid certificate status. Must be 'verified', 'pending', or 'flagged'."
        }), 400

    models.update_certificate_status(student_id, status, remarks)
    student = models.get_student_by_id(student_id)

    models.record_admin_action(
        "CERT_VERIFY",
        student_id,
        f"Certificate status marked as '{status.upper()}' for {student.get('name', 'Student')} (App: {student.get('app_no', '')})"
    )

    return jsonify({
        "success": True,
        "message": f"Certificates for '{student.get('name')}' marked as {status}.",
        "cert_status": status,
        "cert_remarks": remarks
    })


@app.route("/api/queue/<course_code>")
def get_subject_queue(course_code):
    """Returns the FIFO queue of applicants for a specific department."""
    q_students = subject_queues.get_all(course_code)
    return jsonify({
        "success": True,
        "course_code": course_code,
        "queue_size": len(q_students),
        "students": q_students
    })


@app.route("/api/undo", methods=["POST"])
def undo():
    action = admin_stack.pop()

    if not action:
        return jsonify({
            "success": False,
            "error": "Stack is empty! No recent action available to undo."
        }), 400

    student_id = action["student_id"]

    if action["type"] == "ADMIT":
        models.cancel_active_seat(student_id)
        models.update_student_status(student_id, "pending")
        student = models.get_student_by_id(student_id)
        if student:
            c_code = student.get("course_code") or "GEN"
            # Re-enqueue at the front of both queues
            admission_queue.queue.appendleft(student)
            subject_queues.get_queue(c_code).queue.appendleft(student)

    elif action["type"] == "REJECT":
        models.update_student_status(student_id, "pending")
        student = models.get_student_by_id(student_id)
        if student:
            c_code = student.get("course_code") or "GEN"
            admission_queue.enqueue(student)
            subject_queues.enqueue(c_code, student)

    models.mark_last_action_undone()

    return jsonify({
        "success": True,
        "message": f"Undo successful: '{action['type']}' action for '{action.get('student_name', 'Student')}' was reversed via Stack LIFO operation.",
        "action": action
    })


@app.route("/api/merit-sort")
def merit_sort():
    """
    Selection Sort Algorithm API.
    Sorts all applicants (or pending applicants) by 12th Marks in descending order.
    Returns the step-by-step trace for the visual animation.
    """
    dept = request.args.get("department")
    stream = request.args.get("stream")
    students = models.get_all_students()

    if stream and stream != "All":
        students = [s for s in students if s.get("stream") == stream]

    if dept and dept != "All":
        students = [s for s in students if s.get("department") == dept]

    # Run Selection Sort with execution trace
    sort_result = SelectionSort.sort_with_trace(students, key="marks", reverse=True)

    return jsonify({
        "success": True,
        "sorted_students": sort_result["sorted_students"],
        "trace_steps": sort_result["trace_steps"],
        "total_comparisons": sort_result["total_comparisons"],
        "total_swaps": sort_result["total_swaps"],
        "time_complexity": sort_result["time_complexity"],
        "space_complexity": sort_result["space_complexity"],
        "total_count": len(students)
    })


@app.route("/api/dashboard")
def dashboard():
    total_seats = models.get_total_seats()
    filled_seats = models.get_filled_seats()
    all_students = models.get_all_students()
    rejection_data = models.get_rejection_stats()

    total_verified = sum(1 for s in all_students if s.get("cert_status") == "verified")
    total_pending_cert = sum(1 for s in all_students if s.get("cert_status") == "pending")
    total_flagged_cert = sum(1 for s in all_students if s.get("cert_status") in ["flagged", "rejected"])

    demand_ratio = round((len(all_students) / total_seats) * 100, 1) if total_seats > 0 else 0
    demand_factor = round(len(all_students) / total_seats, 2) if total_seats > 0 else 0
    fill_rate = round((filled_seats / total_seats) * 100, 1) if total_seats > 0 else 0
    overfill_count = max(0, len(all_students) - total_seats)
    selectivity_rate = round((filled_seats / len(all_students)) * 100, 1) if len(all_students) > 0 else 0

    return jsonify({
        "success": True,
        "total_seats": total_seats,
        "filled_seats": filled_seats,
        "available_seats": max(0, total_seats - filled_seats),
        "total_students": len(all_students),
        "queue_size": admission_queue.size(),
        "queue_items": admission_queue.get_all(),
        "next_student": admission_queue.peek(),
        "subject_queues": subject_queues.get_summary(),
        "total_verified": total_verified,
        "total_pending_cert": total_pending_cert,
        "total_flagged_cert": total_flagged_cert,
        "total_rejected": rejection_data["total_rejected"],
        "rejection_marks_count": rejection_data["marks_count"],
        "rejection_cert_count": rejection_data["cert_count"],
        "rejection_fees_count": rejection_data["fees_count"],
        "rejection_other_count": rejection_data["other_count"],
        "rejected_students": rejection_data["students"],
        "stack_size": admin_stack.size(),
        "recent_actions": admin_stack.get_recent_actions(8),
        "courses": models.get_course_stats(),
        "hourly_stats": models.get_hourly_admissions(),
        "demand_ratio": demand_ratio,
        "demand_factor": demand_factor,
        "fill_rate": fill_rate,
        "overfill_count": overfill_count,
        "selectivity_rate": selectivity_rate,
        "competition_status": "FIERCE TIER-1 CHENNAI ADMISSION RUSH (OVERFILLING)",
        "is_overfilled": len(all_students) > total_seats,
        "time": datetime.now().strftime("%d-%b-%Y %I:%M:%S %p")
    })


@app.route("/api/rejections")
def get_rejections():
    category = request.args.get("category", "All")
    stats = models.get_rejection_stats()
    students = stats["students"]
    if category and category != "All":
        students = [s for s in students if s.get("reason_category") == category]
    return jsonify({
        "success": True,
        "total_rejected": stats["total_rejected"],
        "marks_count": stats["marks_count"],
        "cert_count": stats["cert_count"],
        "fees_count": stats["fees_count"],
        "other_count": stats["other_count"],
        "filtered_count": len(students),
        "students": students
    })


@app.route("/api/students")
def students():
    return jsonify({
        "success": True,
        "students": models.get_all_students()
    })


@app.route("/api/export-students")
def export_students():
    """
    Exports the overall student repository as a formatted Excel (.xlsx) file
    or CSV file for administrative reporting and Chennai college quota analysis.
    """
    fmt = request.args.get("format", "xlsx").lower()
    stream_filter = request.args.get("stream", "All")
    status_filter = request.args.get("status", "All")
    dept_filter = request.args.get("department", "All")

    students_list = models.get_all_students()

    # Optional query filters
    if stream_filter and stream_filter != "All":
        students_list = [s for s in students_list if s.get("stream") == stream_filter]
    if status_filter and status_filter != "All":
        students_list = [s for s in students_list if s.get("status") == status_filter]
    if dept_filter and dept_filter != "All":
        students_list = [s for s in students_list if s.get("department") == dept_filter]

    # CSV Format Export
    if fmt == "csv":
        output = io.StringIO()
        output.write('\ufeff') # UTF-8 BOM for Excel compatibility
        writer = csv.writer(output)
        writer.writerow([
            "Sl No", "Application No", "Student Name", "Gender", "Mobile Phone", "Email Address",
            "Degree Program", "Stream", "Course Code",
            "Language (Part I)", "English (Part II)", "Core 1", "Core 2", "Core 3", "Core 4 / Elective",
            "HSC Total (/600)", "Aggregate %", "Admission Status", "Allotted Seat No", "Queue Position",
            "Certificate Status", "Document Officer Notes", "Disqualification / Rejection Reason", "Application Date"
        ])
        for idx, s in enumerate(students_list, 1):
            st = s.get("status", "").lower()
            status_label = "ADMITTED" if st == "admitted" else ("WAITLIST" if st == "pending" else "REJECTED")
            seat = s.get("seat_number", "") or ("-" if st == "rejected" else "IN QUEUE")
            q_pos = s.get("queue_position", "") if st == "pending" else "-"

            writer.writerow([
                idx,
                s.get("app_no", ""),
                s.get("name", ""),
                s.get("gender", ""),
                s.get("phone", ""),
                s.get("email", ""),
                s.get("department", ""),
                s.get("stream", ""),
                s.get("course_code", ""),
                s.get("m1", 0),
                s.get("m2", 0),
                s.get("m3", 0),
                s.get("m4", 0),
                s.get("m5", 0),
                s.get("m6", 0),
                s.get("marks_total", 0),
                s.get("marks", 0),
                status_label,
                seat,
                q_pos,
                str(s.get("cert_status", "")).upper(),
                s.get("cert_remarks", ""),
                s.get("rejection_reason", ""),
                s.get("application_date", "")
            ])
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv; charset=utf-8-sig",
            headers={"Content-Disposition": "attachment; filename=ABC_College_Admissions_2026.csv"}
        )

    # Excel (.xlsx) Format Export using openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Student Repository"
    ws.views.sheetView[0].showGridLines = True

    # Typography & Styles
    title_font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    subtitle_font = Font(name="Calibri", size=10, italic=True, color="475569")
    meta_font = Font(name="Calibri", size=9, bold=True, color="0F172A")
    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")

    stripe_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    admitted_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    admitted_font = Font(name="Calibri", size=9, bold=True, color="166534")
    pending_fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    pending_font = Font(name="Calibri", size=9, bold=True, color="1E40AF")
    rejected_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    rejected_font = Font(name="Calibri", size=9, bold=True, color="991B1B")

    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    # Institution Title Block
    ws.merge_cells("A1:X1")
    ws["A1"] = "ABC COLLEGE OF ARTS AND SCIENCE (AUTONOMOUS) — CHENNAI"
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 26

    ws.merge_cells("A2:X2")
    ws["A2"] = "Central Admissions Office & Departmental Queue System — Academic Cohort 2026–2027"
    ws["A2"].font = subtitle_font
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 18

    # Meta KPI line
    ws.merge_cells("A3:X3")
    total_count = len(students_list)
    admitted_count = sum(1 for s in students_list if s.get("status") == "admitted")
    pending_count = sum(1 for s in students_list if s.get("status") == "pending")
    rejected_count = sum(1 for s in students_list if s.get("status") == "rejected")
    ws["A3"] = f"Report Date: {datetime.now().strftime('%d-%b-%Y %I:%M %p')} | Total Applicants: {total_count} | Confirmed Seats: {admitted_count} | In Queue: {pending_count} | Rejected: {rejected_count} | Status: OVERFILLING (Chennai Tier-1 Competition)"
    ws["A3"].font = meta_font
    ws["A3"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[3].height = 20

    # Column Headers at Row 5
    headers = [
        "Sl No", "Application No", "Student Name", "Gender", "Mobile Phone", "Email Address",
        "Degree Program", "Stream", "Course Code",
        "Lang (Part I)", "English (Part II)", "Core 1", "Core 2", "Core 3", "Core 4 / Elective",
        "HSC Total (/600)", "Aggregate %", "Admission Status", "Allotted Seat No", "Queue Rank",
        "Certificate Status", "Document Officer Notes", "Disqualification / Rejection Reason", "Submission Date"
    ]
    ws.append([]) # Row 4 empty
    ws.row_dimensions[4].height = 8
    ws.append(headers) # Row 5
    ws.row_dimensions[5].height = 26

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=5, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Populate Data Rows
    row_num = 6
    for idx, s in enumerate(students_list, 1):
        st = s.get("status", "").lower()
        status_label = "ADMITTED" if st == "admitted" else ("WAITLIST" if st == "pending" else "REJECTED")
        seat = s.get("seat_number", "") or ("-" if st == "rejected" else "IN QUEUE")
        q_pos = s.get("queue_position", "") if st == "pending" else "-"

        row_data = [
            idx,
            s.get("app_no", ""),
            s.get("name", ""),
            s.get("gender", ""),
            s.get("phone", ""),
            s.get("email", ""),
            s.get("department", ""),
            s.get("stream", ""),
            s.get("course_code", ""),
            s.get("m1", 0),
            s.get("m2", 0),
            s.get("m3", 0),
            s.get("m4", 0),
            s.get("m5", 0),
            s.get("m6", 0),
            s.get("marks_total", 0),
            s.get("marks", 0),
            status_label,
            seat,
            q_pos,
            str(s.get("cert_status", "")).upper(),
            s.get("cert_remarks", ""),
            s.get("rejection_reason", ""),
            s.get("application_date", "")
        ]
        ws.append(row_data)
        ws.row_dimensions[row_num].height = 20

        is_even = (idx % 2 == 0)
        for col_idx in range(1, len(row_data) + 1):
            cell = ws.cell(row=row_num, column=col_idx)
            cell.border = thin_border
            cell.font = Font(name="Calibri", size=9)

            if is_even:
                cell.fill = stripe_fill

            # Column alignments
            if col_idx in [1, 4, 8, 9, 18, 19, 20, 21]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx in [10, 11, 12, 13, 14, 15, 16, 17]:
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

            # Color code status column
            if col_idx == 18:
                if st == "admitted":
                    cell.fill = admitted_fill
                    cell.font = admitted_font
                elif st == "pending":
                    cell.fill = pending_fill
                    cell.font = pending_font
                elif st == "rejected":
                    cell.fill = rejected_fill
                    cell.font = rejected_font

        row_num += 1

    # Freeze panes below header row
    ws.freeze_panes = "A6"

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.row < 5:
                continue
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"ABC_College_Student_Admissions_2026.xlsx"
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )


@app.route("/api/reset-demo", methods=["POST"])
def reset_demo():
    """Resets the demo data so examiners can see fresh runs."""
    import os
    if os.path.exists("admissions.db"):
        os.remove("admissions.db")
    models.init_db()
    admin_stack.clear()
    hydrate_queue_from_db()
    return jsonify({
        "success": True,
        "message": "Demo database and DSA structures reset successfully."
    })


def generate_abc_friend_reply(user_msg, requested_lang="auto"):
    text = (user_msg or "").strip()
    lower_text = text.lower()

    # Detect Tamil
    is_tamil = (requested_lang == "ta") or any('\u0b80' <= char <= '\u0bff' for char in text)
    if not is_tamil and any(w in lower_text for w in ["vanakkam", "kattanam", "eppadi", "saandridhal", "matheepen"]):
        is_tamil = True

    courses = models.get_course_stats()

    # Check for specific course query
    matched_course = None
    for c in courses:
        clean_name = c["name"].lower().replace("b.sc ", "").replace("b.a ", "").replace("b.com ", "").replace("b.s.w ", "").replace("b.c.a ", "")
        code_clean = c["code"].lower()
        if (clean_name in lower_text and len(clean_name) > 3) or (code_clean in lower_text) or (c["name"].lower() in lower_text):
            matched_course = c
            break

    # SPECIFIC COURSE QUERY FIRST
    if matched_course:
        c = matched_course
        fee_fmt = f"₹{c.get('tuition_fee', 0):,}"
        if is_tamil:
            return {
                "reply": f"📘 **{c['name']} ({c['code']})** சேர்க்கை விவரங்கள்:\n\n"
                         f"- **பிரிவு (Stream):** {c['stream']} ({'அரசு உதவிபெறும் பிரிவு' if c['stream'] == 'Aided' else 'சுயநிதி பிரிவு'})\n"
                         f"- **பருவக் கட்டணம் (Tuition Fee):** **{fee_fmt} / பருவம்**\n"
                         f"- **தகுதி கட்-ஆஃப்:** **{c['cutoff']}%**\n"
                         f"- **அங்கீகரிக்கப்பட்ட இடங்கள்:** **{c['total_seats']}** (நிரப்பப்பட்டது: {c['filled_seats']}, மீதமுள்ளவை: {c['available_seats']})\n\n"
                         f"இப்பிரிவிற்கு முகப்பு பக்கத்தில் உள்ள விண்ணப்ப படிவம் மூலம் உடனே விண்ணப்பிக்கலாம்!",
                "lang": "ta",
                "suggestions": ["மற்ற படிப்புகளின் கட்டணம்", "சான்றிதழ்கள் என்ன தேவை?", "விண்ணப்பிப்பது எப்படி?"]
            }
        else:
            return {
                "reply": f"📘 **Details for {c['name']} ({c['code']}):**\n\n"
                         f"- **Stream:** {c['stream']} ({'Government Aided' if c['stream'] == 'Aided' else 'Self-Financed Shift'})\n"
                         f"- **Tuition Fee:** **{fee_fmt} per semester**\n"
                         f"- **Eligibility Cutoff:** **{c['cutoff']}%** aggregate\n"
                         f"- **Total Seats:** **{c['total_seats']} seats** (Filled: {c['filled_seats']}, Available: {c['available_seats']})\n\n"
                         f"You can apply for this program directly using the application form below on this portal!",
                "lang": "en",
                "suggestions": ["View Other Course Fees", "What Certificates Needed?", "How Selection Sort Works?"]
            }

    # GREETINGS (When greeting words appear and no specific query keywords like fee/cutoff/etc.)
    has_domain_query = any(w in lower_text for w in [
        "fee", "fees", "cost", "tuition", "கட்டணம்", "கட்டண", "பீஸ்",
        "cutoff", "cut off", "marks needed", "minimum", "கட்-ஆஃப்", "தகுதி",
        "cert", "document", "சான்றிதழ்", "டிசி", "marksheet",
        "apply", "form", "விண்ணப்ப", "பதிவு",
        "status", "track", "நிலை", "டிராக்",
        "dsa", "queue", "stack", "sort", "வரிசை", "அடுக்கு",
        "reject", "நிராகரி",
        "competition", "overfill", "crowd", "rush", "demand", "seats left", "vacancy", "capacity", "போட்டி", "நிரம்ப", "கூட்டம்", "வாய்ப்பு",
        "phone", "mobile", "helpdesk", "contact", "தொலைபேசி", "எண்"
    ])

    if any(w in lower_text for w in ["hi", "hello", "hey", "வணக்கம்", "vanakkam", "help", "who are you", "யாரு"]) and not has_domain_query:
        if is_tamil:
            return {
                "reply": "வணக்கம்! நான் **ABC FRIEND** (ஏபிசி நண்பன்) — ஏபிசி கலை மற்றும் அறிவியல் கல்லூரியின் அதிகாரப்பூர்வ சேர்க்கை AI வழிகாட்டி.\n\nகல்லூரி கட்டண விவரங்கள், கட்-ஆஃப் மதிப்பெண்கள், தேவையான சான்றிதழ்கள், விண்ணப்பிக்கும் முறை அல்லது உங்கள் விண்ணப்ப நிலையை அறிய என்னிடம் கேளுங்கள்!\n\nநேரடி உதவிக்கு: **+91 9342311026**.",
                "lang": "ta",
                "suggestions": ["கட்டண விவரங்கள்", "கட்-ஆஃப் மதிப்பெண்கள்", "தேவையான சான்றிதழ்கள்", "விண்ணப்ப நிலை அறிதல்", "உதவி மையம் எண்"]
            }
        else:
            return {
                "reply": "Hello! I am **ABC FRIEND** — your official AI admissions guide for ABC College of Arts and Science.\n\nI can help you with:\n- 💰 **Course Tuition Fee Structure** (Aided & SFS)\n- 🎯 **Department Cutoff Marks**\n- 📄 **Mandatory Verification Certificates**\n- 📝 **6-Subject Application & Percentage Calculation**\n- 🔍 **Tracking Your Application Status**\n- ⚡ **DSA Concepts (Queue, Stack, Selection Sort)**\n\nAdmissions Helpline: **+91 9342311026**\nHow can I help you today?",
                "lang": "en",
                "suggestions": ["Course Fees Structure", "Cutoff Marks", "Required Certificates", "How to Apply?", "Helpline Contact"]
            }

    # CHENNAI OVERFILLING ADMISSION & COMPETITION RUSH QUERY
    if any(w in lower_text for w in ["competition", "overfill", "crowd", "rush", "demand", "seats left", "vacancy", "capacity", "போட்டி", "நிரம்ப", "கூட்டம்", "வாய்ப்பு"]):
        if is_tamil:
            return {
                "reply": "🔥 **சென்னையின் முன்னணி போட்டி கல்லூரியான ஏபிசி-யின் சேர்க்கை நிலவரம்:**\n\n"
                         "சென்னையின் தலைசிறந்த தன்னாட்சி கலை மற்றும் அறிவியல் கல்லூரியாக விளங்குவதால், நடப்பு 2026-2027 கல்வியாண்டில் சேர்க்கை விண்ணப்பங்கள் **அபாரமாக நிரம்பி வழிகின்றன (Overfilling Admission)**:\n\n"
                         "- 🏛️ **அங்கீகரிக்கப்பட்ட மொத்த இடங்கள்:** 855 இடங்கள் மட்டுமே\n"
                         "- 📋 **பெறப்பட்ட மொத்த விண்ணப்பங்கள்:** **2,475+ விண்ணப்பங்கள்** (சுமார் 290% அதிக விண்ணப்பங்கள்!)\n"
                         "- 💺 **நிரப்பப்பட்ட இடங்கள்:** 815 இடங்கள் (95.3% இடங்கள் உறுதிசெய்யப்பட்டன)\n"
                         "- ⏳ **துறைசார் காத்திருப்போர் வரிசை (Queue):** 1,560-க்கும் மேற்பட்ட மாணவர்கள் காத்திருப்பில் உள்ளனர்!\n"
                         "- 🎯 **முன்னுரிமை சேர்க்கை:** **Selection Sort மெரிட் பட்டியல்** மற்றும் **FIFO முன்னுரிமை வரிசை** மூலம் மட்டுமே சேர்க்கை நடைபெறும்.\n\n"
                         "கடைசி சில இடங்கள் வேகமாக நிரம்பி வருவதால், உடனே விண்ணப்பிக்குமாறு கேட்டுக்கொள்ளப்படுகிறீர்கள்!",
                "lang": "ta",
                "suggestions": ["கட்-ஆஃப் மதிப்பெண்கள்", "கட்டண விவரங்கள்", "விண்ணப்ப முறை", "உதவி மையம் எண்"]
            }
        else:
            return {
                "reply": "🔥 **Chennai Tier-1 Premier Admission Rush & Overfilling Status:**\n\n"
                         "As one of Chennai's premier autonomous Arts & Science institutions (affiliated with University of Madras), admission for 2026–2027 is experiencing an **intense overfilling surge**:\n\n"
                         "- 🏛️ **Approved Sanctioned Intake:** 855 seats across 33 departments\n"
                         "- 📋 **Total Applications Received:** **2,475+ candidates** (**290% Over-subscribed Demand!**)\n"
                         "- 💺 **Confirmed Allotments:** 815 seats (**95.3% Capacity Filled!**)\n"
                         "- ⏳ **Active FIFO Queue Waitlist:** **1,560+ applicants** competing for the remaining ~40 seats!\n"
                         "- 🎯 **Allotment Engine:** Governed purely by merit via **Selection Sort** and **FIFO Department Queues**.\n\n"
                         "With remaining seats closing rapidly, prospective students are advised to complete verification at the earliest.",
                "lang": "en",
                "suggestions": ["View Cutoff Marks", "Tuition Fee Schedule", "How to Apply?", "Helpline Desk"]
            }

    # FEES GENERAL
    if any(w in lower_text for w in ["fee", "fees", "cost", "கட்டணம்", "கட்டண", "பீஸ்", "விலை", "துறை கட்டணம்", "tuition"]):
        if is_tamil:
            return {
                "reply": "💰 **ஏபிசி கல்லூரியின் கட்டண அமைப்பு (2026-2027):**\n\n"
                         "🏛️ **அரசு உதவிபெறும் பிரிவுகள் (Aided - Day Shift):**\n"
                         "- **B.A கலைப்பிரிவுகள்:** ₹4,650 – ₹5,850 / பருவம் (B.A தமிழ்: ₹4,850)\n"
                         "- **B.Sc அறிவியல்:** ₹6,250 – ₹8,250 / பருவம் (B.Sc கணினி அறிவியல்: ₹11,500)\n"
                         "- **B.Com General (Aided):** ₹6,950 / பருவம்\n\n"
                         "🎓 **சுயநிதி பிரிவுகள் (Self-Financed Stream - SFS Evening Shift):**\n"
                         "- **வணிகவியல் (B.Com, BBA):** ₹32,000 – ₹36,000 / பருவம்\n"
                         "- **B.Sc Computer Science / Data Science:** ₹34,500 – ₹37,500 / பருவம்\n"
                         "- **B.C.A / Visual Communication:** ₹36,500 – ₹38,000 / பருவம்\n\n"
                         "விண்ணப்ப படிவத்திற்கு மேலே உள்ள **கட்டண அட்டவணையில் (Fee Structure Table)** அனைத்து 33 துறைகளின் கட்டணங்களையும் நேரடியாக பார்க்கலாம்!\n\n"
                         "கட்டண சலுகைகள் மற்றும் உதவிக்கு: **+91 9342311026**.",
                "lang": "ta",
                "suggestions": ["B.Sc Computer Science கட்டணம்", "B.Com கட்டணம்", "கட்-ஆஃப் மதிப்பெண்கள்", "விண்ணப்ப முறை"]
            }
        else:
            return {
                "reply": "💰 **ABC College Fee Structure Overview (2026-2027):**\n\n"
                         "🏛️ **Government Aided Programs (Day Shift):**\n"
                         "- **B.A Arts & Humanities:** ₹4,650 – ₹5,850 / semester\n"
                         "- **B.Sc Sciences:** ₹6,250 – ₹8,250 / semester (B.Sc CS Aided: ₹11,500)\n"
                         "- **B.Com General (Aided):** ₹6,950 / semester\n\n"
                         "🎓 **Self-Financed Stream - SFS (Evening Shift):**\n"
                         "- **Commerce & Management (B.Com, BBA):** ₹32,000 – ₹36,000 / semester\n"
                         "- **Computer Science / Data Science:** ₹34,500 – ₹37,500 / semester\n"
                         "- **BCA & Visual Communication:** ₹36,500 – ₹38,000 / semester\n\n"
                         "👉 You can also explore the complete interactive Fee Structure Table located right above the admission form!\n\n"
                         "For fee installment assistance or queries, call Helpline: **+91 9342311026**.",
                "lang": "en",
                "suggestions": ["B.Sc Computer Science Fee", "B.Com General Fee", "Cutoff Marks", "Required Certificates"]
            }

    # CUTOFF
    if any(w in lower_text for w in ["cutoff", "cut off", "marks needed", "minimum", "eligibility", "கட்-ஆஃப்", "மதிப்பெண்", "தகுதி"]):
        if is_tamil:
            return {
                "reply": "🎯 **முக்கிய துறைகளின் கட்-ஆஃப் மதிப்பெண்கள் (12-ஆம் வகுப்பு):**\n\n"
                         "- **B.Com General (Aided):** 86.0% | **SFS:** 80.0%\n"
                         "- **B.Sc Computer Science (Aided):** 85.0% | **SFS:** 78.0%\n"
                         "- **B.Sc Data Science:** 83.0%\n"
                         "- **B.C.A Computer Applications:** 80.0%\n"
                         "- **B.A English (Aided):** 78.0% | **B.A தமிழ்:** 60.0%\n"
                         "- **B.Sc கணிதம் (Aided):** 75.0% | **இயற்பியல் (Aided):** 76.0%\n\n"
                         "கல்லூரி **Selection Sort மெரிட் அல்காரிதம்** மூலம் அதிக மதிப்பெண் பெற்ற மாணவர்களுக்கு முன்னுரிமை அளித்து சேர்க்கை வழங்குகிறது!",
                "lang": "ta",
                "suggestions": ["கட்டண விவரங்கள்", "6 பாட மதிப்பெண்கள் கணக்கீடு", "விண்ணப்ப நிலை"]
            }
        else:
            return {
                "reply": "🎯 **Key Department Cutoff Marks (HSC +2 Aggregate):**\n\n"
                         "- **B.Com General:** 86.0% (Aided) | 80.0% (SFS)\n"
                         "- **B.Sc Computer Science:** 85.0% (Aided) | 78.0% (SFS)\n"
                         "- **B.Sc Data Science:** 83.0%\n"
                         "- **B.C.A Computer Applications:** 80.0%\n"
                         "- **B.Com Accounting & Finance:** 82.0%\n"
                         "- **B.Sc Mathematics:** 75.0% (Aided)\n"
                         "- **B.A English:** 78.0% (Aided) | **B.A Tamil:** 60.0%\n\n"
                         "Admission is processed via automated **Selection Sort Merit Ranking** based on 12th marks.",
                "lang": "en",
                "suggestions": ["Fees for B.Sc CS", "What Certificates Needed?", "How to Apply?"]
            }

    # CERTIFICATES
    if any(w in lower_text for w in ["certificate", "cert", "document", "documents", "tc", "marksheet", "சான்றிதழ்", "சான்றிதழ்கள்", "ஆவணம்", "டிசி"]):
        if is_tamil:
            return {
                "reply": "📄 **சேர்க்கை சரிபார்ப்புக்கு தேவையான 4 முக்கிய சான்றிதழ்கள்:**\n\n"
                         "1. **10-ஆம் வகுப்பு மதிப்பெண் சான்றிதழ் (SSLC Marksheet)** — பிறந்த தேதி மற்றும் அடிப்படைக் கல்விச் சான்று.\n"
                         "2. **12-ஆம் வகுப்பு (+2) மதிப்பெண் சான்றிதழ் (HSC Marksheet)** — 6 பாட மதிப்பெண் சரிபார்ப்பிற்கு.\n"
                         "3. **மாற்றுச் சான்றிதழ் மற்றும் நன்னடத்தைச் சான்றிதழ் (TC & Conduct Certificate)** — பள்ளி தலைமை ஆசிரியரால் வழங்கப்பட்டது.\n"
                         "4. **சாதிச் சான்றிதழ் (Community Certificate)** — இடஒதுக்கீடு மற்றும் அரசு கல்வி உதவித்தொகைக்கு.\n\n"
                         "விண்ணப்ப படிவத்தில் இந்த சான்றிதழ்களை டிக் செய்து சமர்ப்பிக்கலாம். சேர்க்கை அலுவலர் நேரில் அல்லது ஆன்லைனில் சரிபார்த்து 'Verified' முத்திரை வழங்குவார்.",
                "lang": "ta",
                "suggestions": ["விண்ணப்பிக்கும் முறை", "நிராகரிப்பு காரணங்கள்", "உதவி மையம் எண்"]
            }
        else:
            return {
                "reply": "📄 **Mandatory Certificates Required for Verification:**\n\n"
                         "1. **10th Standard (SSLC) Marksheet** — Proof of Date of Birth & secondary completion.\n"
                         "2. **12th Standard (HSC +2) Marksheet** — For verifying all 6 subject marks.\n"
                         "3. **Transfer Certificate (TC) & Conduct Certificate** — Issued by school principal.\n"
                         "4. **Community Certificate (BC/MBC/SC/ST)** — For quota eligibility & government concessions.\n\n"
                         "Upload/tick these documents during form submission. The verification desk checks them before final seat allocation.",
                "lang": "en",
                "suggestions": ["How to Apply?", "Course Fees Structure", "Helpline Number"]
            }

    # HOW TO APPLY & 6 MARKS
    if any(w in lower_text for w in ["apply", "application", "how to", "marks", "6 marks", "percentage", "விண்ணப்பிக்க", "விண்ணப்பம்", "பதிவு", "முறை"]):
        if is_tamil:
            return {
                "reply": "📝 **விண்ணப்பிக்கும் எளிய வழிமுறைகள்:**\n\n"
                         "1. உங்கள் பெயர், மின்னஞ்சல், கைபேசி எண் உள்ளிடவும்.\n"
                         "2. விரும்பும் பிரிவு (Aided அல்லது SFS) மற்றும் பாடப்பிரிவை தேர்ந்தெடுக்கவும்.\n"
                         "3. **6 பாடங்களின் மதிப்பெண்களை (ஒவ்வொன்றும் 100-க்கு) உள்ளிடவும்**:\n"
                         "   - மொழி (Language), ஆங்கிலம் (English), 3 முக்கிய பாடங்கள், 1 விருப்பப் பாடம்.\n"
                         "   - தளம் தானாகவே மொத்த மதிப்பெண் (600-க்கு) மற்றும் சதவீதத்தை (Percentage) கணக்கிடும்.\n"
                         "4. சான்றிதழ்களை டிக் செய்து **'Submit Application'** அழுத்தவும்.\n"
                         "5. உங்களுக்கு **ABC26-AID-CS-1001** போன்ற பிரத்யேக எண் வழங்கப்படும். உடனடியாக துறைசார் FIFO காத்திருப்பு வரிசையில் சேர்க்கப்படுவீர்கள்!",
                "lang": "ta",
                "suggestions": ["கட்டண விவரங்கள்", "கட்-ஆஃப் மதிப்பெண்கள்", "விண்ணப்ப நிலை அறிதல்"]
            }
        else:
            return {
                "reply": "📝 **Step-by-Step Application Guide:**\n\n"
                         "1. Enter Candidate Name, Gender, Email, and Mobile Number.\n"
                         "2. Select Shift Stream (Aided / SFS) and your desired Degree Program.\n"
                         "3. **Enter marks for all 6 HSC subjects (out of 100 each)**:\n"
                         "   - Language, English, Core 1, Core 2, Core 3, and Elective.\n"
                         "   - The portal dynamically calculates your **Total (/600)** and **Percentage** live.\n"
                         "4. Confirm document uploads (10th, 12th, TC, Community) and click Submit.\n"
                         "5. You receive an Alphanumeric Application ID (e.g. `ABC26-AID-CS-1001`) and enter the department's FIFO waitlist instantly!",
                "lang": "en",
                "suggestions": ["Check Status", "Tuition Fees", "Required Certificates"]
            }

    # APPLICATION STATUS
    if any(w in lower_text for w in ["status", "track", "app no", "application number", "நிலை", "டிராக்", "முடிவு"]):
        if is_tamil:
            return {
                "reply": "🔍 **விண்ணப்ப நிலையை அறியும் முறை:**\n\n"
                         "முகப்பு பக்கத்தில் வலதுபுறம் உள்ள **'Check Application Status'** பெட்டியில் உங்கள் விண்ணப்ப எண்ணை (எ.கா. `ABC26-AID-CS-1001` அல்லது டோக்கன் எண்) உள்ளிட்டு 'Track Status' அழுத்தவும்.\n\n"
                         "அங்கு உங்கள்:\n"
                         "- துறைசார் வரிசை நிலை (FIFO Queue Position)\n"
                         "- சான்றிதழ் சரிபார்ப்பு நிலை (Verified / Pending)\n"
                         "- உறுதிசெய்யப்பட்ட இருக்கை எண் (Seat Number) ஆகியவற்றை உடனடியாக பார்க்கலாம்!",
                "lang": "ta",
                "suggestions": ["விண்ணப்பிப்பது எப்படி?", "கட்டண விவரங்கள்", "உதவி மையம்"]
            }
        else:
            return {
                "reply": "🔍 **Tracking Your Application Status:**\n\n"
                         "In the **'Check Application Status'** box on the portal, enter your unique alphanumeric Application Number (e.g. `ABC26-AID-CS-1001`) and click **Track Status**.\n\n"
                         "You will see live:\n"
                         "- Real-time FIFO Department Queue Position\n"
                         "- 5-Stage Visual Progress Stepper\n"
                         "- Certificate Verification Status (Verified / Flagged / Pending)\n"
                         "- Confirmed Seat Allotment details.",
                "lang": "en",
                "suggestions": ["Course Fees", "What Certificates Needed?", "Helpline Contact"]
            }

    # DSA QUESTIONS
    if any(w in lower_text for w in ["dsa", "queue", "stack", "sort", "selection sort", "fifo", "lifo", "வரிசை", "அடுக்கு"]):
        if is_tamil:
            return {
                "reply": "⚡ **இந்த சேர்க்கை தளத்தில் பயன்படுத்தப்பட்ட DSA அமைப்புகள்:**\n\n"
                         "1. **Queue (FIFO - First In, First Out):**\n"
                         "   - ஒவ்வொரு துறைக்கும் பிரத்யேக காத்திருப்பு வரிசை. முதலில் விண்ணப்பிக்கும் மாணவர் HEAD-ல் இருப்பார்.\n"
                         "2. **Stack (LIFO - Last In, First Out):**\n"
                         "   - சேர்க்கை அலுவலரின் தவறான முடிவுகளை பின்வாங்க (Undo / Rollback) உதவும் அடுக்கு.\n"
                         "3. **Selection Sort:**\n"
                         "   - 12-ஆம் வகுப்பு மதிப்பெண்கள் அடிப்படையில் தானியங்கி தகுதிப் பட்டியல் (Merit Rank List) தயாரிக்கும் வரிசையாக்க அல்காரிதம்.",
                "lang": "ta",
                "suggestions": ["கட்டண விவரங்கள்", "கட்-ஆஃப் மதிப்பெண்கள்", "விண்ணப்ப நிலை"]
            }
        else:
            return {
                "reply": "⚡ **Data Structures & Algorithms (DSA) Architecture:**\n\n"
                         "1. **Queue (FIFO - First In, First Out):**\n"
                         "   - Each of the 33 departments runs an independent FIFO queue. The earliest applicant stays at the HEAD.\n"
                         "2. **Stack (LIFO - Last In, First Out):**\n"
                         "   - The admin rollback stack records admissions and rejections for single-click O(1) Undo.\n"
                         "3. **Selection Sort Algorithm:**\n"
                         "   - Orders applicants by 12th Marks aggregate to produce official college Merit Rank lists.",
                "lang": "en",
                "suggestions": ["How to Apply?", "Course Fees Structure", "Cutoff Marks"]
            }

    # REJECTIONS
    if any(w in lower_text for w in ["reject", "rejected", "disqualif", "reason", "நிராகரி", "காரணம்"]):
        if is_tamil:
            return {
                "reply": "🚫 **விண்ணப்ப நிராகரிப்புக்கான 3 முக்கிய காரணங்கள்:**\n\n"
                         "1. **மதிப்பெண் பற்றாக்குறை (Marks Below Cutoff):** 12-ஆம் வகுப்பு மதிப்பெண் துறையின் குறைந்தபட்ச கட்-ஆஃப்-ஐ விட குறைவாக இருத்தல்.\n"
                         "2. **சான்றிதழ் நிலுவை (Certificate Pending):** 12-ஆம் வகுப்பு அல்லது மாற்றுச் சான்றிதழ் (TC) சமர்ப்பிக்கப்படாமை.\n"
                         "3. **கட்டண செலுத்த தவறுதல் (Fees Expired):** ஒதுக்கீட்டு காலக்கெடுவுக்குள் கல்விக்கட்டணம் செலுத்தப்படாமை.\n\n"
                         "மேல்முறையீடு செய்ய உதவி மையத்தை **9342311026** என்ற எண்ணில் தொடர்பு கொள்ளலாம்.",
                "lang": "ta",
                "suggestions": ["உதவி மையம் எண்", "சான்றிதழ்கள் என்ன தேவை?", "கட்டண விவரங்கள்"]
            }
        else:
            return {
                "reply": "🚫 **Common Disqualification & Rejection Grounds:**\n\n"
                         "1. **Marks Below Cutoff:** HSC percentage does not meet minimum program cutoff.\n"
                         "2. **Certificate Pending:** Original Transfer Certificate (TC) or 12th Marksheet not verified.\n"
                         "3. **Admission Fees Expired:** Prescribed tuition fee voucher deadline passed.\n\n"
                         "If you wish to submit pending certificates or clear fee discrepancies, contact the helpline at **+91 9342311026**.",
                "lang": "en",
                "suggestions": ["Helpline Contact", "Required Certificates", "Course Fees"]
            }

    # CONTACT / HELPLINE
    if any(w in lower_text for w in ["contact", "phone", "mobile", "helpdesk", "address", "location", "timing", "தொடர்பு", "தொலைபேசி", "முகவரி", "உதவி"]):
        if is_tamil:
            return {
                "reply": "🏛️ **ஏபிசி கல்லூரி சேர்க்கை உதவி மையம்:**\n\n"
                         "📞 **தொலைபேசி & உதவி எண்:** **+91 9342311026** / (044) 2239 0675\n"
                         "💬 **வாட்ஸ்அப் உதவி மையம் (WhatsApp):** **+91 9342311026**\n"
                         "✉️ **மின்னஞ்சல்:** admissions@abccollege.edu.in\n"
                         "📍 **முகவரி:** வேளச்சேரி மெயின் ரோடு, கிழக்கு தாம்பரம், சென்னை - 600 059, தமிழ்நாடு.\n"
                         "🕒 **பணி நேரம்:** திங்கள் முதல் சனி வரை: காலை 09:00 - மாலை 05:00 மணி வரை.",
                "lang": "ta",
                "suggestions": ["கட்டண விவரங்கள்", "கட்-ஆஃப் மதிப்பெண்கள்", "விண்ணப்ப முறை"]
            }
        else:
            return {
                "reply": "🏛️ **ABC College Admission Helpdesk & Contact Info:**\n\n"
                         "📞 **Admissions Helpline:** **+91 9342311026** / +91 (044) 2239 0675\n"
                         "💬 **WhatsApp Query Desk:** **+91 9342311026**\n"
                         "✉️ **Email:** admissions@abccollege.edu.in\n"
                         "📍 **Campus Location:** Velachery Main Road, East Tambaram, Chennai - 600 059, Tamil Nadu.\n"
                         "🕒 **Office Hours:** Monday – Saturday: 09:00 AM – 05:00 PM IST.",
                "lang": "en",
                "suggestions": ["Course Fees Structure", "Cutoff Marks", "How to Apply?"]
            }

    # DEFAULT FALLBACK
    if is_tamil:
        return {
            "reply": "உங்கள் கேள்விக்கு நன்றி! நான் ஏபிசி கல்லூரியின் கட்டண விவரங்கள், கட்-ஆஃப் மதிப்பெண்கள், தேவையான சான்றிதழ்கள், விண்ணப்பிக்கும் முறை மற்றும் விண்ணப்ப நிலை போன்ற அனைத்து தகவல்களையும் உடனடியாக வழங்க முடியும். கீழே உள்ள பரிந்துரை பொத்தான்களை பயன்படுத்தி அல்லது உங்கள் கேள்வியை தெளிவாக தட்டச்சு செய்து கேளுங்கள்!",
            "lang": "ta",
            "suggestions": ["கட்டண விவரங்கள்", "கட்-ஆஃப் மதிப்பெண்கள்", "தேவையான சான்றிதழ்கள்", "உதவி மையம் எண்"]
        }
    else:
        return {
            "reply": "Thank you for asking! I can answer questions about course tuition fees, department cutoff marks, required verification documents, the 6-subject application process, or tracking your application.\n\nYou can also click any of the quick suggestions below or type a course name (e.g. 'B.Sc Computer Science fee'):",
            "lang": "en",
            "suggestions": ["Course Fees Structure", "Department Cutoffs", "Required Certificates", "Helpline Contact: 9342311026"]
        }


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    lang = data.get("lang", "auto")

    if not message:
        return jsonify({
            "success": False,
            "error": "Message is required"
        }), 400

    response_data = generate_abc_friend_reply(message, requested_lang=lang)
    return jsonify({
        "success": True,
        "reply": response_data["reply"],
        "lang": response_data["lang"],
        "suggestions": response_data["suggestions"],
        "time": datetime.now().strftime("%I:%M %p")
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
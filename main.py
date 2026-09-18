from flask import Flask, render_template, request, jsonify
from dsa_structures import AdmissionQueue, AdminActionStack, SelectionSort, SubjectQueueManager
from datetime import datetime
import json
import models

app = Flask(__name__)

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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin")
def admin_page():
    return render_template("admin.html")


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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
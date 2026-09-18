from flask import Flask, render_template, request, jsonify
from dsa_structures import AdmissionQueue, AdminActionStack, SelectionSort
from datetime import datetime
import models

app = Flask(__name__)

admission_queue = AdmissionQueue()
admin_stack = AdminActionStack()

# Initialize DB and pre-populate queue with pending students
models.init_db()

def hydrate_queue_from_db():
    admission_queue.clear()
    pending = models.get_pending_students()
    for s in pending:
        admission_queue.enqueue(s)

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

    required_fields = ["name", "email", "phone", "department", "marks"]

    for field in required_fields:
        if not data.get(field):
            return jsonify({
                "success": False,
                "error": f"{field.capitalize()} is required"
            }), 400

    try:
        marks = float(data["marks"])
        if marks < 0 or marks > 100:
            return jsonify({
                "success": False,
                "error": "Marks percentage must be between 0 and 100"
            }), 400
    except ValueError:
        return jsonify({
            "success": False,
            "error": "Marks must be a valid number"
        }), 400

    queue_position = admission_queue.size() + 1

    student_data = {
        "name": data["name"].strip(),
        "email": data["email"].strip().lower(),
        "phone": data["phone"].strip(),
        "department": data["department"],
        "stream": data.get("stream"),
        "marks": marks,
        "gender": data.get("gender", "Not Specified"),
        "queue_position": queue_position
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
    admission_queue.enqueue(student_data)

    models.record_admin_action(
        "APPLICATION",
        student_id,
        f"Applied for {student_data['department']} with {marks}% ({app_no}, Queue #{queue_position})"
    )

    return jsonify({
        "success": True,
        "student_id": student_id,
        "app_no": app_no,
        "queue_position": queue_position,
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

    # Calculate real-time queue position
    queue_pos = None
    all_queue = admission_queue.get_all()
    for idx, s in enumerate(all_queue):
        if s.get("id") == student["id"]:
            queue_pos = idx + 1
            break

    student["current_queue_position"] = queue_pos

    return jsonify({
        "success": True,
        "student": student
    })


@app.route("/api/admit-next", methods=["POST"])
def admit_next():
    student = admission_queue.dequeue()

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

    # Remove from queue if present
    admission_queue.remove_by_id(student_id)
    models.update_student_status(student_id, "rejected")

    action_record = {
        "type": "REJECT",
        "student_id": student_id,
        "app_no": student.get("app_no", f"#{student_id}"),
        "student_name": student["name"],
        "department": student.get("department", ""),
        "stream": student.get("stream", "Aided"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    admin_stack.push(action_record)

    models.record_admin_action(
        "REJECT",
        student_id,
        f"Application rejected for {student['name']}"
    )

    return jsonify({
        "success": True,
        "message": f"Application for '{student['name']}' has been rejected.",
        "student_id": student_id
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
            # Re-enqueue at the front of queue
            admission_queue.queue.appendleft(student)

    elif action["type"] == "REJECT":
        models.update_student_status(student_id, "pending")
        student = models.get_student_by_id(student_id)
        if student:
            admission_queue.enqueue(student)

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

    return jsonify({
        "success": True,
        "total_seats": total_seats,
        "filled_seats": filled_seats,
        "available_seats": max(0, total_seats - filled_seats),
        "queue_size": admission_queue.size(),
        "queue_items": admission_queue.get_all(),
        "next_student": admission_queue.peek(),
        "stack_size": admin_stack.size(),
        "recent_actions": admin_stack.get_recent_actions(8),
        "courses": models.get_course_stats(),
        "hourly_stats": models.get_hourly_admissions(),
        "time": datetime.now().strftime("%d-%b-%Y %I:%M:%S %p")
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
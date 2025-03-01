import os
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import matplotlib
matplotlib.use("Agg")
from routes.hod_routes import hod_bp
from routes.admin_routes import admin_bp

from utils import (
    read_csv_as_list,
    load_admin_mapping,
    update_admin_mappings,
    append_ratings,
    get_student_info,
    has_submitted_feedback,
    encrypt_regno,
    is_encrypted,
)
from config import (
    DEPARTMENTS_FILE,
    SEMESTERS_FILE,
    STAFFS_FILE,
    SUBJECTS_FILE,
    REQUIRED_FILES,
    FEEDBACK_QUESTIONS,
    STUDENT_FILE,
)
from asgiref.wsgi import WsgiToAsgi

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a secure key in production
app.register_blueprint(hod_bp)
app.register_blueprint(admin_bp)


asgi_app = WsgiToAsgi(app)


@app.route("/add_staff", methods=["POST"])
def add_staff():
    staff_name = request.form.get("staff_name", "").strip()
    if staff_name:
        with open("staffs.csv", "r", newline="") as csvfile:
            reader = csv.reader(csvfile)
            staff_list = [row[0] for row in reader if row]
        if staff_name in staff_list:
            flash("Staff already exists", "danger")
        else:
            with open("staffs.csv", "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([staff_name])
            flash("Staff added successfully!", "success")
            return {"success": True, "message": "Staff added successfully!"}
    return {"success": False, "message": "Staff name is required"}

@app.route("/add_subject", methods=["POST"])
def add_subject():
    subject_name = request.form.get("subject_name", "").strip()
    if subject_name:
        with open("subjects.csv", "r", newline="") as csvfile:
            reader = csv.reader(csvfile)
            subject_list = [row[0] for row in reader if row]
        if subject_name in subject_list:
            flash("Subject already exists", "danger")
        else:
            with open("subjects.csv", "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([subject_name])
            flash("Subject added successfully!", "success")
            return {"success": True, "message": "Subject added successfully!"}
    return {"success": False, "message": "Subject name is required"}

@app.route("/validate_regno", methods=["POST"])
def validate_regno():
    registerno = request.form.get("registerno", "").strip()
    if not registerno:
        return jsonify({
            "valid": False,
            "message": "Please enter a registration number"
        })

    try:
        # Remove any whitespace and non-numeric characters
        registerno = ''.join(filter(str.isdigit, registerno))
        
        if not registerno:
            return jsonify({
                "valid": False,
                "message": "Registration number must contain at least one digit"
            })

        reg_num = int(registerno)
        if reg_num < 1:
            return jsonify({
                "valid": False,
                "message": "Registration number must be a positive number"
            })

        student_info = get_student_info(registerno)
        if not student_info:
            return jsonify({
                "valid": False,
                "message": "Registration number not found"
            })

        if has_submitted_feedback(registerno):
            return jsonify({
                "valid": False,
                "message": "Feedback already submitted for this registration number"
            })

        # Check registration number range
        department = student_info.get("department")
        semester = student_info.get("semester")
        with open(STUDENT_FILE, "r") as f:
            reader = csv.DictReader(f)
            reg_nums = [int(row["registerno"]) for row in reader 
                      if row["department"] == department and row["semester"] == semester]

        if reg_nums:
            min_reg = min(reg_nums)
            max_reg = max(reg_nums)
            if max_reg - min_reg > 120:
                return jsonify({
                    "valid": False,
                    "message": "Registration number range exceeds 120 for your batch"
                })

        return jsonify({
            "valid": True,
            "message": "Registration number validated successfully!"
        })

    except ValueError:
        return jsonify({
            "valid": False,
            "message": "Invalid registration number format"
        })

@app.route("/", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        registerno = request.form.get("registerno", "")
        if not registerno:
            flash("Please enter your registration number.", "danger")
            return render_template("student_login.html")
        
        # Clean registration number - remove whitespace and non-numeric characters
        registerno = ''.join(filter(str.isdigit, registerno))
        
        if not registerno:
            flash("Registration number must contain at least one digit.", "danger")
            return render_template("student_login.html")
        
        try:
            reg_num = int(registerno)
            if reg_num < 1:
                flash("Registration number must be a positive number.", "danger")
                return render_template("student_login.html")
            
            student_info = get_student_info(registerno)
            if not student_info:
                flash("Registration number not found. Please try again.", "danger")
                return render_template("student_login.html")
            
            # Get all registration numbers from the same department and semester
            department = student_info.get("department")
            semester = student_info.get("semester")
            with open(STUDENT_FILE, "r") as f:
                reader = csv.DictReader(f)
                reg_nums = [int(row["registerno"]) for row in reader
                          if row["department"] == department and row["semester"] == semester]
            
            # Check if the difference between min and max is <= 120
            if reg_nums:
                min_reg = min(reg_nums)
                max_reg = max(reg_nums)
                if max_reg - min_reg > 120:
                    flash("Registration number range exceeds 120 for your batch.", "danger")
                    return render_template("student_login.html")
            
            if has_submitted_feedback(registerno):
                flash("Feedback already submitted for this registration number.", "info")
                return render_template("student_login.html")
            
            flash("Registration number validated successfully!", "success")
            return redirect(
                url_for(
                    "feedback",
                    department=department,
                    semester=semester,
                    registerno=registerno,
                )
            )
            
        except ValueError:
            flash("Invalid registration number format.", "danger")
            return render_template("student_login.html")
    
    return render_template("student_login.html")


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "vsbec":
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Incorrect password.", "danger")
            return redirect(url_for("admin_login"))
    return render_template("admin_login.html")


@app.route("/admin_dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")


@app.route("/admin_students")
def admin_students():
    departments = read_csv_as_list(DEPARTMENTS_FILE)
    semesters = read_csv_as_list(SEMESTERS_FILE)
    return render_template(
        "admin_students.html", departments=departments, semesters=semesters
    )


@app.route("/admin", methods=["GET", "POST"])
def admin():
    departments = read_csv_as_list(DEPARTMENTS_FILE)
    semesters = read_csv_as_list(SEMESTERS_FILE)
    staffs = read_csv_as_list(STAFFS_FILE)
    subjects = read_csv_as_list(SUBJECTS_FILE)

    if request.method == "POST":
        department = request.form.get("department")
        semester = request.form.get("semester")
        staff_list = request.form.getlist("staff")
        subject_list = request.form.getlist("subject")
        new_mappings = [
            {
                "department": department,
                "semester": semester,
                "staff": staff.strip(),
                "subject": subject.strip(),
            }
            for staff, subject in zip(staff_list, subject_list)
            if staff.strip() and subject.strip()
        ]

        if not new_mappings:
            flash("Please enter at least one valid staff–subject mapping.", "danger")
        else:
            update_admin_mappings(department, semester, new_mappings)
            flash("Mapping(s) saved successfully.", "success")
            return redirect(url_for("admin"))

    return render_template(
        "admin_mapping.html",
        departments=departments,
        semesters=semesters,
        staffs=staffs,
        subjects=subjects,
    )


@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    department = request.args.get("department")
    semester = request.args.get("semester")
    registerno = request.args.get("registerno")

    if not department or not semester or not registerno:
        flash("Missing department, semester, or registration number.", "danger")
        return redirect(url_for("student_login"))

    if has_submitted_feedback(registerno):
        flash("Feedback already submitted. You have already registered.", "info")
        return redirect(url_for("student_login"))

    mappings = load_admin_mapping(department, semester)
    if not mappings:
        return (
            f"<h2>No staff/subject mappings found for {department} - {semester}.</h2>"
        )

    if request.method == "POST":
        if has_submitted_feedback(registerno):
            flash("Feedback already submitted. You have already registered.", "info")
            return redirect(url_for("student_login"))

        rating_rows = []
        error_flag = False

        for idx, mapping in enumerate(mappings):
            ratings_dict = {}
            ratings = []
            for q in range(1, 11):
                key = f"rating-{idx}-{q}"
                value = request.form.get(key)
                if not value:
                    flash(
                        f"Please fill all rating boxes for {mapping['staff']}.",
                        "danger",
                    )
                    error_flag = True
                    break
                try:
                    score = float(value)
                except ValueError:
                    flash(f"Invalid rating value for {mapping['staff']}.", "danger")
                    error_flag = True
                    break
                ratings.append(score)
                ratings_dict[f"q{q}"] = f"{score:.2f}"

            if error_flag:
                break

            average = sum(ratings) / len(ratings)
            row_data = {
                "registerno": encrypt_regno(registerno) if not is_encrypted(registerno) else registerno,
                "department": department,
                "semester": semester,
                "staff": mapping["staff"],
                "subject": mapping["subject"],
                "average": f"{average:.2f}",
            }
            row_data.update(ratings_dict)  # Add individual question ratings
            rating_rows.append(row_data)

        if error_flag:
            return redirect(
                url_for(
                    "feedback",
                    department=department,
                    semester=semester,
                    registerno=registerno,
                )
            )
        else:
            append_ratings(rating_rows)
            flash("Feedback submitted successfully. Thank you!", "success")
            return redirect(url_for("student_login"))

    return render_template(
        "feedback.html",
        department=department,
        semester=semester,
        mappings=mappings,
        questions=FEEDBACK_QUESTIONS,
    )


# Redirect to admin_routes.py for adding students
@app.route("/addStudents", methods=["POST"])
def add_students_redirect():
    # This route is deprecated, redirecting to the new route in admin_routes.py
    return redirect(url_for('admin.add_students'))


if __name__ == "__main__":
    # Create CSV files if they don't exist and ensure they are writable
    for file, headers in REQUIRED_FILES.items():
        try:
            if not os.path.exists(file):
                with open(file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
            # Test write permissions
            with open(file, "a", newline="", encoding="utf-8") as f:
                pass
        except PermissionError:
            print(
                f"Error: No write permission for {file}. Please check file permissions."
            )
            exit(1)

    import uvicorn
    import socket
    host_ip = socket.gethostbyname(socket.gethostname())
    uvicorn.run(asgi_app, host=host_ip, port=80)

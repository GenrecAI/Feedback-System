from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from utils import (
    read_csv_as_list,
    update_admin_mappings,
    encrypt_regno,
    is_encrypted,
    normalize_regno
)
from config import DEPARTMENTS_FILE, SEMESTERS_FILE, STAFFS_FILE, SUBJECTS_FILE, STUDENT_FILE
import csv
import json

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'vsbec':
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash("Incorrect password.", "danger")
            return redirect(url_for('admin.admin_login'))
    return render_template('admin_login.html')

@admin_bp.route('/admin', methods=['GET', 'POST'])
def admin():
    departments = read_csv_as_list(DEPARTMENTS_FILE)
    semesters = read_csv_as_list(SEMESTERS_FILE)
    staffs = read_csv_as_list(STAFFS_FILE)
    subjects = read_csv_as_list(SUBJECTS_FILE)

    if request.method == 'POST':
        department = request.form.get('department')
        semester = request.form.get('semester')
        staff_list = request.form.getlist('staff')
        subject_list = request.form.getlist('subject')

        new_mappings = [{
            'department': department,
            'semester': semester,
            'staff': staff.strip(),
            'subject': subject.strip()
        } for staff, subject in zip(staff_list, subject_list) 
          if staff.strip() and subject.strip()]

        if not new_mappings:
            flash("Please enter at least one valid staff–subject mapping.", "danger")
        else:
            update_admin_mappings(department, semester, new_mappings)
            flash("Mapping(s) saved successfully.", "success")
            return redirect(url_for('admin.admin'))

    return render_template('admin_mapping.html',
                         departments=departments,
                         semesters=semesters,
                         staffs=staffs,
                         subjects=subjects)

@admin_bp.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@admin_bp.route('/admin/students', methods=['GET'])
def admin_students():
    departments = read_csv_as_list(DEPARTMENTS_FILE)
    semesters = read_csv_as_list(SEMESTERS_FILE)
    return render_template('admin_students.html',
                         departments=departments,
                         semesters=semesters)

@admin_bp.route('/admin/add_students', methods=['POST'])
def add_students():
    print("[DEBUG] add_students form data:", request.form.to_dict())
    department = request.form.get('department', '').strip()
    semester = request.form.get('semester', '').strip()
    start_reg = request.form.get('startReg', '').strip()
    end_reg = request.form.get('endReg', '').strip()

    print(f"[DEBUG] Processing add_students: department={department}, semester={semester}, start_reg={start_reg}, end_reg={end_reg}")

    # Clean up semester input - extract just the number
    semester = semester.replace('Semester ', '').replace('semester ', '').strip()

    if (not department or not semester or not start_reg or not end_reg
        or department.lower() == 'department' or semester.lower() == 'semester'
        or not semester.isdigit()):
        return jsonify({
            'success': False,
            'message': 'All fields (Department, Semester, Start Registration Number, End Registration Number) are required and must be properly selected.'
        })

    try:
        start_num = int(start_reg)
        end_num = int(end_reg)

        # Check if the range is within 120
        if (end_num - start_num + 1) > 120:
            return jsonify({
                'success': False,
                'message': 'The range between start and end numbers should not exceed 120'
            })

        # Read existing students to check for duplicates
        existing_students = {}
        try:
            with open(STUDENT_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = (row['department'], row['semester'])
                    regno = row['registerno']
                    if key not in existing_students:
                        existing_students[key] = {'encrypted': set(), 'plain': set()}
                    
                    if is_encrypted(regno):
                        existing_students[key]['encrypted'].add(regno)
                        # Try to guess the original number by checking common patterns
                        for i in range(1, 1000):
                            if encrypt_regno(str(i)) == regno:
                                existing_students[key]['plain'].add(str(i))
                                break
                    else:
                        existing_students[key]['plain'].add(regno)
                        existing_students[key]['encrypted'].add(encrypt_regno(regno))
        except FileNotFoundError:
            # Create file with headers if it doesn't exist
            with open(STUDENT_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['registerno', 'department', 'semester'])
                print(f"[DEBUG] Created new students.csv file with headers")

        # Add new students
        new_students = []
        duplicates = []
        dept_sem_key = (department, semester)
        existing_plain = existing_students.get(dept_sem_key, {}).get('plain', set())
        existing_encrypted = existing_students.get(dept_sem_key, {}).get('encrypted', set())
        
        print(f"[DEBUG] Existing students for {dept_sem_key}: plain={len(existing_plain)}, encrypted={len(existing_encrypted)}")

        for reg_no in range(start_num, end_num + 1):
            reg_str = str(reg_no)  # Don't pad with zeros to match the format in the form
            
            # Check if this register number already exists (either in plain or encrypted form)
            if reg_str in existing_plain or encrypt_regno(reg_str) in existing_encrypted:
                duplicates.append(reg_str)  # Store original for display to user
            else:
                # Store plain text version
                new_students.append([reg_str, department, semester])

        if new_students:
            with open(STUDENT_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(new_students)
                print(f"[DEBUG] Department/Semester: {dept_sem_key} | Added {len(new_students)} new students | Skipped {len(duplicates)} duplicates")
            
            msg = f"Successfully added {len(new_students)} students."
            if duplicates:
                msg += f" Registration numbers {', '.join(duplicates)} were skipped as they already exist."
            return jsonify({
                'success': True,
                'message': msg
            })
        else:
            return jsonify({
                'success': False,
                'message': f"All the registration numbers already exist for this department and semester: {', '.join(duplicates)}"
            })

    except ValueError as ve:
        print(f"[DEBUG] ValueError in add_students: {str(ve)}")
        return jsonify({
            'success': False,
            'message': 'Please enter valid registration numbers'
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_msg = f"Error in add_students: {str(e)}\nTraceback:\n{error_traceback}"
        print(error_msg)
        return jsonify({
            'success': False,
            'message': 'An error occurred while adding students. Please try again with different registration numbers or contact support if the issue persists.'
        })

@admin_bp.route('/admin/add_staff', methods=['POST'])
def add_staff():
    try:
        staff_name = request.form.get('staff_name', '').strip()
        if not staff_name:
            return jsonify({
                'success': False,
                'message': 'Staff name cannot be empty'
            })

        # Read existing staff
        staffs = read_csv_as_list(STAFFS_FILE)
        
        if staff_name in staffs:
            return jsonify({
                'success': False,
                'message': 'Staff name already exists'
            })

        # Append new staff
        with open(STAFFS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([staff_name])

        return jsonify({
            'success': True,
            'message': f'Successfully added staff: {staff_name}',
            'staff_name': staff_name
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        })

@admin_bp.route('/admin/add_subject', methods=['POST'])
def add_subject():
    try:
        subject_name = request.form.get('subject_name', '').strip()
        if not subject_name:
            return jsonify({
                'success': False,
                'message': 'Subject name cannot be empty'
            })

        # Read existing subjects
        subjects = read_csv_as_list(SUBJECTS_FILE)
        
        if subject_name in subjects:
            return jsonify({
                'success': False,
                'message': 'Subject already exists'
            })

        # Append new subject
        with open(SUBJECTS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([subject_name])

        return jsonify({
            'success': True,
            'message': f'Successfully added subject: {subject_name}',
            'subject_name': subject_name
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        })

@admin_bp.route('/admin/get_lists', methods=['GET'])
def get_lists():
    try:
        staffs = read_csv_as_list(STAFFS_FILE)
        subjects = read_csv_as_list(SUBJECTS_FILE)
        return jsonify({
            'success': True,
            'staffs': staffs,
            'subjects': subjects
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching lists: {str(e)}'
        })
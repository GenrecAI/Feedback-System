from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, make_response, current_app
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from utils import read_csv_as_list, update_mainratings, normalize_semester
from config import (DEPARTMENTS_FILE, SEMESTERS_FILE, MAINRATING_FILE,
                   RATING_FILE, STUDENT_FILE, REQUIRED_FILES, ADMIN_MAPPING_FILE)
import os
import csv
import io
import base64
import matplotlib.pyplot as plt
from datetime import datetime
import textwrap
from report_generator import generate_feedback_report
import shutil

hod_bp = Blueprint('hod', __name__)

def create_empty_csv(file_path, headers):
    """Create a new CSV file with only headers."""
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

def safe_move_file(src, dst):
    """Move file if it exists, create empty one if it doesn't."""
    if os.path.exists(src):
        shutil.copy2(src, dst)  # Copy with metadata

@hod_bp.route('/hod', methods=['GET', 'POST'])
def hod_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin':
            return redirect(url_for('hod.hod_select'))
        else:
            flash("Incorrect credentials.", "danger")
            return redirect(url_for('hod.hod_login'))
    return render_template('hod_login.html')

@hod_bp.route('/hod/select', methods=['GET', 'POST'])
def hod_select():
    departments = read_csv_as_list(DEPARTMENTS_FILE)
    semesters = read_csv_as_list(SEMESTERS_FILE)
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        department = request.form.get('department')
        semester = request.form.get('semester')
        
        if not department or not semester:
            flash("Please select both department and semester.", "danger")
            return redirect(url_for('hod.hod_select'))
        
        if action in ['view_pdf', 'download_pdf']:
            try:
                normalized_input_semester = normalize_semester(semester)
                update_mainratings()
                
                feedback_data = {}
                staff_counter = 1
                
                if os.path.exists(MAINRATING_FILE):
                    with open(MAINRATING_FILE, newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            dep = row.get('department', '').strip()
                            sem = normalize_semester(row.get('semester', ''))
                            if dep == department.strip() and sem == normalized_input_semester:
                                staff_name = row.get('staff', '').strip()
                                subject_name = row.get('subject', '').strip()
                                scores = []
                                for i in range(1, 11):
                                    try:
                                        score = float(row.get(f'q{i}_avg', '0.00'))
                                        scores.append(score)
                                    except (ValueError, TypeError):
                                        scores.append(0.0)
                                
                                key = f"{staff_name}_{subject_name}"
                                feedback_data[key] = {
                                    'reference': f'S{staff_counter}',
                                    'staff_name': staff_name,
                                    'subject': subject_name,
                                    'scores': scores
                                }
                                staff_counter += 1
                
                if not feedback_data:
                    flash("No rating data found for the selected department and semester.", "danger")
                    return redirect(url_for('hod.hod_select'))
                
                # Generate PDF report
                year = (int(normalized_input_semester) + 1) // 2
                try:
                    pdf_path = generate_feedback_report(
                        academic_year=str(datetime.now().year),
                        branch=department,
                        semester=semester,
                        year=str(year),
                        feedback_data=feedback_data
                    )
                    
                    if not pdf_path or not os.path.exists(pdf_path):
                        raise ValueError("PDF file was not generated properly")
                    
                    # Read the generated PDF
                    with open(pdf_path, 'rb') as f:
                        pdf_content = f.read()
                    
                    # Create response
                    response = make_response(pdf_content)
                    response.headers['Content-Type'] = 'application/pdf'
                    
                    if action == 'download_pdf':
                        response.headers['Content-Disposition'] = f'attachment; filename={os.path.basename(pdf_path)}'
                    else:  # view_pdf
                        response.headers['Content-Disposition'] = f'inline; filename={os.path.basename(pdf_path)}'
                    
                    # Clean up the temporary PDF file
                    try:
                        os.remove(pdf_path)
                    except:
                        pass
                    
                    return response
                
                except Exception as e:
                    current_app.logger.error(f"PDF Generation Error: {str(e)}")
                    flash(f"Error generating PDF report: {str(e)}", "danger")
                    return redirect(url_for('hod.hod_select'))
                
            except Exception as e:
                current_app.logger.error(f"General Error: {str(e)}")
                flash(f"Error processing request: {str(e)}", "danger")
                return redirect(url_for('hod.hod_select'))
        
        elif action == 'archive':
            try:
                if not os.path.exists('history'):
                    os.makedirs('history')
                
                timestamp = datetime.now().strftime("%d-%b-%Y--%H-%M-%S")
                archive_dir = os.path.join('history', timestamp)
                if not os.path.exists(archive_dir):
                    os.makedirs(archive_dir)
                
                files_to_handle = {
                    RATING_FILE: REQUIRED_FILES[RATING_FILE],
                    STUDENT_FILE: REQUIRED_FILES[STUDENT_FILE],
                    ADMIN_MAPPING_FILE: ['department', 'semester', 'staff', 'subject'],
                    MAINRATING_FILE: None
                }
                
                for file, headers in files_to_handle.items():
                    if os.path.exists(file):
                        archive_path = os.path.join(archive_dir, os.path.basename(file))
                        safe_move_file(file, archive_path)
                        
                        if headers is not None:
                            create_empty_csv(file, headers)
                        elif file == MAINRATING_FILE and os.path.exists(file):
                            os.remove(file)
                
                flash("Data successfully archived and system reset.", "success")
                
            except Exception as e:
                flash(f"Error during archival process: {str(e)}", "danger")
            
            return redirect(url_for('hod.hod_select'))
    
    return render_template('hod_select.html', 
                         departments=departments,
                         semesters=semesters)

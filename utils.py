import csv
import os
import hashlib
import base64
from config import (
    RATING_FILE, STUDENT_FILE, ADMIN_MAPPING_FILE,
    MAINRATING_FILE, REQUIRED_FILES
)

# Secret key for encryption (in a real application, this should be stored securely)
SECRET_KEY = "VSB_FEEDBACK_SYSTEM_SECRET_KEY"

def normalize_regno(regno):
    """Normalize a registration number by removing leading zeros."""
    try:
        return str(int(regno))
    except (ValueError, TypeError):
        return regno

def encrypt_regno(regno):
    """
    Encrypt a registration number using a one-way hash function.
    This ensures the registration number cannot be recovered from the stored value,
    but the same registration number will always produce the same hash.
    """
    if not regno:
        print("[DEBUG] encrypt_regno: Empty registration number")
        return ""
    
    # Normalize the registration number
    normalized_regno = normalize_regno(regno)
    print(f"[DEBUG] encrypt_regno: Normalized {regno} to {normalized_regno}")
    
    # Create a hash using the normalized number and secret key
    input_str = normalized_regno + SECRET_KEY
    print(f"[DEBUG] encrypt_regno: Input string length: {len(input_str)}")
    
    hash_obj = hashlib.sha256(input_str.encode())
    hash_str = base64.b64encode(hash_obj.digest()).decode('utf-8')
    result = hash_str[:32]
    
    print(f"[DEBUG] encrypt_regno: Input: {regno} -> Normalized: {normalized_regno} -> Output: {result}")
    return result

def is_encrypted(value):
    """
    Check if a value is already encrypted.
    Encrypted values are base64 strings of a specific length.
    """
    print(f"[DEBUG] is_encrypted: Checking value: {value}, type: {type(value)}")
    if not value:
        print("[DEBUG] is_encrypted: Empty value")
        return False
    
    # Check if the value looks like a base64 string of the right length
    try:
        if len(value) == 32:
            print(f"[DEBUG] is_encrypted: Length check passed")
            valid_chars = all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in value)
            print(f"[DEBUG] is_encrypted: Character check result: {valid_chars}")
            if valid_chars:
                return True
    except Exception as e:
        print(f"[DEBUG] is_encrypted: Error during check: {str(e)}")
        pass
    
    print("[DEBUG] is_encrypted: Not encrypted")
    return False

def read_csv_as_list(filename):
    """Return a list of values from the specified column in the CSV file."""
    if not os.path.exists(filename):
        return []
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        header = REQUIRED_FILES[filename][0]  # Get the expected header for this file
        return [row[header].strip() for row in reader if row.get(header)]

def load_admin_mapping(department, semester):
    """Return a list of mapping dictionaries matching the given department and semester."""
    mappings = []
    dep_norm = department.strip()
    sem_norm = semester.strip()
    if sem_norm.lower().startswith("semester"):
        sem_norm = sem_norm[len("semester"):].strip()
    if os.path.exists(ADMIN_MAPPING_FILE):
        with open(ADMIN_MAPPING_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_dep = row.get('department', '').strip()
                row_sem = row.get('semester', '').strip()
                if row_sem.lower().startswith("semester"):
                    row_sem = row_sem[len("semester"):].strip()
                if row_dep == dep_norm and row_sem == sem_norm:
                    mappings.append(row)
    return mappings

def update_admin_mappings(department, semester, new_mappings):
    """
    Overwrite any existing mappings for the given department and semester
    with new_mappings. Other mappings are preserved.
    """
    dep_norm = department.strip()
    sem_norm = semester.strip()
    if sem_norm.lower().startswith("semester"):
        sem_norm = sem_norm[len("semester"):].strip()
    existing = []
    if os.path.exists(ADMIN_MAPPING_FILE):
        with open(ADMIN_MAPPING_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_dep = row.get('department', '').strip()
                row_sem = row.get('semester', '').strip()
                if row_sem.lower().startswith("semester"):
                    row_sem = row_sem[len("semester"):].strip()
                if row_dep == dep_norm and row_sem == sem_norm:
                    continue
                else:
                    existing.append(row)
    combined = existing + new_mappings
    with open(ADMIN_MAPPING_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['department', 'semester', 'staff', 'subject']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in combined:
            writer.writerow(row)

def append_ratings(rating_rows):
    """Append rating rows (list of dicts) to RATING_FILE."""
    file_exists = os.path.exists(RATING_FILE)
    with open(RATING_FILE, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['registerno', 'department', 'semester', 'staff', 'subject',
                     'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9', 'q10', 'average']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in rating_rows:
            # Store the registration number as is (no encryption)
            writer.writerow(row)

def get_student_info(registerno):
    """Return student info (as a dict) from STUDENT_FILE by registration number."""
    if not os.path.exists(STUDENT_FILE):
        print("[DEBUG] Student file does not exist")
        return None
    
    print(f"[DEBUG] Looking for registration number: {registerno}")
    
    # Normalize input number
    reg_num = normalize_regno(registerno)
    print(f"[DEBUG] Normalized to: {reg_num}")
    
    if registerno != reg_num:
        print(f"[DEBUG] Registration number was normalized from {registerno} to {reg_num}")
    
    with open(STUDENT_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stored_regno = row.get('registerno', '')
            
            # Try to normalize the stored regno if it's not encrypted
            if not is_encrypted(stored_regno):
                stored_regno = normalize_regno(stored_regno)
            
            print(f"[DEBUG] Comparing with stored number: {stored_regno}")
            
            # Check if the stored regno matches either the normalized input or its encrypted form
            if stored_regno == reg_num or stored_regno == encrypt_regno(reg_num):
                print(f"[DEBUG] Found match!")
                return row
    
    print(f"[DEBUG] No match found for {reg_num}")
    return None

def has_submitted_feedback(registerno):
    """Return True if the student has already submitted feedback."""
    if not os.path.exists(RATING_FILE):
        print("[DEBUG] Rating file does not exist")
        return False

    # Normalize input number
    reg_num = normalize_regno(registerno)
    print(f"[DEBUG] Checking feedback for registration number: {registerno} (normalized: {reg_num})")

    if registerno != reg_num:
        print(f"[DEBUG] Registration number was normalized from {registerno} to {reg_num}")

    with open(RATING_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stored_regno = row.get('registerno', '')
            
            # Try to normalize the stored regno if it's not encrypted
            if not is_encrypted(stored_regno):
                stored_regno = normalize_regno(stored_regno)
            
            print(f"[DEBUG] Comparing with stored number: {stored_regno}")
            
            # Check if the stored regno matches either the normalized input or its encrypted form
            if stored_regno == reg_num or stored_regno == encrypt_regno(reg_num):
                print(f"[DEBUG] Found feedback submission!")
                return True
    
    print(f"[DEBUG] No feedback found for {reg_num}")
    return False

def update_mainratings():
    """
    Aggregate ratings from RATING_FILE grouped by department, semester, staff, and subject,
    and write the aggregated (overall average) data to MAINRATING_FILE.
    Also calculates per-question averages.
    """
    aggregated = {}
    if os.path.exists(RATING_FILE):
        with open(RATING_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                dep = row.get('department', '').strip()
                sem = row.get('semester', '').strip()
                staff = row.get('staff', '').strip()
                subject = row.get('subject', '').strip()
                key = (dep, sem, staff, subject)
                
                # Initialize if this is the first rating for this combination
                if key not in aggregated:
                    aggregated[key] = {
                        'q_sums': [0.0] * 10,  # Sum for each question
                        'count': 0,  # Number of ratings
                        'total_avg': 0.0  # Running sum of averages
                    }
                
                # Add individual question ratings
                for i in range(1, 11):
                    try:
                        q_val = float(row.get(f'q{i}', 0))
                        aggregated[key]['q_sums'][i-1] += q_val
                    except (ValueError, TypeError):
                        continue
                
                try:
                    avg = float(row.get('average', 0))
                    aggregated[key]['total_avg'] += avg
                    aggregated[key]['count'] += 1
                except (ValueError, TypeError):
                    continue
    
    with open(MAINRATING_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['department', 'semester', 'staff', 'subject', 'q1_avg', 'q2_avg', 
                    'q3_avg', 'q4_avg', 'q5_avg', 'q6_avg', 'q7_avg', 'q8_avg', 'q9_avg', 
                    'q10_avg', 'overall_average']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for key, data in aggregated.items():
            dep, sem, staff, subject = key
            count = data['count']
            if count > 0:
                row_data = {
                    'department': dep,
                    'semester': sem,
                    'staff': staff,
                    'subject': subject,
                }
                # Calculate per-question averages
                for i in range(10):
                    q_avg = data['q_sums'][i] / count
                    row_data[f'q{i+1}_avg'] = f"{q_avg:.2f}"
                
                # Calculate overall average
                overall_avg = data['total_avg'] / count
                row_data['overall_average'] = f"{overall_avg:.2f}"
                
                writer.writerow(row_data)

def normalize_semester(semester):
    """Normalize semester string by removing 'semester' prefix if present."""
    semester = semester.strip()
    if semester.lower().startswith("semester"):
        semester = semester[len("semester"):].strip()
    return semester
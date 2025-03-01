import csv
import os
import sys
from utils import normalize_regno, encrypt_regno, is_encrypted

def encrypt_csv_file(file_path, regno_field='registerno'):
    """
    Encrypt registration numbers in a CSV file.
    
    Args:
        file_path: Path to the CSV file
        regno_field: Name of the field containing registration numbers
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return False
    
    # Read all records
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            records = list(reader)
        
        # Encrypt registration numbers
        encrypted_count = 0
        for record in records:
            regno = record.get(regno_field, '')
            if regno:
                try:
                    # Check if already encrypted
                    if is_encrypted(regno):
                        print(f"Register number {regno} is already encrypted.")
                        continue
                        
                    # Encrypt the registration number
                    encrypted_regno = encrypt_regno(regno)
                    record[regno_field] = encrypted_regno
                    encrypted_count += 1
                    print(f"Encrypted {regno} to {encrypted_regno}")
                except Exception as e:
                    print(f"Could not encrypt {regno}: {str(e)}")
                    print(f"Error details: {sys.exc_info()}")
        
        # Write back the encrypted records
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        
        print(f"Successfully encrypted {encrypted_count} registration numbers in {file_path}")
        return True
    
    except Exception as e:
        print(f"Error encrypting data in {file_path}: {str(e)}")
        return False

def encrypt_ratings_csv():
    """
    Encrypt registration numbers in the ratings.csv file.
    """
    return encrypt_csv_file('ratings.csv')

def encrypt_students_csv():
    """
    Encrypt registration numbers in the students.csv file.
    """
    return encrypt_csv_file('students.csv')

if __name__ == "__main__":
    print("Starting encryption of registration numbers...")
    
    # Encrypt ratings.csv
    ratings_result = encrypt_ratings_csv()
    print(f"Ratings encryption {'completed successfully' if ratings_result else 'failed'}")
    
    # Encrypt students.csv
    students_result = encrypt_students_csv()
    print(f"Students encryption {'completed successfully' if students_result else 'failed'}")
    
    print("Encryption process complete.")

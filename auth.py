import csv
import os
from werkzeug.security import generate_password_hash, check_password_hash

USER_CSV = 'users.csv'

def user_exists(email):
    if not os.path.exists(USER_CSV):
        return False
    with open(USER_CSV, newline='') as f:
        reader = csv.DictReader(f)
        return any(row['username'].lower() == email.lower() for row in reader)

def create_user(username, password, role, company, pin='', name_or_company=''):
    hashed_password = generate_password_hash(password)
    file_exists = os.path.isfile(USER_CSV)
    with open(USER_CSV, 'a', newline='') as csvfile:
        fieldnames = ['username', 'password', 'role', 'company', 'pin', 'name_or_company']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'username': username,
            'password': hashed_password,
            'role': role,
            'company': company,
            'pin': pin,
            'name_or_company': name_or_company or company
        })

def authenticate_user(email, password):
    if not os.path.exists(USER_CSV):
        return None
    with open(USER_CSV, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'].lower() == email.lower() and check_password_hash(row['password'], password):
                return {
                    'username': row['username'],
                    'role': row['role'],
                    'company': row['company'],
                    'pin': row.get('pin', ''),
                    'name_or_company': row.get('name_or_company', row['company'])
                }
    return None


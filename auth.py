import csv
import os
from werkzeug.security import generate_password_hash, check_password_hash

USERS_FILE = 'users_secure.csv'

def create_user(username, password, role, company):
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['username', 'password', 'role', 'company'])

    hashed_pw = generate_password_hash(password)
    with open(USERS_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([username, hashed_pw, role, company])

def authenticate_user(username, password):
    if not os.path.exists(USERS_FILE):
        return None
    with open(USERS_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == username and check_password_hash(row['password'], password):
                return {'username': username, 'role': row['role'], 'company': row['company']}
    return None

def user_exists(username):
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == username:
                return True
    return False
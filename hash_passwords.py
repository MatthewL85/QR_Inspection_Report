import csv
from werkzeug.security import generate_password_hash

with open('users.csv', newline='') as infile, open('users_hashed.csv', 'w', newline='') as outfile:
    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        row['password'] = generate_password_hash(row['password'])  # hash the password
        writer.writerow(row)

print("Done! Hashed passwords saved in 'users_hashed.csv'")

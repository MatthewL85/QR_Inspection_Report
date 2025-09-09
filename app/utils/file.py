import os
from werkzeug.utils import secure_filename

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def save_profile_photo(file, user_id):
    filename = secure_filename(f"user_{user_id}_{file.filename}")
    path = os.path.join('static/uploads/avatars', filename)
    file.save(path)
    return path

from datetime import datetime
from app.extensions import db

# ----------------------------
# DIRECTOR TO AREA ASSIGNMENT
# ----------------------------
# Associates directors with specific site areas
class DirectorAreaAssignment(db.Model):
    __tablename__ = 'director_area_assignments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    area = db.Column(db.String(100))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
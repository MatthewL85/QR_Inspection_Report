from app.helpers.decorators import login_required
from flask import Blueprint, render_template, session
director_bp = Blueprint('director', __name__)

@director_bp.route('/dashboard')
@login_required(role='Director')
def dashboard():
    return render_template('director_dashboard.html')

@director_bp.route('/settings')
def director_settings():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(email=session['user']['email']).first()
    return render_template('director_settings.html', user=user)

@director_bp.route('/update-profile', methods=['POST'])
def director_update_profile():
    user = User.query.filter_by(email=session['user']['email']).first()
    user.full_name = request.form['full_name'].strip()
    db.session.commit()
    flash("Profile updated successfully!", "success")
    return redirect(url_for('director_settings'))

@director_bp.route('/change-password', methods=['POST'])
def director_change_password():
    # logic for password change with hash check
    return redirect(url_for('director_settings'))

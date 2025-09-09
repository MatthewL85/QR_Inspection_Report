# ✅ app/routes/auth/language.py
from flask import Blueprint, request, session, redirect, url_for

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/set-language', methods=['POST'], endpoint='set_language')
def set_language():
    lang = request.form.get('language')
    session['language'] = lang
    return redirect(request.referrer or url_for('auth.login'))

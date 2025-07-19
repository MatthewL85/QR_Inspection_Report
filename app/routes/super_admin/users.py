from flask import Blueprint, render_template, redirect, url_for, flash
from app.decorators import super_admin_required, has_permission
from app.models.core.user import User
from app.models.core.role import Role
from app.extensions import db

super_admin_users_bp = Blueprint('super_admin_users', __name__, url_prefix='/super-admin/users')

@super_admin_users_bp.route('/manage', endpoint='manage_users')
@super_admin_required
@has_permission('manage_users')
def manage_users():
    users = User.query.all()
    return render_template('super_admin/manage_users.html', users=users)

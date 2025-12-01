# app/routes/unit.py

from flask import Blueprint
from flask_login import login_required

# Import controller methods
from app.controllers.unit_controller import view_unit


# -----------------------------------------
# 🔵 Blueprint Definition
# -----------------------------------------
unit_bp = Blueprint(
    'unit_bp',
    __name__,
    url_prefix='/units'
)


# -----------------------------------------
# 📌 Routes
# -----------------------------------------

@unit_bp.route('/<int:unit_id>', methods=['GET'], endpoint='view_unit')
@login_required
def unit_detail(unit_id):
    """
    Wrapper route that calls the controller.
    Keeping routes thin and controllers thick is best practice.
    """
    return view_unit(unit_id)


# (Optional) — future editing, listing, assigning, etc. will go here:
#
# @unit_bp.route('/', methods=['GET'], endpoint='list_units')
# def list_units():
#     ...
#
# @unit_bp.route('/create', methods=['GET', 'POST'], endpoint='create_unit')
# def create_unit():
#     ...
#
# @unit_bp.route('/<int:unit_id>/edit', methods=['GET', 'POST'], endpoint='edit_unit')
# def edit_unit(unit_id):
#     ...
#
# @unit_bp.route('/<int:unit_id>/delete', methods=['POST'], endpoint='delete_unit')
# def delete_unit(unit_id):
#     ...
#
# These will be implemented later once UI and permissions are completed.

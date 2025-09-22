from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.forms.company.emergency_contact import EmergencyContactForm
from .. import settings_bp
from ._common import get_contact_or_404, clear_other_defaults

@settings_bp.route("/emergency/<int:contact_id>/edit", methods=["GET","POST"])
@login_required
def emergency_edit(contact_id):
    ec = get_contact_or_404(contact_id)
    form = EmergencyContactForm(obj=ec)
    if form.validate_on_submit():
        old_service = ec.service_type
        form.populate_obj(ec)
        # If default is checked or service type changed, enforce uniqueness per service
        if form.is_default.data and ec.service_type:
            clear_other_defaults(service_type=ec.service_type, exclude_id=ec.id)
            ec.is_default = True
        # If service type changed and it was default before, clear previous group’s default if needed
        if old_service != ec.service_type and ec.is_default and old_service:
            clear_other_defaults(service_type=old_service, exclude_id=ec.id)  # harmless if none
        db.session.commit()
        flash("Emergency contact updated.", "success")
        return redirect(url_for("settings.emergency_index"))
    return render_template("settings/emergency_contacts/form.html", form=form, title="Edit Emergency Contact")

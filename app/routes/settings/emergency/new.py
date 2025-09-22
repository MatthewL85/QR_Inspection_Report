from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.forms.company.emergency_contact import EmergencyContactForm
from app.models.onboarding import EmergencyContact
from .. import settings_bp
from ._common import current_company_id, clear_other_defaults

@settings_bp.route("/emergency/new", methods=["GET","POST"])
@login_required
def emergency_new():
    form = EmergencyContactForm()
    if form.validate_on_submit():
        ec = EmergencyContact(
            company_id=current_company_id(),
            label=form.label.data,
            provider=form.provider.data,
            service_type=form.service_type.data,
            phone=form.phone.data,
            alt_phone=form.alt_phone.data,
            email=form.email.data,
            coverage=form.coverage.data,
            days_of_week=form.days_of_week.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            priority=form.priority.data or 1,
            active=bool(form.active.data),
            is_default=bool(form.is_default.data),
            valid_from=form.valid_from.data,
            valid_to=form.valid_to.data,
            notes=form.notes.data,
        )
        db.session.add(ec)
        db.session.flush()
        if ec.is_default and ec.service_type:
            clear_other_defaults(service_type=ec.service_type, exclude_id=ec.id)
        db.session.commit()
        flash("Emergency contact created.", "success")
        return redirect(url_for("settings.emergency_index"))
    return render_template("settings/emergency_contacts/form.html", form=form, title="New Emergency Contact")

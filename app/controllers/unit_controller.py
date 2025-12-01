# app/controllers/unit_controller.py

# app/controllers/unit_controller.py

from flask import render_template, abort
from flask_login import login_required

from app.services.unit_service import UnitService


@login_required
def view_unit(unit_id):
    """
    Controller for viewing a single Unit.
    """

    data = UnitService.get_unit_by_id(unit_id)

    if data is None:
        abort(404)

    return render_template(
        'units/detail.html',
        data=data,
        unit=data["unit"],
        client=data["client"],
        company=data["company"],
        block=data["block"],
        core=data["core"],
        owners=data["owners"],
        owner_entities=data["owner_entities"],
        residents=data["residents"],
        resident_entities=data["resident_entities"],
        invoices=data["invoices"],
        work_orders=data["work_orders"],
        documents=data["documents"],
        child_units=data["child_units"],
    )

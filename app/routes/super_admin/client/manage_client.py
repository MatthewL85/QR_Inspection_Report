# app/routes/super_admin/client/manage_client.py

from datetime import date, datetime
import csv
import io
import re

from flask import render_template, abort, current_app, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from sqlalchemy import func, nullslast, or_
from sqlalchemy.orm import joinedload

from app.models import db
from app.models.client.client import Client          # concrete model path
from app.models.contracts import ClientContract
from app.models.core.user import User
from app.models.finance.outstanding_balance import OutstandingBalance
from app.models.maintenance.maintenance_request import MaintenanceRequest
from app.models.members.unit import Unit
from app.models.members.unit_access_invite import UnitAccessInvite
from app.models.members.unit_membership import UnitMembership
from app.models.works.work_order import WorkOrder
from app.routes.super_admin import super_admin_bp
from app.decorators import super_admin_required
from app.services.gar import build_client_context
from app.services.unit_access_service import (
    bulk_create_unit_access_invites_for_client,
    cancel_unit_access_invite,
    send_pending_unit_access_invites_for_client,
    send_unit_access_invite,
)
from app.services.unit_generation_service import generate_units_for_client, grouped_units_for_client


def _natural_key(value):
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", str(value or ""))
    ]


def _owner_summary(memberships):
    owners = [link.member for link in memberships if link.member]
    if not owners:
        return "-", "-", "-"

    names = ", ".join(owner.full_name for owner in owners)
    primary = owners[0]
    return names, primary.phone or "-", primary.email or "-"


def _members_logix_access_status(memberships, pending_invite=False):
    for link in memberships:
        member = link.member
        if link.user_id or (member and member.user_id):
            return "active", "Members Logix access active"
    if pending_invite:
        return "pending", "Members Logix invite pending"
    return "none", "No Members Logix access"


def _occupancy_label(value):
    labels = {
        "owner_occupied": "Owner Occupied",
        "let": "Let / Rented",
        "vacant": "Vacant",
        "unknown": "Unknown",
    }
    key = (value or "unknown").lower()
    return labels.get(key, str(value or "Unknown").replace("_", " ").title())


def _unit_balance_summary(unit_ids):
    if not unit_ids:
        return {}

    rows = (
        db.session.query(
            OutstandingBalance.unit_id,
            func.coalesce(func.sum(OutstandingBalance.outstanding_amount), 0),
        )
        .filter(
            OutstandingBalance.unit_id.in_(unit_ids),
            OutstandingBalance.outstanding_amount.isnot(None),
            or_(
                OutstandingBalance.status.is_(None),
                ~OutstandingBalance.status.in_(["Paid", "Written Off"]),
            ),
        )
        .group_by(OutstandingBalance.unit_id)
        .all()
    )
    return {unit_id: amount for unit_id, amount in rows}


def _unit_work_count_summary(unit_ids):
    if not unit_ids:
        return {}

    closed_statuses = {"completed", "closed", "resolved", "cancelled"}
    rows = (
        db.session.query(WorkOrder.unit_id, func.count(WorkOrder.id))
        .filter(
            WorkOrder.unit_id.in_(unit_ids),
            or_(
                WorkOrder.status.is_(None),
                ~func.lower(WorkOrder.status).in_(closed_statuses),
            ),
        )
        .group_by(WorkOrder.unit_id)
        .all()
    )
    return {unit_id: count for unit_id, count in rows}


def _unit_open_request_count_summary(unit_ids):
    if not unit_ids:
        return {}

    closed_statuses = {"completed", "closed", "resolved", "cancelled", "converted"}
    rows = (
        db.session.query(MaintenanceRequest.unit_id, func.count(MaintenanceRequest.id))
        .filter(
            MaintenanceRequest.unit_id.in_(unit_ids),
            MaintenanceRequest.work_order_id.is_(None),
            or_(
                MaintenanceRequest.status.is_(None),
                ~func.lower(MaintenanceRequest.status).in_(closed_statuses),
            ),
        )
        .group_by(MaintenanceRequest.unit_id)
        .all()
    )
    return {unit_id: count for unit_id, count in rows}


def _unit_pending_invite_summary(unit_ids):
    if not unit_ids:
        return {}

    rows = (
        UnitAccessInvite.query
        .filter(
            UnitAccessInvite.unit_id.in_(unit_ids),
            UnitAccessInvite.status == "pending",
            UnitAccessInvite.expires_at >= datetime.utcnow(),
        )
        .all()
    )
    pending = {}
    for invite in rows:
        pending.setdefault(invite.unit_id, set()).add((invite.role or "").lower())
    return pending


def _has_letting_agent_details(unit):
    return any(
        (value or "").strip()
        for value in [
            unit.letting_agent_name,
            unit.letting_agent_phone,
            unit.letting_agent_email,
            unit.letting_agent_address_line1,
            unit.letting_agent_address_line2,
            unit.letting_agent_city,
            unit.letting_agent_postcode,
        ]
    )


def _parse_date_arg(name):
    raw = (request.args.get(name) or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _parse_month_arg(name):
    raw = (request.args.get(name) or "").strip()
    if not raw:
        return None
    try:
        year, month = [int(part) for part in raw.split("-", 1)]
        return date(year, month, 1)
    except (TypeError, ValueError):
        return None


def _next_month(month_start):
    if month_start.month == 12:
        return date(month_start.year + 1, 1, 1)
    return date(month_start.year, month_start.month + 1, 1)


def _format_money(value, currency):
    if value in (None, ""):
        return ""
    return f"{currency or 'EUR'} {float(value):,.2f}"


def _latest_contracts_for_clients(client_ids):
    if not client_ids:
        return {}

    contracts = (
        ClientContract.query
        .filter(ClientContract.client_id.in_(client_ids))
        .order_by(ClientContract.client_id.asc(), ClientContract.end_date.desc(), ClientContract.created_at.desc())
        .all()
    )
    latest = {}
    for contract in contracts:
        latest.setdefault(contract.client_id, contract)
    return latest


def _client_review_csv(clients, latest_contracts):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Client",
        "Property Name",
        "Address",
        "City",
        "Region",
        "Country",
        "Client Type",
        "Units",
        "Property Manager",
        "Financial Controller",
        "Assistant",
        "Contract Value",
        "Contract Start",
        "Contract End",
        "Next Fee Increase",
    ])

    for client in clients:
        contract = latest_contracts.get(client.id)
        writer.writerow([
            client.name or "",
            client.property_name or "",
            ", ".join(part for part in [client.address_line1, client.address_line2] if part),
            client.city or "",
            client.region or "",
            client.country or "",
            client.client_type or "",
            client.number_of_units or "",
            client.assigned_pm.full_name if client.assigned_pm else "",
            client.assigned_fc.full_name if client.assigned_fc else "",
            client.assigned_assistant.full_name if client.assigned_assistant else "",
            _format_money(client.contract_value, client.currency),
            contract.start_date.isoformat() if contract and contract.start_date else "",
            contract.end_date.isoformat() if contract and contract.end_date else "",
            contract.next_fee_increase_date.isoformat() if contract and contract.next_fee_increase_date else "",
        ])

    filename = f"client-review-{date.today().isoformat()}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _client_manager_query(apply_filters=False):
    q = (
        Client.query
        .options(
            joinedload(Client.assigned_pm),
            joinedload(Client.assigned_fc),
            joinedload(Client.assigned_assistant),
        )
    )

    # Multi-tenant safety: scope to current user's company if present.
    if getattr(current_user, "company_id", None):
        q = q.filter(Client.company_id == current_user.company_id)

    if not apply_filters:
        return q

    location = (request.args.get("location") or "").strip()
    contract_start_month = _parse_month_arg("contract_start_month")
    contract_end_month = _parse_month_arg("contract_end_month")
    next_fee_month = _parse_month_arg("next_fee_month")
    has_contract_date_filter = any([contract_start_month, contract_end_month, next_fee_month])

    if location:
        like = f"%{location}%"
        q = q.filter(or_(
            Client.address_line1.ilike(like),
            Client.address_line2.ilike(like),
            Client.address.ilike(like),
            Client.city.ilike(like),
            Client.region.ilike(like),
            Client.country.ilike(like),
            Client.property_name.ilike(like),
        ))
    if has_contract_date_filter:
        contract_client_ids = db.session.query(ClientContract.client_id)
        if contract_start_month:
            contract_client_ids = contract_client_ids.filter(
                ClientContract.start_date >= contract_start_month,
                ClientContract.start_date < _next_month(contract_start_month),
            )
        if contract_end_month:
            contract_client_ids = contract_client_ids.filter(
                ClientContract.end_date >= contract_end_month,
                ClientContract.end_date < _next_month(contract_end_month),
            )
        if next_fee_month:
            contract_client_ids = contract_client_ids.filter(
                ClientContract.next_fee_increase_date >= next_fee_month,
                ClientContract.next_fee_increase_date < _next_month(next_fee_month),
            )
        q = q.filter(Client.id.in_(contract_client_ids.distinct()))

    return q


def _client_unit_directory(client_id: int):
    units = (
        Unit.query
        .filter(Unit.client_id == client_id)
        .order_by(Unit.block_name.asc(), Unit.core_name.asc(), Unit.unit_number.asc(), Unit.unit_label.asc())
        .all()
    )
    unit_ids = [unit.id for unit in units]
    owner_links = []
    resident_links = []
    balances_by_unit = _unit_balance_summary(unit_ids)
    open_works_by_unit = _unit_work_count_summary(unit_ids)
    open_requests_by_unit = _unit_open_request_count_summary(unit_ids)
    pending_invites_by_unit = _unit_pending_invite_summary(unit_ids)

    if unit_ids:
        owner_links = (
            UnitMembership.query
            .options(joinedload(UnitMembership.member))
            .filter(
                UnitMembership.unit_id.in_(unit_ids),
                UnitMembership.role == "owner",
                UnitMembership.is_current.is_(True),
            )
            .order_by(UnitMembership.unit_id.asc(), UnitMembership.is_primary.desc(), UnitMembership.id.asc())
            .all()
        )
        resident_links = (
            UnitMembership.query
            .options(joinedload(UnitMembership.member))
            .filter(
                UnitMembership.unit_id.in_(unit_ids),
                UnitMembership.role.in_(("resident", "tenant")),
                UnitMembership.is_current.is_(True),
            )
            .order_by(UnitMembership.unit_id.asc(), UnitMembership.is_primary.desc(), UnitMembership.id.asc())
            .all()
        )

    owners_by_unit = {}
    for link in owner_links:
        owners_by_unit.setdefault(link.unit_id, []).append(link)

    residents_by_unit = {}
    for link in resident_links:
        residents_by_unit.setdefault(link.unit_id, []).append(link)

    has_blocks = any((unit.block_name or "").strip() for unit in units)
    has_cores = any((unit.core_name or "").strip() for unit in units)
    tab_mode = "block" if has_blocks else ("core" if has_cores else "unit")

    rows = []
    resident_rows = []
    tab_values = set()
    for unit in units:
        block = (unit.block_name or "").strip()
        core = (unit.core_name or "").strip()
        area = (unit.area_name or "").strip()

        if tab_mode == "block":
            tab_value = block or "Unassigned"
        elif tab_mode == "core":
            tab_value = core or "Unassigned"
        else:
            tab_value = "All Units"

        tab_values.add(tab_value)
        unit_owner_links = owners_by_unit.get(unit.id, [])
        unit_resident_links = residents_by_unit.get(unit.id, [])
        pending_invite_roles = pending_invites_by_unit.get(unit.id, set())
        owner_names, owner_phone, owner_email = _owner_summary(unit_owner_links)
        balance_value = balances_by_unit.get(unit.id)
        occupancy_value = unit.occupancy_status or "unknown"
        occupancy_key = occupancy_value.lower()
        is_owner_occupied = occupancy_key in {"owner_occupied", "owner occupied", "owned", "owner occupied"}
        resident_source_links = unit_resident_links or (unit_owner_links if is_owner_occupied else [])
        resident_names, resident_phone, resident_email = _owner_summary(resident_source_links)
        owner_access_status, owner_access_label = _members_logix_access_status(
            unit_owner_links,
            pending_invite=bool(pending_invite_roles.intersection({"owner", "co_owner"})),
        )
        resident_access_status, resident_access_label = _members_logix_access_status(
            resident_source_links,
            pending_invite=bool(
                pending_invite_roles.intersection(
                    {"owner", "co_owner"} if resident_source_links == unit_owner_links and is_owner_occupied
                    else {"resident", "tenant"}
                )
            ),
        )
        status_value = unit.status or "Active"
        open_works_count = open_works_by_unit.get(unit.id, 0)
        open_requests_count = open_requests_by_unit.get(unit.id, 0)
        has_letting_agent = _has_letting_agent_details(unit)
        rows.append({
            "unit": unit,
            "tab": tab_value,
            "unit_display": unit.unit_number or "-",
            "block": block or area or "-",
            "core": core or "-",
            "block_core": " / ".join(part for part in [block, core] if part) or area or "-",
            "owner_names": owner_names,
            "owner_phone": owner_phone,
            "owner_email": owner_email,
            "member_access_status": owner_access_status,
            "member_access_label": owner_access_label,
            "balance_display": _format_money(balance_value, "EUR") if balance_value else "-",
            "occupancy": _occupancy_label(occupancy_value),
            "occupancy_key": occupancy_key,
            "status": status_value,
            "status_key": status_value.lower(),
            "sort_key": (
                _natural_key(block or tab_value),
                _natural_key(core),
                _natural_key(unit.unit_number or ""),
            ),
        })
        resident_rows.append({
            "unit": unit,
            "tab": tab_value,
            "unit_display": unit.unit_number or "-",
            "block": block or area or "-",
            "core": core or "-",
            "resident_names": resident_names,
            "resident_phone": resident_phone,
            "resident_email": resident_email,
            "member_access_status": resident_access_status,
            "member_access_label": resident_access_label,
            "has_letting_agent": has_letting_agent,
            "open_works_count": open_works_count,
            "open_requests_count": open_requests_count,
            "sort_key": (
                _natural_key(block or tab_value),
                _natural_key(core),
                _natural_key(unit.unit_number or ""),
            ),
        })

    rows.sort(key=lambda row: row["sort_key"])
    resident_rows.sort(key=lambda row: row["sort_key"])
    tabs = sorted(tab_values, key=lambda value: (value == "Unassigned", _natural_key(value)))
    return {"rows": rows, "resident_rows": resident_rows, "tabs": tabs, "tab_mode": tab_mode}


def _client_unit_access_invites(client_id: int):
    return (
        UnitAccessInvite.query
        .options(joinedload(UnitAccessInvite.unit))
        .filter(UnitAccessInvite.client_id == client_id)
        .order_by(UnitAccessInvite.created_at.desc())
        .limit(30)
        .all()
    )


def _client_unit_access_invite_summary(client_id: int):
    invites = UnitAccessInvite.query.filter(UnitAccessInvite.client_id == client_id).all()
    summary = {
        "total": len(invites),
        "pending": 0,
        "claimed": 0,
        "cancelled": 0,
        "expired": 0,
        "sent": 0,
        "failed": 0,
        "not_sent": 0,
    }
    for invite in invites:
        status = invite.status or "pending"
        delivery = invite.delivery_status or "not_sent"
        if status in summary:
            summary[status] += 1
        if delivery in summary:
            summary[delivery] += 1
    return summary


# 🧭 Manage Clients – list view (now includes `today` for expiry badges)
@super_admin_bp.route('/clients', methods=['GET'], endpoint='manage_clients')
@super_admin_required
@login_required
def manage_clients():
    """
    Lists clients for the current tenant/company, preloading related staff so the
    template can render without N+1 queries. We also inject `today` so the Jinja
    template can compute 'days to expiry' badges client-side.
    """
    clients = _client_manager_query().order_by(Client.name.asc()).all()
    latest_contracts = _latest_contracts_for_clients([client.id for client in clients])

    # Pass `today` for Jinja date math on contract_end_date
    # PLUS: expose the Jinja environment as `env` so legacy templates using `env.filters` won't 500
    return render_template(
        'super_admin/client/manage_clients.html',
        clients=clients,
        latest_contracts=latest_contracts,
        today=date.today(),
        env=current_app.jinja_env,   # ✅ add Jinja env for templates that reference `env.filters`
    )


# 👁️ View a single client (read-only details, edit gated in template by role)
@super_admin_bp.route('/clients/review-report', methods=['GET'], endpoint='client_review_report')
@super_admin_required
@login_required
def client_review_report():
    q = _client_manager_query(apply_filters=True)
    value_sort = (request.args.get("value_sort") or "").strip()
    if value_sort == "low_to_high":
        q = q.order_by(nullslast(Client.contract_value.asc()), Client.name.asc())
    elif value_sort == "high_to_low":
        q = q.order_by(nullslast(Client.contract_value.desc()), Client.name.asc())
    else:
        q = q.order_by(Client.name.asc())

    clients = q.all()
    latest_contracts = _latest_contracts_for_clients([client.id for client in clients])

    if request.args.get("export") == "csv":
        return _client_review_csv(clients, latest_contracts)

    return render_template(
        'super_admin/client/client_review_report.html',
        clients=clients,
        latest_contracts=latest_contracts,
        filters=request.args,
        today=date.today(),
        env=current_app.jinja_env,
    )


@super_admin_bp.route('/clients/<int:client_id>', methods=['GET'], endpoint='view_client')
@super_admin_required
@login_required
def view_client(client_id: int):
    """
    Shows a single client's details. We enforce tenant isolation so a Super Admin
    from one company cannot view another company's records.
    """
    client = (
        Client.query
        .options(
            joinedload(Client.assigned_pm),
            joinedload(Client.assigned_fc),
            joinedload(Client.assigned_assistant),
        )
        .get_or_404(client_id)
    )

    # Tenant isolation
    if getattr(current_user, "company_id", None) and client.company_id != current_user.company_id:
        abort(404)

    # Also pass `env` for templates that check `env.filters`
    return render_template(
        'super_admin/client/view_client.html',
        client=client,
        gar_client_context=build_client_context(client.id, getattr(current_user, "id", None)),
        grouped_units=grouped_units_for_client(client.id),
        unit_directory=_client_unit_directory(client.id),
        unit_access_invites=_client_unit_access_invites(client.id),
        unit_access_invite_summary=_client_unit_access_invite_summary(client.id),
        unit_count=client.units.count(),
        env=current_app.jinja_env,   # ✅ add Jinja env for templates that reference `env.filters`
    )


@super_admin_bp.route('/clients/<int:client_id>/units/generate', methods=['POST'], endpoint='generate_client_units')
@super_admin_required
@login_required
def generate_client_units(client_id: int):
    client = Client.query.get_or_404(client_id)

    if getattr(current_user, "company_id", None) and client.company_id != current_user.company_id:
        abort(404)

    summary = generate_units_for_client(client)
    if summary["errors"]:
        flash("Unit information could not be generated. Please review the development structure and try again.", "danger")
    elif summary["created"] > 0:
        flash(
            f"Unit information is ready. {summary['created']} unit records were created and linked to this client.",
            "success",
        )
    elif summary["skipped_existing"] > 0:
        flash(
            "Unit information is already up to date. No duplicate unit records were created.",
            "info",
        )
    else:
        flash(
            "No unit records were created. Add unit counts to the client structure, then generate again.",
            "warning",
        )

    return redirect(url_for('super_admin.view_client', client_id=client.id, tab='units'))


@super_admin_bp.route('/clients/<int:client_id>/bulk-member-invites', methods=['POST'], endpoint='bulk_member_invites')
@super_admin_required
@login_required
def bulk_member_invites(client_id: int):
    client = Client.query.get_or_404(client_id)

    if getattr(current_user, "company_id", None) and client.company_id != current_user.company_id:
        abort(404)

    summary = bulk_create_unit_access_invites_for_client(
        client,
        created_by_user_id=getattr(current_user, "id", None),
    )

    if summary.errors:
        flash(
            "Bulk member invites completed with some issues. Review the owner records and try again for any missing items.",
            "warning",
        )
    elif summary.created:
        flash(
            f"Members Logix portal codes created for {summary.created} owner record"
            f"{'' if summary.created == 1 else 's'}.",
            "success",
        )
    elif summary.skipped_existing_pending or summary.skipped_already_claimed or summary.skipped_already_linked:
        flash("No new portal codes were needed. Existing portal access or pending codes are already in place.", "info")
    else:
        flash("No portal codes were created. Add owner email addresses before running the bulk invite.", "warning")

    return redirect(url_for('super_admin.view_client', client_id=client.id, tab='units'))


@super_admin_bp.route('/clients/<int:client_id>/member-invites/send', methods=['POST'], endpoint='send_client_member_invites')
@super_admin_required
@login_required
def send_client_member_invites(client_id: int):
    client = Client.query.get_or_404(client_id)

    if getattr(current_user, "company_id", None) and client.company_id != current_user.company_id:
        abort(404)

    summary = send_pending_unit_access_invites_for_client(client.id)
    if summary.sent:
        flash(
            f"Members Logix portal invite email{' was' if summary.sent == 1 else 's were'} sent to "
            f"{summary.sent} owner{' record' if summary.sent == 1 else ' records'}.",
            "success",
        )
    elif summary.failed:
        flash("Portal invite emails could not be sent. Check email configuration and the invite tracking table.", "warning")
    else:
        flash("There are no pending portal invite emails ready to send for this client.", "info")

    return redirect(url_for('super_admin.view_client', client_id=client.id, tab='units'))


@super_admin_bp.route('/clients/<int:client_id>/member-invites/<int:invite_id>/send', methods=['POST'], endpoint='send_member_invite')
@super_admin_required
@login_required
def send_member_invite(client_id: int, invite_id: int):
    client = Client.query.get_or_404(client_id)
    invite = UnitAccessInvite.query.get_or_404(invite_id)

    if getattr(current_user, "company_id", None) and client.company_id != current_user.company_id:
        abort(404)
    if invite.client_id != client.id or invite.company_id != client.company_id:
        abort(404)

    if send_unit_access_invite(invite):
        flash("Members Logix portal invite email sent.", "success")
    else:
        flash("Portal invite email could not be sent. Review the delivery status for this invite.", "warning")

    return redirect(url_for('super_admin.view_client', client_id=client.id, tab='units'))


@super_admin_bp.route('/clients/<int:client_id>/member-invites/<int:invite_id>/cancel', methods=['POST'], endpoint='cancel_member_invite')
@super_admin_required
@login_required
def cancel_member_invite(client_id: int, invite_id: int):
    client = Client.query.get_or_404(client_id)
    invite = UnitAccessInvite.query.get_or_404(invite_id)

    if getattr(current_user, "company_id", None) and client.company_id != current_user.company_id:
        abort(404)
    if invite.client_id != client.id or invite.company_id != client.company_id:
        abort(404)

    if cancel_unit_access_invite(invite):
        flash("Members Logix portal invite cancelled.", "success")
    else:
        flash("Only pending portal invites can be cancelled.", "info")

    return redirect(url_for('super_admin.view_client', client_id=client.id, tab='units'))

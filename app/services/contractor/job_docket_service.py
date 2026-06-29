from __future__ import annotations

from datetime import date, datetime, time, timedelta

from app.extensions import db
from app.models.contractor.contractor_calendar_entry import ContractorCalendarEntry
from app.models.contractor.contractor_team import ContractorTeam
from app.models.contractor.job_docket import JobDocket
from app.models.core.user import User
from app.models.works.work_order import WorkOrder


AWAITING_SCHEDULING_STATUS = "Accepted - Awaiting Scheduling"
SCHEDULED_STATUS = "Scheduled"


def _display(value, fallback="-"):
    return value if value not in (None, "") else fallback


def _date_value(value):
    return value.isoformat() if value else None


def _time_value(value):
    return value.strftime("%H:%M") if value else None


def _unit_reference(unit) -> str:
    if not unit:
        return "-"
    parts = [unit.block_name, unit.core_name, unit.unit_number or unit.unit_label]
    return " / ".join(str(part) for part in parts if part) or unit.unit_label or "-"


def _job_location(work_order: WorkOrder) -> str:
    unit = work_order.unit
    client = work_order.client
    address_parts = []
    if unit:
        address_parts.extend([
            unit.address_line_1,
            unit.address_line_2,
            unit.town_city,
            unit.postal_code,
        ])
    if not any(address_parts) and client:
        address_parts.extend([
            getattr(client, "address_line1", None) or getattr(client, "address_line_1", None),
            getattr(client, "address_line2", None) or getattr(client, "address_line_2", None),
            getattr(client, "city", None),
            getattr(client, "postal_code", None),
        ])
    return ", ".join(str(part) for part in address_parts if part) or _unit_reference(unit)


def _standalone_location(docket: JobDocket) -> str:
    address_parts = [
        docket.standalone_address_line_1,
        docket.standalone_address_line_2,
        docket.standalone_town_city,
        docket.standalone_region,
        docket.standalone_postal_code,
        docket.standalone_country,
    ]
    return ", ".join(str(part) for part in address_parts if part) or _standalone_unit_reference(docket)


def _standalone_unit_reference(docket: JobDocket) -> str:
    parts = [
        docket.standalone_block_name,
        docket.standalone_core_name,
        docket.standalone_unit_number,
    ]
    return " / ".join(str(part) for part in parts if part) or "-"


def _work_order_contact(work_order: WorkOrder) -> dict:
    request = work_order.maintenance_request
    reporter = getattr(request, "requested_by", None) if request else None
    member = getattr(request, "member", None) if request else None
    return {
        "name": work_order.occupant_name
        or getattr(reporter, "full_name", None)
        or getattr(member, "full_name", None),
        "phone": work_order.occupant_phone
        or getattr(reporter, "mobile", None)
        or getattr(reporter, "direct_line", None)
        or getattr(member, "phone", None),
        "email": getattr(reporter, "email", None) or getattr(member, "email", None),
    }


def _docket_reference(docket_id: int) -> str:
    return f"JD-{datetime.utcnow().year}-{docket_id:05d}"


def _entry_title(docket: JobDocket) -> str:
    title = getattr(docket.work_order, "title", None) or docket.scope_of_works or "Standalone Job"
    return f"{docket.docket_number or 'Job Docket'} - {title}"


def create_standalone_job_docket(
    *,
    contractor_id: int,
    company_id: int | None = None,
    created_by_id: int | None = None,
    contractor_job_number: str | None = None,
    external_work_order_reference: str | None = None,
    client_name: str,
    property_name: str | None = None,
    address_line_1: str | None = None,
    address_line_2: str | None = None,
    town_city: str | None = None,
    region: str | None = None,
    postal_code: str | None = None,
    country: str | None = None,
    block_name: str | None = None,
    core_name: str | None = None,
    unit_number: str | None = None,
    required_trade: str | None = None,
    priority: str | None = None,
    scope_of_works: str | None = None,
    access_notes: str | None = None,
    contact_name: str | None = None,
    contact_phone: str | None = None,
    contact_email: str | None = None,
    instruction_source: str = "Manual Instruction",
) -> JobDocket:
    """Create a Contractor Logix job docket without requiring LogixPM/Works Logix."""

    docket = JobDocket(
        contractor_id=contractor_id,
        company_id=company_id,
        contractor_job_number=(contractor_job_number or "").strip() or None,
        external_work_order_reference=(external_work_order_reference or "").strip() or None,
        instruction_source=instruction_source,
        standalone_client_name=(client_name or "").strip(),
        standalone_property_name=(property_name or "").strip() or None,
        standalone_address_line_1=(address_line_1 or "").strip() or None,
        standalone_address_line_2=(address_line_2 or "").strip() or None,
        standalone_town_city=(town_city or "").strip() or None,
        standalone_region=(region or "").strip() or None,
        standalone_postal_code=(postal_code or "").strip() or None,
        standalone_country=(country or "").strip() or None,
        standalone_block_name=(block_name or "").strip() or None,
        standalone_core_name=(core_name or "").strip() or None,
        standalone_unit_number=(unit_number or "").strip() or None,
        assigned_engineer_id=created_by_id,
        status=AWAITING_SCHEDULING_STATUS,
        priority=(priority or "").strip() or "Normal",
        required_trade=(required_trade or "").strip() or None,
        scope_of_works=(scope_of_works or "").strip() or None,
        access_notes=(access_notes or "").strip() or None,
        contact_name=(contact_name or "").strip() or None,
        contact_phone=(contact_phone or "").strip() or None,
        contact_email=(contact_email or "").strip() or None,
        source_module="Contractor Logix",
        gar_chat_ready=True,
    )
    db.session.add(docket)
    db.session.flush()
    docket.docket_number = _docket_reference(docket.id)
    return docket


def ensure_job_docket_for_work_order(
    work_order: WorkOrder,
    *,
    accepted_by_id: int | None = None,
) -> tuple[JobDocket, bool]:
    """Create the Contractor Logix job docket once a work order is accepted."""

    if work_order.job_docket:
        return work_order.job_docket, False

    contact = _work_order_contact(work_order)
    unit = work_order.unit
    docket = JobDocket(
        work_order_id=work_order.id,
        contractor_id=work_order.contractor_id,
        company_id=work_order.company_id or getattr(work_order.client, "company_id", None),
        client_id=work_order.client_id,
        unit_id=work_order.unit_id,
        assigned_engineer_id=work_order.assigned_user_id or accepted_by_id,
        assigned_team_id=work_order.assigned_team_id,
        status=AWAITING_SCHEDULING_STATUS,
        priority=work_order.gar_risk_level or getattr(work_order.maintenance_request, "urgency_level", None) or "Normal",
        required_trade=work_order.business_type,
        scope_of_works=work_order.description,
        access_notes=getattr(unit, "entrance", None) or getattr(unit, "notes", None),
        contact_name=contact["name"],
        contact_phone=contact["phone"],
        contact_email=contact["email"],
        source_module="Contractor Logix",
        gar_chat_ready=True,
    )
    db.session.add(docket)
    db.session.flush()
    docket.docket_number = _docket_reference(docket.id)
    return docket, True


def calendar_context(contractor_id: int, *, filters: dict | None = None) -> dict:
    filters = filters or {}
    today = date.today()
    unscheduled = (
        JobDocket.query
        .filter(
            JobDocket.contractor_id == contractor_id,
            JobDocket.scheduled_date.is_(None),
            JobDocket.status == AWAITING_SCHEDULING_STATUS,
        )
        .order_by(JobDocket.created_at.asc())
        .all()
    )

    scheduled_query = ContractorCalendarEntry.query.filter(
        ContractorCalendarEntry.contractor_id == contractor_id,
    )
    if filters.get("engineer_id"):
        scheduled_query = scheduled_query.filter(ContractorCalendarEntry.assigned_engineer_id == filters["engineer_id"])
    if filters.get("team_id"):
        scheduled_query = scheduled_query.filter(ContractorCalendarEntry.assigned_team_id == filters["team_id"])
    if filters.get("status"):
        scheduled_query = scheduled_query.filter(ContractorCalendarEntry.calendar_status == filters["status"])

    scheduled_entries = (
        scheduled_query
        .order_by(
            ContractorCalendarEntry.scheduled_date.asc(),
            ContractorCalendarEntry.start_time.asc(),
            ContractorCalendarEntry.id.asc(),
        )
        .all()
    )
    engineers = (
        User.query
        .filter(User.contractor_id == contractor_id, User.is_active.is_(True))
        .order_by(User.full_name.asc())
        .all()
    )
    teams = (
        ContractorTeam.query
        .filter(ContractorTeam.contractor_id == contractor_id, ContractorTeam.is_active.is_(True))
        .order_by(ContractorTeam.name.asc())
        .all()
    )
    return {
        "contractor_id": contractor_id,
        "filters": filters,
        "unscheduled_dockets": unscheduled,
        "scheduled_entries": scheduled_entries,
        "engineers": engineers,
        "teams": teams,
        "stats": {
            "unscheduled": len(unscheduled),
            "scheduled": sum(1 for entry in scheduled_entries if entry.calendar_status == SCHEDULED_STATUS),
            "scheduled_today": sum(1 for entry in scheduled_entries if entry.scheduled_date == today and entry.calendar_status == SCHEDULED_STATUS),
            "overdue": sum(1 for entry in scheduled_entries if entry.scheduled_date < today and entry.calendar_status == SCHEDULED_STATUS),
            "completed": sum(1 for entry in scheduled_entries if entry.calendar_status in {"Completed", "Approved"}),
        },
    }


def contractor_today_schedule_context(
    contractor_id: int,
    *,
    days_ahead: int = 7,
) -> dict:
    """Build the mobile-ready contractor field schedule view."""

    today = date.today()
    horizon = today + timedelta(days=days_ahead)
    scheduled_entries = (
        ContractorCalendarEntry.query
        .filter(
            ContractorCalendarEntry.contractor_id == contractor_id,
            ContractorCalendarEntry.calendar_status == SCHEDULED_STATUS,
            ContractorCalendarEntry.scheduled_date <= horizon,
        )
        .order_by(
            ContractorCalendarEntry.scheduled_date.asc(),
            ContractorCalendarEntry.start_time.asc(),
            ContractorCalendarEntry.id.asc(),
        )
        .all()
    )
    overdue_entries = [entry for entry in scheduled_entries if entry.scheduled_date < today]
    today_entries = [entry for entry in scheduled_entries if entry.scheduled_date == today]
    upcoming_entries = [entry for entry in scheduled_entries if today < entry.scheduled_date <= horizon]
    return {
        "today": today,
        "horizon": horizon,
        "overdue_entries": overdue_entries,
        "today_entries": today_entries,
        "upcoming_entries": upcoming_entries,
        "stats": {
            "overdue": len(overdue_entries),
            "today": len(today_entries),
            "upcoming": len(upcoming_entries),
            "total_visible": len(scheduled_entries),
        },
    }


def _job_docket_payload(docket: JobDocket) -> dict:
    work_order_title = getattr(docket.work_order, "title", None)
    return {
        "id": docket.id,
        "docket_number": docket.docket_number,
        "work_order_id": docket.work_order_id,
        "work_order_reference": f"WO-{docket.work_order_id}" if docket.work_order_id else None,
        "external_work_order_reference": docket.external_work_order_reference,
        "title": work_order_title or docket.scope_of_works or "Standalone Job",
        "status": docket.status,
        "priority": docket.priority or "Normal",
        "required_trade": docket.required_trade,
        "instruction_source": docket.instruction_source,
        "client": {
            "id": docket.client_id,
            "name": docket.client.name if docket.client else docket.standalone_client_name,
        },
        "unit": {
            "id": docket.unit_id,
            "reference": _unit_reference(docket.unit) if docket.unit else _standalone_unit_reference(docket),
            "block": getattr(docket.unit, "block_name", None) or docket.standalone_block_name,
            "core": getattr(docket.unit, "core_name", None) or docket.standalone_core_name,
            "unit_number": getattr(docket.unit, "unit_number", None) or docket.standalone_unit_number,
        },
        "schedule": {
            "scheduled_date": _date_value(docket.scheduled_date),
            "start_time": _time_value(docket.start_time),
            "end_time": _time_value(docket.end_time),
            "estimated_duration_minutes": docket.estimated_duration_minutes,
        },
        "assignment": {
            "engineer_id": docket.assigned_engineer_id,
            "engineer_name": docket.assigned_engineer.full_name if docket.assigned_engineer else None,
            "team_id": docket.assigned_team_id,
            "team_name": docket.assigned_team.name if docket.assigned_team else None,
        },
        "contact": {
            "name": docket.contact_name,
            "phone": docket.contact_phone,
            "email": docket.contact_email,
        },
        "source_reference": {
            "model": "JobDocket",
            "record_id": docket.id,
            "module": "Contractor Logix",
        },
    }


def _calendar_entry_payload(entry: ContractorCalendarEntry) -> dict:
    return {
        "id": entry.id,
        "job_docket_id": entry.job_docket_id,
        "docket_number": entry.job_docket.docket_number if entry.job_docket else None,
        "work_order_id": entry.work_order_id,
        "title": entry.title,
        "calendar_status": entry.calendar_status,
        "priority": entry.priority or "Normal",
        "scheduled_date": _date_value(entry.scheduled_date),
        "start_time": _time_value(entry.start_time),
        "end_time": _time_value(entry.end_time),
        "estimated_duration_minutes": entry.estimated_duration_minutes,
        "location": entry.location,
        "notes": entry.notes,
        "client": {
            "id": entry.client_id,
            "name": entry.client.name if entry.client else None,
        },
        "unit": {
            "id": entry.unit_id,
            "reference": _unit_reference(entry.unit),
            "block": getattr(entry.unit, "block_name", None),
            "core": getattr(entry.unit, "core_name", None),
            "unit_number": getattr(entry.unit, "unit_number", None),
        },
        "assignment": {
            "engineer_id": entry.assigned_engineer_id,
            "engineer_name": entry.assigned_engineer.full_name if entry.assigned_engineer else None,
            "team_id": entry.assigned_team_id,
            "team_name": entry.assigned_team.name if entry.assigned_team else None,
        },
        "source_reference": {
            "model": "ContractorCalendarEntry",
            "record_id": entry.id,
            "module": "Contractor Logix",
        },
    }


def contractor_schedule_feed_payload(context: dict) -> dict:
    today_context = contractor_today_schedule_context(
        context["contractor_id"],
        days_ahead=context.get("days_ahead", 7),
    )
    unscheduled = [_job_docket_payload(docket) for docket in context.get("unscheduled_dockets", [])]
    scheduled = [_calendar_entry_payload(entry) for entry in context.get("scheduled_entries", [])]
    overdue = [_calendar_entry_payload(entry) for entry in today_context["overdue_entries"]]
    today = [_calendar_entry_payload(entry) for entry in today_context["today_entries"]]
    upcoming = [_calendar_entry_payload(entry) for entry in today_context["upcoming_entries"]]
    source_references = [
        item["source_reference"]
        for item in [*unscheduled, *scheduled]
        if item.get("source_reference")
    ]
    return {
        "context_type": "contractor_schedule",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "contractor_id": context["contractor_id"],
        "stats": {
            **context.get("stats", {}),
            "today": len(today),
            "upcoming_7_days": len(upcoming),
            "visible_schedule_items": len(scheduled),
        },
        "unscheduled_dockets": unscheduled,
        "scheduled_entries": scheduled,
        "today": today,
        "overdue": overdue,
        "upcoming": upcoming,
        "filters": context.get("filters", {}),
        "source_references": source_references,
        "app_contract": {
            "read_only": True,
            "mobile_ready": True,
            "offline_policy": "static-shell-only",
            "actions_route_to": "Contractor Logix web actions",
        },
    }


def build_standalone_job_docket_pack(docket: JobDocket) -> dict:
    """Build the read-only detail pack for a standalone Contractor Logix docket."""

    address_lines = [
        docket.standalone_address_line_1,
        docket.standalone_address_line_2,
        docket.standalone_town_city,
        docket.standalone_region,
        docket.standalone_postal_code,
        docket.standalone_country,
    ]
    return {
        "pdf_ready": False,
        "location": {
            "development": docket.standalone_client_name or "-",
            "property": docket.standalone_property_name or docket.standalone_client_name or "-",
            "unit": _standalone_unit_reference(docket),
            "block": docket.standalone_block_name or "-",
            "core": docket.standalone_core_name or "-",
            "address_lines": [part for part in address_lines if part],
            "access_notes": docket.access_notes or "-",
        },
        "classification": {
            "request_type": docket.instruction_source or "Manual Instruction",
        },
        "request_context": {
            "member_request_title": "Standalone contractor instruction",
        },
        "gar_history": {
            "contractor_safe_summary": (
                "Standalone Contractor Logix docket. Future GAR email intake can draft this data from inbound instructions."
            ),
        },
        "evidence_items": [],
        "lifecycle": [],
    }


def schedule_job_docket(
    *,
    docket_id: int,
    contractor_id: int,
    scheduled_date: date,
    start_time: time | None = None,
    end_time: time | None = None,
    estimated_duration_minutes: int | None = None,
    assigned_engineer_id: int | None = None,
    assigned_team_id: int | None = None,
    notes: str = "",
    scheduled_by_id: int | None = None,
) -> tuple[JobDocket | None, ContractorCalendarEntry | None]:
    docket = JobDocket.query.filter_by(id=docket_id, contractor_id=contractor_id).first()
    if not docket:
        return None, None

    if start_time and not end_time and estimated_duration_minutes:
        end_dt = datetime.combine(scheduled_date, start_time) + timedelta(minutes=estimated_duration_minutes)
        end_time = end_dt.time()

    docket.assigned_engineer_id = assigned_engineer_id
    docket.assigned_team_id = assigned_team_id
    docket.scheduled_date = scheduled_date
    docket.start_time = start_time
    docket.end_time = end_time
    docket.estimated_duration_minutes = estimated_duration_minutes
    docket.scheduling_notes = notes
    docket.status = SCHEDULED_STATUS
    if docket.work_order:
        docket.work_order.status = SCHEDULED_STATUS
        docket.work_order.assigned_user_id = assigned_engineer_id
        docket.work_order.assigned_team_id = assigned_team_id

    entry = (docket.calendar_entries or [None])[0]
    if not entry:
        entry = ContractorCalendarEntry(
            job_docket_id=docket.id,
            work_order_id=docket.work_order_id,
            contractor_id=docket.contractor_id,
            company_id=docket.company_id,
            client_id=docket.client_id,
            unit_id=docket.unit_id,
            created_by_id=scheduled_by_id,
        )
        db.session.add(entry)

    entry.assigned_engineer_id = assigned_engineer_id
    entry.assigned_team_id = assigned_team_id
    entry.title = _entry_title(docket)
    entry.scheduled_date = scheduled_date
    entry.start_time = start_time
    entry.end_time = end_time
    entry.estimated_duration_minutes = estimated_duration_minutes
    entry.calendar_status = SCHEDULED_STATUS
    entry.priority = docket.priority
    entry.location = _job_location(docket.work_order) if docket.work_order else _standalone_location(docket)
    entry.notes = notes
    entry.updated_by_id = scheduled_by_id
    db.session.flush()
    entry.ics_uid = entry.ics_uid or f"logixpm-job-docket-{docket.id}@logixpm.local"
    return docket, entry


def contractor_calendar_entries_for_ics(contractor_id: int) -> list[ContractorCalendarEntry]:
    return (
        ContractorCalendarEntry.query
        .filter(ContractorCalendarEntry.contractor_id == contractor_id)
        .order_by(ContractorCalendarEntry.scheduled_date.asc(), ContractorCalendarEntry.start_time.asc())
        .all()
    )


def _ics_escape(value: str | None) -> str:
    return (value or "").replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")


def _ics_datetime(day: date, clock: time | None, fallback_hour: int = 9) -> str:
    clock = clock or time(hour=fallback_hour)
    return datetime.combine(day, clock).strftime("%Y%m%dT%H%M%S")


def build_contractor_calendar_ics(entries: list[ContractorCalendarEntry]) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//LogixPM//Contractor Logix Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Contractor Logix Jobs",
    ]
    now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    for entry in entries:
        end_value = entry.end_time
        if not end_value and entry.start_time and entry.estimated_duration_minutes:
            end_value = (datetime.combine(entry.scheduled_date, entry.start_time) + timedelta(minutes=entry.estimated_duration_minutes)).time()
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{entry.ics_uid or f'logixpm-calendar-entry-{entry.id}@logixpm.local'}",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART:{_ics_datetime(entry.scheduled_date, entry.start_time)}",
            f"DTEND:{_ics_datetime(entry.scheduled_date, end_value, fallback_hour=10)}",
            f"SUMMARY:{_ics_escape(entry.title)}",
            f"LOCATION:{_ics_escape(entry.location)}",
            f"DESCRIPTION:{_ics_escape(entry.notes or _display(getattr(entry.job_docket, 'scope_of_works', None), 'Scheduled Contractor Logix job'))}",
            f"STATUS:{'CONFIRMED' if entry.calendar_status == SCHEDULED_STATUS else 'TENTATIVE'}",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"

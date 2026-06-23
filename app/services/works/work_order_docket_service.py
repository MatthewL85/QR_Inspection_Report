from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import BytesIO, StringIO
from typing import Any
import textwrap

from flask import current_app, render_template

from app.models.works.work_order import WorkOrder
from app.services.gar import build_work_order_relevant_history
from app.services.works.audit_pack_service import build_completion_evidence_pack
from app.services.works.workflow_service import build_work_order_lifecycle_for_audience


PDF_READY_STATUSES = {"accepted", "in progress", "completion submitted", "completed", "closed", "resolved", "returned"}


def _display(value: Any, fallback: str = "-") -> str:
    value = "" if value is None else str(value).strip()
    return value or fallback


def _date_value(value: Any) -> str:
    return value.strftime("%d %b %Y") if value else "-"


def _datetime_value(value: Any) -> str:
    return value.strftime("%d %b %Y %H:%M") if value else "-"


def _address_lines(*parts: Any) -> list[str]:
    return [_display(part, "").strip() for part in parts if _display(part, "").strip()]


def _unit_label(unit) -> str:
    if not unit:
        return "-"
    prefix = f"{unit.block_name} / " if getattr(unit, "block_name", None) else ""
    return f"{prefix}{unit.unit_number or unit.unit_label or unit.unit_name or unit.id}"


def _client_address(client) -> list[str]:
    if not client:
        return []
    return _address_lines(
        getattr(client, "address_line1", None) or getattr(client, "address", None),
        getattr(client, "address_line2", None),
        getattr(client, "city", None),
        getattr(client, "region", None),
        getattr(client, "postal_code", None),
        getattr(client, "country", None),
    )


def _unit_address(unit, client) -> list[str]:
    if not unit:
        return _client_address(client)
    return _address_lines(
        getattr(unit, "address_line_1", None),
        getattr(unit, "address_line_2", None),
        getattr(unit, "town_city", None),
        getattr(unit, "county_region", None),
        getattr(unit, "postal_code", None),
        getattr(unit, "country", None),
    ) or _client_address(client)


def _contact_card(label: str, name: str = "", phone: str = "", email: str = "", note: str = "") -> dict[str, str]:
    return {
        "label": label,
        "name": _display(name),
        "phone": _display(phone),
        "email": _display(email),
        "note": _display(note),
    }


def _unique_links(*groups: Any) -> list[str]:
    links: list[str] = []
    for group in groups:
        if not group:
            continue
        values = group if isinstance(group, list) else [group]
        for value in values:
            value = (value or "").strip()
            if value and value not in links:
                links.append(value)
    return links


def build_contractor_work_order_docket(work_order: WorkOrder, *, audience: str = "contractor") -> dict[str, Any]:
    """Build the contractor-visible work order pack from source records."""
    client = work_order.client
    unit = work_order.unit
    contractor = work_order.contractor_company
    maintenance_request = work_order.maintenance_request
    request_reporter = getattr(maintenance_request, "requested_by", None) if maintenance_request else None
    request_member = getattr(maintenance_request, "member", None) if maintenance_request else None
    creator = work_order.created_by
    accepted_by = work_order.accepted_contractor
    pm = getattr(client, "assigned_pm", None) if client else None
    assistant = getattr(client, "assigned_assistant", None) if client else None

    evidence_items = []
    if maintenance_request:
        request_links = _unique_links(
            maintenance_request.attachment_url,
            maintenance_request.doc_links,
            maintenance_request.photo_links,
        )
        for index, reference in enumerate(request_links, start=1):
            evidence_items.append({
                "source": "Members Logix",
                "label": f"Request attachment {index}",
                "reference": reference,
            })
    if work_order.attachments_count:
        evidence_items.append({
            "source": "Works Logix",
            "label": "Work order attachments",
            "reference": f"{work_order.attachments_count} attachment(s) recorded",
        })
    completion_evidence = build_completion_evidence_pack(work_order.completion)
    for index, reference in enumerate(completion_evidence.get("evidence_links") or [], start=1):
        evidence_items.append({
            "source": "Contractor Logix",
            "label": f"Completion evidence {index}",
            "reference": reference,
        })

    contacts = [
        _contact_card(
            "Property Manager",
            getattr(pm, "full_name", ""),
            getattr(pm, "mobile_phone", "") or getattr(pm, "direct_phone", ""),
            getattr(pm, "email", ""),
        ),
        _contact_card(
            "Assistant",
            getattr(assistant, "full_name", ""),
            getattr(assistant, "mobile_phone", "") or getattr(assistant, "direct_phone", ""),
            getattr(assistant, "email", ""),
        ),
        _contact_card(
            "Reported By / Occupier",
            work_order.occupant_name
            or getattr(request_reporter, "full_name", "")
            or getattr(request_member, "full_name", ""),
            work_order.occupant_phone
            or getattr(request_reporter, "mobile_phone", "")
            or getattr(request_reporter, "direct_phone", "")
            or getattr(request_member, "phone", "")
            or getattr(request_member, "alternate_phone", ""),
            getattr(request_reporter, "email", "") or getattr(request_member, "email", ""),
            work_order.occupant_apartment,
        ),
        _contact_card(
            "Contractor",
            getattr(contractor, "company_name", ""),
            getattr(contractor, "phone", ""),
            getattr(contractor, "email", ""),
            getattr(contractor, "contact_name", ""),
        ),
    ]

    return {
        "work_order": work_order,
        "reference": f"WO-{work_order.id}",
        "status_key": (work_order.status or "").strip().lower(),
        "pdf_ready": (work_order.status or "").strip().lower() in PDF_READY_STATUSES,
        "client": client,
        "unit": unit,
        "contractor": contractor,
        "maintenance_request": maintenance_request,
        "location": {
            "development": _display(getattr(client, "name", None)),
            "property": _display(getattr(client, "property_name", None)),
            "unit": _unit_label(unit),
            "block": _display(getattr(unit, "block_name", None)),
            "core": _display(getattr(unit, "core_name", None)),
            "area": _display(getattr(unit, "area_name", None)),
            "address_lines": _unit_address(unit, client),
            "access_notes": _display(getattr(unit, "entrance", None), ""),
        },
        "contacts": contacts,
        "dates": {
            "created": _datetime_value(work_order.created_at),
            "preferred_visit": _date_value(work_order.preferred_visit_date),
            "accepted_by": _display(getattr(accepted_by, "full_name", None)),
        },
        "classification": {
            "request_type": _display(work_order.request_type),
            "business_type": _display(work_order.business_type),
            "source": _display(work_order.source_system),
            "external_reference": _display(work_order.external_reference),
        },
        "privacy": {
            "scope": _display(work_order.privacy_scope),
            "access_masked": bool(work_order.access_masked),
        },
        "request_context": {
            "member_request_title": _display(getattr(maintenance_request, "title", None)),
            "member_request_category": _display(getattr(maintenance_request, "category", None)),
            "member_request_urgency": _display(getattr(maintenance_request, "urgency_level", None)),
            "member_request_description": _display(getattr(maintenance_request, "description", None)),
        },
        "evidence_items": evidence_items,
        "completion_evidence": build_completion_evidence_pack(work_order.completion),
        "lifecycle": build_work_order_lifecycle_for_audience(work_order, audience),
        "gar_history": build_work_order_relevant_history(work_order.id, audience=audience, _work_order=work_order),
        "created_by": _display(getattr(creator, "full_name", None)),
    }


def render_contractor_work_order_pdf(work_order: WorkOrder) -> BytesIO:
    """Render an accepted contractor work order docket as a PDF stream."""
    docket = build_contractor_work_order_docket(work_order)
    try:
        import os
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            from weasyprint import CSS, HTML  # type: ignore

        html = render_template("contractor/work_order_pdf.html", docket=docket)
        css_paths = []
        pdf_css = os.path.join(current_app.static_folder, "css", "pdf.css")
        if os.path.exists(pdf_css):
            css_paths.append(CSS(filename=pdf_css))

        pdf_bytes = HTML(string=html, base_url=current_app.root_path).write_pdf(stylesheets=css_paths)
    except Exception:
        pdf_bytes = _render_plain_work_order_pdf(docket)
    stream = BytesIO(pdf_bytes)
    stream.seek(0)
    return stream


def _pdf_escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_text_lines(docket: dict[str, Any]) -> list[str]:
    work_order = docket["work_order"]
    location = docket["location"]
    lines = [
        f"{docket['reference']} Contractor Work Order Pack",
        f"Status: {work_order.status or 'Assigned'}",
        "",
        "Work Order",
        f"Title: {work_order.title or docket['reference']}",
        f"Created: {docket['dates']['created']}",
        f"Type: {docket['classification']['business_type']}",
        f"Preferred Visit: {docket['dates']['preferred_visit']}",
        f"Description: {work_order.description or '-'}",
        "",
        "Location",
        f"Development: {location['development']}",
        f"Property: {location['property']}",
        f"Unit: {location['unit']}",
        f"Block: {location['block']}",
        f"Core: {location['core']}",
        "Address: " + ("; ".join(location["address_lines"]) if location["address_lines"] else "-"),
        f"Access Notes: {location['access_notes'] or '-'}",
        "",
        "Contacts",
    ]
    for contact in docket["contacts"]:
        lines.append(
            f"{contact['label']}: {contact['name']} | Phone: {contact['phone']} | Email: {contact['email']} | Note: {contact['note']}"
        )

    lines.extend(["", "Evidence"])
    if docket["evidence_items"]:
        for item in docket["evidence_items"]:
            lines.append(f"{item['source']} - {item['label']}: {item['reference']}")
    else:
        lines.append("No images, videos or document references are linked yet.")

    lines.extend([
        "",
        "GAR Context",
        docket["gar_history"].get("contractor_safe_summary") if docket.get("gar_history") else "No related history flagged.",
    ])
    return [line if line is not None else "-" for line in lines]


def _render_plain_work_order_pdf(docket: dict[str, Any]) -> bytes:
    """Create a minimal text PDF without external native dependencies."""
    page_width, page_height = 595, 842
    left_margin, top_y, line_height = 50, 800, 15
    wrapped_lines: list[str] = []
    for line in _pdf_text_lines(docket):
        if not line:
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(textwrap.wrap(str(line), width=92) or [""])

    pages: list[list[str]] = []
    current: list[str] = []
    max_lines = 48
    for line in wrapped_lines:
        if len(current) >= max_lines:
            pages.append(current)
            current = []
        current.append(line)
    if current:
        pages.append(current)

    objects: list[bytes] = []

    def add_object(payload: str | bytes) -> int:
        data = payload if isinstance(payload, bytes) else payload.encode("latin-1", "replace")
        objects.append(data)
        return len(objects)

    catalog_id = add_object("<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object(b"")
    font_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids: list[int] = []
    content_ids: list[int] = []
    for page_lines in pages or [["No work order content available."]]:
        commands = ["BT", "/F1 10 Tf", f"{left_margin} {top_y} Td"]
        first = True
        for line in page_lines:
            if not first:
                commands.append(f"0 -{line_height} Td")
            commands.append(f"({_pdf_escape(line)}) Tj")
            first = False
        commands.append("ET")
        content = "\n".join(commands).encode("latin-1", "replace")
        content_id = add_object(
            b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream"
        )
        page_id = add_object(
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {page_width} {page_height}] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
        )
        content_ids.append(content_id)
        page_ids.append(page_id)

    objects[pages_id - 1] = (
        f"<< /Type /Pages /Kids [{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] /Count {len(page_ids)} >>"
    ).encode("latin-1")

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, payload in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(payload)
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode("ascii")
    )
    return bytes(output)

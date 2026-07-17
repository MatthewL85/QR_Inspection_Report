# app/routes/super_admin/gar/gar_insights.py

from datetime import date
import csv
import io

from flask import Response, jsonify, render_template, request
from flask_login import login_required, current_user

from app.decorators.role import super_admin_required
from app.routes.super_admin import super_admin_bp
from app.services.gar import (
    attach_gar_capability_readiness,
    build_development_health_register,
    build_gar_answer_readiness,
    build_gar_capability_registry,
    build_gar_inquiry_response,
    build_operational_digest,
    build_portfolio_context,
)


HEALTH_STATUS_LABELS = {
    "danger": "At Risk",
    "warning": "Needs Review",
    "info": "Watch",
    "success": "Healthy",
}


def _health_register_filters():
    return {
        "search": (request.args.get("search") or "").strip(),
        "status": (request.args.get("status") or "").strip(),
        "sort": (request.args.get("sort") or "risk_first").strip(),
    }


def _filter_health_rows(rows, filters):
    filtered_rows = list(rows or [])
    search = filters["search"].lower()
    status = filters["status"]
    sort = filters["sort"]

    if search:
        filtered_rows = [
            row for row in filtered_rows
            if search in " ".join([
                str(row.get("client_name") or ""),
                str(row.get("property_name") or ""),
                str(row.get("city") or ""),
                str(row.get("status") or ""),
            ]).lower()
        ]

    if status:
        filtered_rows = [row for row in filtered_rows if row.get("tone") == status]

    if sort == "score_high":
        filtered_rows.sort(key=lambda row: (-int(row.get("score") or 0), row.get("client_name") or ""))
    elif sort == "score_low":
        filtered_rows.sort(key=lambda row: (int(row.get("score") or 0), row.get("client_name") or ""))
    elif sort == "works_high":
        filtered_rows.sort(key=lambda row: (-int(row.get("open_work_orders") or 0), row.get("client_name") or ""))
    elif sort == "name":
        filtered_rows.sort(key=lambda row: (row.get("client_name") or "").lower())
    else:
        filtered_rows.sort(key=lambda row: (
            int(row.get("score") or 0),
            -int(row.get("gar_attention_total") or 0),
            (row.get("client_name") or "").lower(),
        ))

    return filtered_rows


def _health_register_csv(rows):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Development",
        "Property",
        "City",
        "Health Score",
        "Health Status",
        "Open Works",
        "Resident Signals",
        "Finance Ready Units",
        "Generated Units",
        "Expected Units",
        "Pattern Memory Groups",
        "GAR Attention Total",
    ])

    for row in rows:
        writer.writerow([
            row.get("client_name") or "",
            row.get("property_name") or "",
            row.get("city") or "",
            row.get("score") or 0,
            row.get("status") or HEALTH_STATUS_LABELS.get(row.get("tone"), ""),
            row.get("open_work_orders") or 0,
            row.get("resident_signals") or 0,
            row.get("finance_ready_units") or 0,
            row.get("generated_units") or 0,
            row.get("expected_units") or 0,
            row.get("pattern_memory_groups") or 0,
            row.get("gar_attention_total") or 0,
        ])

    filename = f"gar-development-health-{date.today().isoformat()}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@super_admin_bp.route('/gar-insights', endpoint='gar_insights')
@login_required
@super_admin_required
def gar_insights():
    company_id = getattr(current_user, "company_id", None)
    gar_question = (request.args.get("gar_question") or "").strip()
    portfolio_context = build_portfolio_context(company_id=company_id)
    development_health_register = build_development_health_register(company_id=company_id)
    operational_digest = build_operational_digest(
        company_id=company_id,
        role_context="super_admin",
    )
    filters = _health_register_filters()
    original_rows = development_health_register.get("rows", [])
    filtered_rows = _filter_health_rows(original_rows, filters)

    if request.args.get("export") == "csv":
        return _health_register_csv(filtered_rows)

    gar_inquiry_response = None
    if gar_question:
        gar_inquiry_response = build_gar_inquiry_response(
            gar_question,
            role_context="super_admin",
            company_id=company_id,
            user_id=current_user.id,
            execute_source_query=True,
        )

    development_health_register = {
        **development_health_register,
        "rows": filtered_rows,
        "view_summary": {
            "records": len(filtered_rows),
            "total": len(original_rows),
        },
    }

    return render_template(
        'super_admin/gar/gar_insights.html',
        portfolio_context=portfolio_context,
        development_health_register=development_health_register,
        operational_digest=operational_digest,
        filters=filters,
        gar_question=gar_question,
        gar_inquiry_response=gar_inquiry_response,
        user=current_user,
    )


@super_admin_bp.route('/gar-insights/feed.json', endpoint='gar_insights_feed')
@login_required
@super_admin_required
def gar_insights_feed():
    company_id = getattr(current_user, "company_id", None)
    payload = build_operational_digest(
        company_id=company_id,
        role_context="super_admin",
    )
    return jsonify(attach_gar_capability_readiness(
        payload,
        role_context="super_admin",
        question=(request.args.get("question") or "").strip() or None,
    ))


@super_admin_bp.route('/gar-insights/capabilities.json', endpoint='gar_capabilities_feed')
@login_required
@super_admin_required
def gar_capabilities_feed():
    question = (request.args.get("question") or "").strip()
    payload = build_gar_capability_registry(role_context="super_admin")
    if question:
        payload["answer_readiness"] = build_gar_answer_readiness(
            question,
            role_context="super_admin",
        )
    return jsonify(payload)


@super_admin_bp.route('/gar-insights/inquiry.json', endpoint='gar_inquiry')
@login_required
@super_admin_required
def gar_inquiry():
    question = (request.args.get("question") or "").strip()
    company_id = getattr(current_user, "company_id", None)
    return jsonify(build_gar_inquiry_response(
        question,
        role_context="super_admin",
        company_id=company_id,
        user_id=current_user.id,
        execute_source_query=True,
    ))

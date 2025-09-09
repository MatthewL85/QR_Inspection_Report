# app/services/capex_service.py
from datetime import datetime
from sqlalchemy import func
from app.extensions import db
from app.models.client.client import Client
from app.models.capex.capex_request import CapexRequest
from app.schemas.capex.capex_profile import default_capex_profile
from app.validators.capex.capex_profile import validate_capex_profile

# Map request status to summary buckets
_STATUS_BUCKET = {
    "Pending": "planned_cost",
    "In Review": "planned_cost",
    "Approved": "approved_cost",
    "In Tender": "approved_cost",
    "In Progress": "in_progress_cost",
    "Done": "done_cost",
    "Rejected": None,
    "Deferred": "planned_cost",
  }

def recompute_capex_profile(client_id: int, actor_user_id: int | None = None):
    client = Client.query.get(client_id)
    if not client:
        raise ValueError("Client not found")

    profile = default_capex_profile()

    # Optional: pull “priority_areas” from tags on requests
    areas = (db.session.query(CapexRequest.area)
             .filter(CapexRequest.client_id == client_id)
             .group_by(CapexRequest.area)
             .order_by(func.count().desc())
             .limit(5)
             .all())
    profile["priority_areas"] = [a[0] for a in areas]

    # Next major works (earliest approved/in progress with estimated_cost)
    next_req = (CapexRequest.query
                .filter(CapexRequest.client_id == client_id,
                        CapexRequest.estimated_cost.isnot(None),
                        CapexRequest.status.in_(["Approved", "In Progress"]))
                .order_by(CapexRequest.submitted_at.asc())
                .first())
    profile["next_major_works"] = next_req.submitted_at.date().isoformat() if next_req else None

    # Build by_year and totals using estimated_cost + a simple year from submitted_at
    by_year = {}
    totals = {"planned_cost":0.0,"approved_cost":0.0,"in_progress_cost":0.0,"done_cost":0.0}

    q = (db.session.query(CapexRequest.submitted_at, CapexRequest.status, CapexRequest.estimated_cost)
         .filter(CapexRequest.client_id == client_id))
    for submitted_at, status, cost in q:
        if not cost:
            continue
        bucket = _STATUS_BUCKET.get(status)
        if not bucket:
            continue
        year = (submitted_at.year if submitted_at else None) or datetime.utcnow().year
        by_year.setdefault(year, {"planned_cost":0.0,"approved_cost":0.0,"in_progress_cost":0.0,"done_cost":0.0})
        by_year[year][bucket] += float(cost)
        totals[bucket] += float(cost)

    profile["projects_summary"]["by_year"] = by_year
    profile["projects_summary"]["totals"] = totals

    profile["last_updated_by"] = actor_user_id
    profile["last_updated_at"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    # validate & persist
    validate_capex_profile(profile)
    client.capex_profile = profile
    if client.capex_status == "not_created" and (by_year or totals["planned_cost"] > 0):
        client.capex_status = "in_progress"
    db.session.commit()
    return profile

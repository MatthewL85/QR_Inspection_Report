# app/routes/devtools.py
from flask import Blueprint, current_app, Response

devtools_bp = Blueprint("devtools", __name__)

@devtools_bp.route("/__routes")
def list_routes():
    out = []
    for rule in sorted(current_app.url_map.iter_rules(), key=lambda r: r.rule):
        methods = ",".join(sorted(m for m in rule.methods if m not in ("HEAD","OPTIONS")))
        out.append(f"{rule.rule:40s} → {rule.endpoint:35s}   [{methods}]")
    return Response("\n".join(out), mimetype="text/plain")

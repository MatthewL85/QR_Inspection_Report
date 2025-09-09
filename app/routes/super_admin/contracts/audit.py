# app/routes/super_admin/contracts/audits.py
from __future__ import annotations

from flask import request, render_template
from sqlalchemy import desc

from app import db
from app.decorators import super_admin_required
from app.models import ContractAudit, User
from app.models.contracts import ClientContract
from app.routes.super_admin import super_admin_bp

# If you created app/utils/diff.py earlier, we’ll use it.
# Otherwise, uncomment the fallback below.
try:
    from app.utils.diff import changed_keys  # returns a list of changed top-level keys
except Exception:  # pragma: no cover
    def changed_keys(before, after):
        before = before or {}
        after = after or {}
        keys = set(before.keys()) | set(after.keys())
        return sorted([k for k in keys if before.get(k) != after.get(k)])

@super_admin_bp.route("/contracts/audits", methods=["GET"], endpoint="contract_audits_list")
@super_admin_required
def contract_audits_list():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 25, type=int), 100)

    contract_id = request.args.get("contract_id", type=int)
    action = (request.args.get("action") or "").strip() or None
    actor_id = request.args.get("actor_id", type=int)

    q = ContractAudit.query
    if contract_id:
        q = q.filter(ContractAudit.contract_id == contract_id)
    if action:
        q = q.filter(ContractAudit.action == action)
    if actor_id:
        q = q.filter(ContractAudit.actor_id == actor_id)

    audits = q.order_by(desc(ContractAudit.happened_at)).paginate(page=page, per_page=per_page, error_out=False)

    # Preload related objects for display
    contract_map: dict[int, ClientContract] = {}
    actor_map: dict[int, User] = {}
    if audits.items:
        cids = {a.contract_id for a in audits.items if a.contract_id}
        uids = {a.actor_id for a in audits.items if a.actor_id}
        if cids:
            for c in ClientContract.query.filter(ClientContract.id.in_(list(cids))).all():
                contract_map[c.id] = c
        if uids:
            for u in User.query.filter(User.id.in_(list(uids))).all():
                actor_map[u.id] = u

    # Compute Delta keys for the table badges
    changed_by_id = {a.id: changed_keys(a.before_data, a.after_data) for a in audits.items}

    # Distinct actions for the filter dropdown
    actions = [r[0] for r in db.session.execute(db.text("SELECT DISTINCT action FROM contract_audits ORDER BY action")).all()]

    return render_template(
        "super_admin/contracts/audits_list.html",
        audits=audits,
        contract_map=contract_map,   # matches your template
        actor_map=actor_map,         # matches your template
        changed_by_id=changed_by_id, # matches your template
        actions=actions,
        filters={"contract_id": contract_id, "action": action, "actor_id": actor_id, "per_page": per_page},
    )

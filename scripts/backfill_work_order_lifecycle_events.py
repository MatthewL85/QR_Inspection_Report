r"""Backfill persisted Works Logix lifecycle events for existing work orders.

Run from the project root:
    .\venv\Scripts\python.exe scripts\backfill_work_order_lifecycle_events.py --dry-run
    .\venv\Scripts\python.exe scripts\backfill_work_order_lifecycle_events.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill work order lifecycle events.")
    parser.add_argument("--dry-run", action="store_true", help="Report what would be created, then roll back.")
    args = parser.parse_args()

    from app import create_app
    from app.extensions import db
    from app.models.works.work_order import WorkOrder
    from app.services.works.workflow_service import backfill_work_order_lifecycle_events

    app = create_app()
    total_created = 0
    total_work_orders = 0

    with app.app_context():
        work_orders = WorkOrder.query.order_by(WorkOrder.id.asc()).all()
        total_work_orders = len(work_orders)
        for work_order in work_orders:
            total_created += backfill_work_order_lifecycle_events(work_order)

        if args.dry_run:
            db.session.rollback()
        else:
            db.session.commit()

    mode = "DRY RUN" if args.dry_run else "APPLIED"
    print("Works lifecycle backfill")
    print(f"- Mode: {mode}")
    print(f"- Work orders checked: {total_work_orders}")
    print(f"- Lifecycle events {'identified' if args.dry_run else 'created'}: {total_created}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

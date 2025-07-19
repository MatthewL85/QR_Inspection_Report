from decimal import Decimal
from app.extensions import db
from app.models.finance.lease_apportionment_schedule import LeaseApportionmentSchedule
from app.models.members.unit import Unit
from app.models.finance.apportionment_audit_log import ApportionmentAuditLog

class ApportionmentEngine:
    """
    Smart engine for calculating unit budget allocations based on lease rules,
    with AI/GAR audit trail support.
    """

    def __init__(self, client_id, budget_amount):
        self.client_id = client_id
        self.budget_amount = Decimal(budget_amount)
        self.schedules = LeaseApportionmentSchedule.query.filter_by(client_id=client_id).all()
        self.ai_audit = []

        # Preload all units to avoid N+1 queries
        unit_ids = [s.unit_id for s in self.schedules]
        self.unit_map = {u.id: u for u in Unit.query.filter(Unit.id.in_(unit_ids)).all()}

        # Pre-calculate totals
        self.total_units = len(self.schedules)
        self.total_percentage = sum(Decimal(s.value) for s in self.schedules if s.method == 'Percentage')

        self.total_unit_size = sum(
            Decimal(self.unit_map.get(s.unit_id).size or 0)
            for s in self.schedules
            if s.method == 'UnitSize' and self.unit_map.get(s.unit_id)
        )

    def run_allocation(self):
        allocations = []

        for s in self.schedules:
            method = s.method
            value = Decimal(s.value)
            unit = self.unit_map.get(s.unit_id)
            unit_size = Decimal(unit.size or 0) if unit else Decimal('0')
            amount = Decimal('0.00')
            reason = ''
            gar_flag = False
            gar_notes = ''

            # --- Allocation Logic ---
            if not unit:
                reason = 'Unit not found'
                gar_flag = True
                gar_notes = 'Missing unit for apportionment schedule.'
            elif method == 'Equal':
                amount = round(self.budget_amount / self.total_units, 2)
                reason = 'Equally divided among all units'
            elif method == 'Percentage' and self.total_percentage > 0:
                proportion = value / self.total_percentage
                amount = round(self.budget_amount * proportion, 2)
                reason = f'{value}% of budget as per lease'
            elif method == 'UnitSize' and self.total_unit_size > 0:
                proportion = unit_size / self.total_unit_size
                amount = round(self.budget_amount * proportion, 2)
                reason = f'Based on unit size: {unit_size} sqm'
            else:
                reason = f"Unknown method '{method}' - skipped"
                gar_flag = True
                gar_notes = 'Unrecognized apportionment method. Please review lease schedule.'

            # --- GAR-Aware AI Metadata ---
            self.ai_audit.append({
                'unit_id': s.unit_id,
                'method': method,
                'amount': float(amount),
                'basis_value': float(value),
                'unit_size': float(unit_size),
                'ai_reasoning': reason,
                'gar_flagged': gar_flag,
                'gar_notes': gar_notes,
            })

            allocations.append({
                'unit_id': s.unit_id,
                'amount': amount,
                'method': method,
                'reason': reason
            })

        return allocations

    def get_gar_audit(self):
        """
        Returns the detailed allocation log with AI reasoning & GAR review fields.
        """
        return self.ai_audit

    def save_gar_audit_to_db(self):
        """
        Persists the AI/GAR audit log to the database.
        """
        audit_logs = []

        for entry in self.ai_audit:
            log = ApportionmentAuditLog(
                client_id=self.client_id,
                unit_id=entry['unit_id'],
                method=entry['method'],
                amount=Decimal(entry['amount']),
                basis_value=Decimal(entry['basis_value']),
                unit_size=Decimal(entry['unit_size']),
                ai_reasoning=entry['ai_reasoning'],
                gar_flagged=entry['gar_flagged'],
                gar_notes=entry['gar_notes']
            )
            audit_logs.append(log)

        db.session.bulk_save_objects(audit_logs)
        db.session.commit()

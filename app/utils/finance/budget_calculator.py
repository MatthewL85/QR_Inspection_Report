from decimal import Decimal
from app.models.finance.lease_apportionment_schedule import LeaseApportionmentSchedule
from app.models.members.unit import Unit
from app.extensions import db
from datetime import datetime

class BudgetCalculator:
    @staticmethod
    def calculate_budget_allocation(budget_amount, client_id, return_gar_meta=False):
        """
        Allocates the budget amount across units based on lease apportionment schedule.
        Supports Equal, Percentage, and UnitSize methods.
        Adds support for AI and GAR flagging for policy insight.

        :param budget_amount: Total budget amount (Decimal or float)
        :param client_id: ID of the client (development)
        :param return_gar_meta: If True, include AI-ready GAR metadata per allocation
        :return: List of dicts [{unit_id, amount, method, apportionment_value, ...}, ...]
        """
        budget_amount = Decimal(budget_amount)
        allocations = []
        gar_notes = []  # for GAR Chat review or audit log

        schedules = LeaseApportionmentSchedule.query.filter_by(client_id=client_id).all()

        percentage_total = sum(s.value for s in schedules if s.method == 'Percentage')
        unit_size_total = sum((Unit.query.get(s.unit_id).size or 0) for s in schedules if s.method == 'UnitSize')

        for schedule in schedules:
            method = schedule.method
            value = schedule.value or 0
            unit_id = schedule.unit_id
            amount = Decimal('0.00')
            ai_flag = None
            ai_confidence = None
            gar_flag = None
            gar_reason = None

            if method == 'Equal':
                equal_share = budget_amount / len(schedules)
                amount = round(equal_share, 2)
                gar_reason = "Equal share used across all units."

            elif method == 'Percentage':
                proportion = value / percentage_total if percentage_total > 0 else 0
                amount = round(budget_amount * Decimal(proportion), 2)
                if value > 100:
                    gar_flag = "Over 100% allocation"
                    gar_reason = f"Percentage value exceeds standard cap: {value}%"

            elif method == 'UnitSize':
                unit = Unit.query.get(unit_id)
                size = unit.size or 0
                proportion = size / unit_size_total if unit_size_total > 0 else 0
                amount = round(budget_amount * Decimal(proportion), 2)
                gar_reason = f"Proportional to unit size: {size} sqm"

            elif method == 'AIWeighted':
                amount = Decimal('0.00')  # placeholder
                ai_flag = "Awaiting AI model support"
                gar_reason = "AI-based allocation method not yet active"

            allocation = {
                'unit_id': unit_id,
                'amount': amount,
                'method': method,
                'apportionment_value': value,
                'timestamp': datetime.utcnow(),
            }

            if return_gar_meta:
                allocation.update({
                    'gar_flag': gar_flag,
                    'gar_reason': gar_reason,
                    'ai_flag': ai_flag,
                    'ai_confidence': ai_confidence,
                })

            allocations.append(allocation)

        return allocations

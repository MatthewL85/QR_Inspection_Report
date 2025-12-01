# app/services/unit_service.py

from app.extensions import db

from app.models.members.unit import Unit
from app.models.members.member import Member, member_units
from app.models.members.resident import Resident

from app.models.finance.invoice import Invoice
from app.models.works.work_order import WorkOrder
from app.models.core.document import Document


class UnitService:

    @staticmethod
    def get_unit_by_id(unit_id: int):
        """
        Returns a complete Unit data bundle for UI rendering.
        Works with the new Unit + Member + Resident architecture.
        Fully compatible with LogixPM, Members Logix, Works Logix, and Finance Logix.
        """

        # ---------------------------------
        # Fetch base Unit
        # ---------------------------------
        unit = (
            db.session.query(Unit)
            .filter(Unit.id == unit_id)
            .first()
        )

        if not unit:
            return None

        # ---------------------------------
        # OWNERS (Members)
        # ---------------------------------
        # Using association table: member_units
        owners = unit.members.all()      # list[Member]

        # For consistent template usage
        owner_entities = owners

        # ---------------------------------
        # RESIDENTS
        # ---------------------------------
        residents = unit.residents       # backref from Resident.unit
        resident_entities = residents    # they are already usable objects

        # ---------------------------------
        # FINANCE (Invoices)
        # ---------------------------------
        invoices = []
        if hasattr(unit, "invoices"):
            invoices = unit.invoices.all()

        # ---------------------------------
        # WORK ORDERS
        # ---------------------------------
        work_orders = []
        if hasattr(unit, "work_orders"):
            work_orders = unit.work_orders.all()

        # ---------------------------------
        # DOCUMENTS (Lease, Surveys, Legal, etc.)
        # ---------------------------------
        documents = unit.documents.all() if unit.documents else []

        # ---------------------------------
        # CHILD UNITS (car spaces, storage rooms)
        # ---------------------------------
        child_units = unit.child_units if hasattr(unit, "child_units") else []

        # ---------------------------------
        # Return UI-safe data package
        # ---------------------------------
        return {
            "unit": unit,
            "client": unit.client,
            "company": unit.company,
            "block": unit.block,
            "core": unit.core,

            "owners": owners,
            "owner_entities": owner_entities,

            "residents": residents,
            "resident_entities": resident_entities,

            "invoices": invoices,
            "work_orders": work_orders,
            "documents": documents,

            "child_units": child_units,
        }

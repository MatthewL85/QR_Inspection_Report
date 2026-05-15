# app/services/unit_service.py

from __future__ import annotations
from typing import Any, Dict, List, Optional

from sqlalchemy import or_

from app.extensions import db
from app.models.members.unit import Unit
from app.models.members.member import Member
from app.models.members.member import member_units
from app.models.client.client import Client


class UnitService:
    # ------------------------------------------------------------
    # PAGINATED UNIT LISTING
    # ------------------------------------------------------------
    @staticmethod
    def list_units_for_company(
        company_id: int,
        page: int = 1,
        per_page: int = 25,
        client_id: Optional[int] = None,
        search: Optional[str] = None,
        block_name: Optional[str] = None,
        core_name: Optional[str] = None,
        only_active: bool = True,
    ):
        query = Unit.query.filter(Unit.company_id == company_id)

        if client_id:
            query = query.filter(Unit.client_id == client_id)

        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(
                    Unit.unit_label.ilike(like),
                    Unit.block_name.ilike(like),
                    Unit.core_name.ilike(like),
                )
            )

        if block_name:
            query = query.filter(Unit.block_name.ilike(f"%{block_name}%"))
        if core_name:
            query = query.filter(Unit.core_name.ilike(f"%{core_name}%"))

        if only_active:
            query = query.filter(Unit.status == "active")

        query = query.order_by(
            Unit.block_name.asc(),
            Unit.core_name.asc(),
            Unit.unit_label.asc(),
        )

        return query.paginate(page=page, per_page=per_page, error_out=False)

    # ------------------------------------------------------------
    # GET A SINGLE UNIT (Enterprise View)
    # ------------------------------------------------------------
    @staticmethod
    def get_unit(unit_id: int) -> Optional[Dict[str, Any]]:
        unit = Unit.query.get(unit_id)
        if not unit:
            return None

        client = Client.query.get(unit.client_id)
        company = client.company if client else None

        # Ownership & Tenancy Timelines
        owners = UnitService.get_current_owners(unit_id)
        tenants = UnitService.get_current_tenants(unit_id)
        ownership_history = UnitService.get_ownership_history(unit_id)
        tenancy_history = UnitService.get_tenancy_history(unit_id)

        return {
            "unit": unit,
            "client": client,
            "company": company,
            "owner_entities": owners,
            "tenant_entities": tenants,
            "ownership_history": ownership_history,
            "tenancy_history": tenancy_history,
            # stubs for later integrations:
            "invoices": [],
            "work_orders": [],
            "documents": [],
            "child_units": unit.child_units if hasattr(unit, "child_units") else [],
        }

    # ------------------------------------------------------------
    # CREATION
    # ------------------------------------------------------------
    @staticmethod
    def create_unit(form, company_id: int) -> Unit:
        unit = Unit(
            company_id=company_id,
            client_id=form.get("client_id"),
            unit_label=form.get("unit_label"),
            unit_category=form.get("unit_category"),
            unit_type=form.get("unit_type"),
            block_name=form.get("block_name"),
            core_name=form.get("core_name"),
            floor_number=form.get("floor_number"),
            entrance=form.get("entrance"),
            square_meters=form.get("square_meters") or None,
            parent_unit_id=form.get("parent_unit_id") or None,
            status=form.get("status", "active"),
            is_common_area=bool(form.get("is_common_area")),
            service_charge_scheme=form.get("service_charge_scheme"),
            service_charge_percent=form.get("service_charge_percent") or None,
            service_charge_amount=form.get("service_charge_amount") or None,
            billing_frequency=form.get("billing_frequency"),
            financial_year_start=form.get("financial_year_start") or None,
            financial_year_end=form.get("financial_year_end") or None,
            notes=form.get("notes"),
        )

        db.session.add(unit)
        db.session.commit()
        return unit

    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------
    @staticmethod
    def update_unit(unit_id: int, form, company_id: int) -> bool:
        unit = Unit.query.filter_by(id=unit_id, company_id=company_id).first()
        if not unit:
            return False

        for field in [
            "client_id", "unit_label", "unit_category", "unit_type",
            "block_name", "core_name", "floor_number", "entrance",
            "service_charge_scheme", "billing_frequency", "notes"
        ]:
            setattr(unit, field, form.get(field))

        unit.is_common_area = bool(form.get("is_common_area"))

        # numeric fields
        unit.square_meters = form.get("square_meters") or None
        unit.service_charge_percent = form.get("service_charge_percent") or None
        unit.service_charge_amount = form.get("service_charge_amount") or None

        # dates
        unit.financial_year_start = form.get("financial_year_start") or None
        unit.financial_year_end = form.get("financial_year_end") or None

        # hierarchy
        unit.parent_unit_id = form.get("parent_unit_id") or None

        db.session.commit()
        return True

    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------
    @staticmethod
    def delete_unit(unit_id: int, company_id: int) -> bool:
        unit = Unit.query.filter_by(id=unit_id, company_id=company_id).first()
        if not unit:
            return False
        db.session.delete(unit)
        db.session.commit()
        return True

    # ==================================================================================
    # 🟦 ENTERPRISE FEATURE: TIMELINE HELPERS
    # ==================================================================================

    # ------------------------------
    # CURRENT OWNERS
    # ------------------------------
    @staticmethod
    def get_current_owners(unit_id: int) -> List[Dict[str, Any]]:
        sql = (
            db.session.query(Member, member_units)
            .join(member_units, Member.id == member_units.c.member_id)
            .filter(
                member_units.c.unit_id == unit_id,
                Member.is_owner == True,
                member_units.c.sale_date.is_(None),
            )
            .all()
        )

        result = []
        for member, link in sql:
            result.append({
                "member": member,
                "purchase_date": link.purchase_date,
                "ownership_percentage": link.ownership_percentage,
                "ownership_type": link.ownership_type,
            })
        return result

    # ------------------------------
    # CURRENT TENANTS
    # ------------------------------
    @staticmethod
    def get_current_tenants(unit_id: int) -> List[Dict[str, Any]]:
        sql = (
            db.session.query(Member, member_units)
            .join(member_units, Member.id == member_units.c.member_id)
            .filter(
                member_units.c.unit_id == unit_id,
                Member.is_owner == False,
                member_units.c.tenancy_status == "active",
            )
            .all()
        )

        result = []
        for member, link in sql:
            result.append({
                "member": member,
                "tenancy_start_date": link.tenancy_start_date,
                "tenancy_end_date": link.tenancy_end_date,
                "tenancy_status": link.tenancy_status,
            })
        return result

    # ------------------------------
    # FULL OWNERSHIP HISTORY
    # ------------------------------
    @staticmethod
    def get_ownership_history(unit_id: int) -> List[Dict[str, Any]]:
        sql = (
            db.session.query(Member, member_units)
            .join(member_units, Member.id == member_units.c.member_id)
            .filter(
                member_units.c.unit_id == unit_id,
                Member.is_owner == True,
            )
            .order_by(member_units.c.purchase_date.asc())
            .all()
        )

        result = []
        for member, link in sql:
            result.append({
                "member": member,
                "purchase_date": link.purchase_date,
                "sale_date": link.sale_date,
                "ownership_percentage": link.ownership_percentage,
                "ownership_type": link.ownership_type,
            })
        return result

    # ------------------------------
    # FULL TENANCY HISTORY
    # ------------------------------
    @staticmethod
    def get_tenancy_history(unit_id: int) -> List[Dict[str, Any]]:
        sql = (
            db.session.query(Member, member_units)
            .join(member_units, Member.id == member_units.c.member_id)
            .filter(
                member_units.c.unit_id == unit_id,
                Member.is_owner == False,
            )
            .order_by(member_units.c.tenancy_start_date.asc())
            .all()
        )

        result = []
        for member, link in sql:
            result.append({
                "member": member,
                "tenancy_start_date": link.tenancy_start_date,
                "tenancy_end_date": link.tenancy_end_date,
                "tenancy_status": link.tenancy_status,
            })
        return result

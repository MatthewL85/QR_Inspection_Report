# app/services/unit_service.py

from __future__ import annotations
from datetime import datetime
import math
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import or_

from app.extensions import db
from app.models.members.unit import Unit
from app.models.members.member import Member
from app.models.members.unit_membership import UnitMembership
from app.models.client.client import Client
from app.models.maintenance.maintenance_request import MaintenanceRequest
from app.models.works.work_order import WorkOrder
from app.services.work_order_reopen_service import WorkOrderReopenService


def _clean(value: Any) -> Optional[str]:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _parse_date(value: Any):
    value = _clean(value)
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _has_person_payload(form, prefix: str) -> bool:
    fields = [
        "first_name",
        "last_name",
        "email",
        "phone",
        "alternate_phone",
        "postal_address_line1",
        "postal_postcode",
    ]
    return any(_clean(form.get(f"{prefix}_{field}")) for field in fields)


def _is_open_status(status: Any) -> bool:
    closed_statuses = {
        "completed",
        "complete",
        "closed",
        "resolved",
        "cancelled",
        "canceled",
        "rejected",
    }
    value = (status or "").strip().lower()
    return value not in closed_statuses


class SimplePagination:
    def __init__(self, items: List[Any], page: int, per_page: int, total: int):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = math.ceil(total / per_page) if per_page else 0
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1
        self.next_num = page + 1

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if (
                num <= left_edge
                or (num > self.page - left_current - 1 and num < self.page + right_current)
                or num > self.pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num


def _natural_key(value: Any):
    value = _clean(value) or ""
    parts = re.split(r"(\d+)", value.lower())
    return [int(part) if part.isdigit() else part for part in parts]


def _directory_search_text(unit: Unit) -> str:
    owner_bits = []
    try:
        links = unit.membership_links.filter_by(role="owner", is_current=True).all()
        for link in links:
            if link.member:
                owner_bits.extend([
                    link.member.full_name,
                    link.member.phone,
                    link.member.email,
                ])
    except Exception:
        pass

    values = [
        unit.unit_label,
        unit.unit_number,
        unit.block_name,
        unit.core_name,
        unit.occupancy_status,
        unit.client.name if unit.client else None,
        *owner_bits,
    ]
    return " ".join(str(value).lower() for value in values if value)


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

        if block_name:
            query = query.filter(Unit.block_name.ilike(f"%{block_name}%"))
        if core_name:
            query = query.filter(Unit.core_name.ilike(f"%{core_name}%"))

        if only_active:
            query = query.filter(Unit.is_active.is_(True))

        units = query.all()

        if search:
            search_value = search.lower().strip()
            units = [unit for unit in units if search_value in _directory_search_text(unit)]

        has_blocks = any(_clean(unit.block_name) for unit in units)
        has_cores = any(_clean(unit.core_name) for unit in units)

        def sort_key(unit: Unit):
            unit_number = unit.unit_number or unit.unit_label
            if has_blocks:
                location = _clean(unit.block_name)
                location_rank = 0 if location else 1
                secondary = _clean(unit.core_name) or ""
            elif has_cores:
                location = _clean(unit.core_name)
                location_rank = 0 if location else 1
                secondary = ""
            else:
                location = ""
                location_rank = 0
                secondary = ""

            return (
                location_rank,
                _natural_key(location),
                _natural_key(secondary),
                _natural_key(unit_number),
            )

        units = sorted(units, key=sort_key)
        total = len(units)
        start = max(page - 1, 0) * per_page
        end = start + per_page
        return SimplePagination(units[start:end], page=page, per_page=per_page, total=total)


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
        works_summary = UnitService.get_unit_works_summary(unit_id)
        pending_reopen_requests = []
        if unit.company_id:
            pending_reopen_requests = WorkOrderReopenService.get_pending_for_unit(unit_id, unit.company_id)

        return {
            "unit": unit,
            "client": client,
            "company": company,
            "block": unit.block,
            "core": unit.core,
            "owner_entities": owners,
            "tenant_entities": tenants,
            "owners": [],
            "resident_entities": [],
            "residents": [],
            "ownership_history": ownership_history,
            "tenancy_history": tenancy_history,
            # stubs for later integrations:
            "invoices": [],
            "work_orders": works_summary["open_work_orders"],
            "closed_work_orders": works_summary["closed_work_orders"],
            "maintenance_requests": works_summary["open_maintenance_requests"],
            "works_summary": works_summary,
            "pending_reopen_requests": pending_reopen_requests,
            "documents": [],
            "child_units": unit.child_units if hasattr(unit, "child_units") else [],
        }

    # ------------------------------------------------------------
    # CREATION
    # ------------------------------------------------------------
    @staticmethod
    def create_unit(form, company_id: int) -> Unit:
        client_id = form.get("client_id")
        client = Client.query.filter_by(id=client_id, company_id=company_id).first()
        if not client:
            raise ValueError("Select a valid development before creating the unit.")

        unit = Unit(
            company_id=company_id,
            client_id=client.id,
            unit_label=form.get("unit_label"),
            unit_category=form.get("unit_category"),
            unit_type=form.get("unit_type"),
            unit_number=form.get("unit_number") or form.get("unit_label"),
            unit_name=form.get("unit_name") or form.get("unit_label"),
            block_name=form.get("block_name"),
            core_name=form.get("core_name"),
            area_name=form.get("area_name"),
            floor_number=form.get("floor_number"),
            entrance=form.get("entrance"),
            parking_label=form.get("parking_label"),
            storage_label=form.get("storage_label"),
            letting_agent_name=form.get("letting_agent_name"),
            letting_agent_phone=form.get("letting_agent_phone"),
            letting_agent_email=form.get("letting_agent_email"),
            letting_agent_address_line1=form.get("letting_agent_address_line1"),
            letting_agent_address_line2=form.get("letting_agent_address_line2"),
            letting_agent_city=form.get("letting_agent_city"),
            letting_agent_region=form.get("letting_agent_region"),
            letting_agent_postcode=form.get("letting_agent_postcode"),
            letting_agent_country=form.get("letting_agent_country"),
            letting_agent_notes=form.get("letting_agent_notes"),
            sale_status=form.get("sale_status") or None,
            conveyancing_status=form.get("conveyancing_status") or None,
            owner_portfolio_type=form.get("owner_portfolio_type") or None,
            owner_portfolio_name=form.get("owner_portfolio_name") or None,
            owner_portfolio_reference=form.get("owner_portfolio_reference") or None,
            owner_portfolio_notes=form.get("owner_portfolio_notes") or None,
            square_meters=form.get("square_meters") or None,
            parent_unit_id=form.get("parent_unit_id") or None,
            status=form.get("status") or "Active",
            is_common_area=bool(form.get("is_common_area")),
            service_charge_scheme=form.get("service_charge_scheme"),
            service_charge_percent=form.get("service_charge_percent") or None,
            service_charge_amount=form.get("service_charge_amount") or None,
            billing_frequency=form.get("billing_frequency"),
            financial_year_start=form.get("financial_year_start") or None,
            financial_year_end=form.get("financial_year_end") or None,
            notes=form.get("notes"),
            ai_summary=form.get("ai_summary") or None,
            gar_recommendations=form.get("gar_recommendations") or None,
            gar_feedback=form.get("gar_feedback") or None,
        )

        db.session.add(unit)
        db.session.flush()
        UnitService.sync_unit_relationships(unit, form, company_id=company_id)
        db.session.commit()
        return unit

    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------
    @staticmethod
    def update_unit(unit_id: int, form, company_id: int, can_edit_core_details: bool = False) -> bool:
        unit = Unit.query.filter_by(id=unit_id, company_id=company_id).first()
        if not unit:
            return False

        submitted_client_id = form.get("client_id")
        if submitted_client_id and str(submitted_client_id) != str(unit.client_id):
            raise ValueError("A unit cannot be moved to another development from this screen.")

        shared_fields = [
            "letting_agent_name", "letting_agent_phone", "letting_agent_email",
            "letting_agent_address_line1", "letting_agent_address_line2",
            "letting_agent_city", "letting_agent_region", "letting_agent_postcode",
            "letting_agent_country",
            "letting_agent_notes", "sale_status", "conveyancing_status", "status",
            "owner_portfolio_type", "owner_portfolio_name", "owner_portfolio_reference",
            "owner_portfolio_notes",
            "service_charge_scheme", "billing_frequency", "notes",
            "ai_summary", "gar_recommendations", "gar_feedback"
        ]
        core_fields = [
            "unit_label", "unit_category", "unit_type",
            "unit_number", "unit_name", "block_name", "core_name", "area_name",
            "floor_number", "entrance", "parking_label", "storage_label"
        ]
        editable_fields = shared_fields + (core_fields if can_edit_core_details else [])

        for field in editable_fields:
            setattr(unit, field, form.get(field))

        unit.is_common_area = bool(form.get("is_common_area"))

        # numeric fields
        if can_edit_core_details:
            unit.square_meters = form.get("square_meters") or None
            unit.parent_unit_id = form.get("parent_unit_id") or None
        unit.service_charge_percent = form.get("service_charge_percent") or None
        unit.service_charge_amount = form.get("service_charge_amount") or None

        # dates
        unit.financial_year_start = form.get("financial_year_start") or None
        unit.financial_year_end = form.get("financial_year_end") or None

        unit.occupancy_status = form.get("occupancy_status") or unit.occupancy_status or "unknown"
        unit.is_occupied = unit.occupancy_status in {"owner_occupied", "let"}

        UnitService.sync_unit_relationships(unit, form, company_id=company_id)

        db.session.commit()
        return True

    # ------------------------------------------------------------
    # OWNERSHIP / OCCUPANCY CAPTURE
    # ------------------------------------------------------------
    @staticmethod
    def relationship_form_context(unit: Unit) -> Dict[str, Any]:
        owner_link = UnitService._current_membership(unit.id, "owner")
        co_owner_link = UnitService._current_co_owner_membership(unit.id)
        tenant_link = UnitService._current_membership(unit.id, "tenant")

        return {
            "owner_link": owner_link,
            "owner_member": owner_link.member if owner_link else None,
            "co_owner_link": co_owner_link,
            "co_owner_member": co_owner_link.member if co_owner_link else None,
            "tenant_link": tenant_link,
            "tenant_member": tenant_link.member if tenant_link else None,
        }

    @staticmethod
    def sync_unit_relationships(unit: Unit, form, company_id: int) -> None:
        owner_member = None

        if _has_person_payload(form, "owner"):
            owner_link = UnitService._current_membership(unit.id, "owner")
            owner_member = UnitService._upsert_member_from_form(
                form=form,
                prefix="owner",
                company_id=company_id,
                client_id=unit.client_id,
                is_owner=True,
                existing_member=owner_link.member if owner_link else None,
            )
            db.session.flush()

            if owner_link is None:
                owner_link = UnitMembership(
                    unit_id=unit.id,
                    member_id=owner_member.id,
                    role="owner",
                    is_primary=True,
                    is_current=True,
                )
                db.session.add(owner_link)
            else:
                owner_link.member_id = owner_member.id

            owner_link.ownership_start_date = _parse_date(form.get("owner_ownership_start_date"))
            owner_link.ownership_end_date = _parse_date(form.get("owner_ownership_end_date"))
            owner_link.notes = _clean(form.get("owner_notes"))
            owner_link.is_current = owner_link.ownership_end_date is None
            owner_link.is_primary = True

        occupancy_status = form.get("occupancy_status") or unit.occupancy_status or "unknown"
        unit.occupancy_status = occupancy_status
        unit.is_occupied = occupancy_status in {"owner_occupied", "let"}

        if owner_member:
            owner_member.is_owner_occupier = occupancy_status == "owner_occupied"

        if _has_person_payload(form, "co_owner"):
            co_owner_link = UnitService._current_co_owner_membership(unit.id)
            co_owner_member = UnitService._upsert_member_from_form(
                form=form,
                prefix="co_owner",
                company_id=company_id,
                client_id=unit.client_id,
                is_owner=True,
                existing_member=co_owner_link.member if co_owner_link else None,
            )
            db.session.flush()

            if co_owner_link is None:
                co_owner_link = UnitMembership(
                    unit_id=unit.id,
                    member_id=co_owner_member.id,
                    role="owner",
                    is_primary=False,
                    is_current=True,
                )
                db.session.add(co_owner_link)
            else:
                co_owner_link.member_id = co_owner_member.id

            co_owner_link.ownership_start_date = _parse_date(form.get("co_owner_ownership_start_date"))
            co_owner_link.ownership_end_date = _parse_date(form.get("co_owner_ownership_end_date"))
            co_owner_link.notes = _clean(form.get("co_owner_notes"))
            co_owner_link.is_current = co_owner_link.ownership_end_date is None
            co_owner_link.is_primary = False

        tenant_link = UnitService._current_membership(unit.id, "tenant")
        if occupancy_status == "let" and _has_person_payload(form, "tenant"):
            tenant_member = UnitService._upsert_member_from_form(
                form=form,
                prefix="tenant",
                company_id=company_id,
                client_id=unit.client_id,
                is_owner=False,
                existing_member=tenant_link.member if tenant_link else None,
            )
            db.session.flush()

            if tenant_link is None:
                tenant_link = UnitMembership(
                    unit_id=unit.id,
                    member_id=tenant_member.id,
                    role="tenant",
                    is_primary=True,
                    is_current=True,
                )
                db.session.add(tenant_link)
            else:
                tenant_link.member_id = tenant_member.id

            tenant_link.tenancy_start_date = _parse_date(form.get("tenant_tenancy_start_date"))
            tenant_link.tenancy_end_date = _parse_date(form.get("tenant_tenancy_end_date"))
            tenant_link.notes = _clean(form.get("tenant_notes"))
            tenant_link.is_current = tenant_link.tenancy_end_date is None
            tenant_link.is_primary = True

        if occupancy_status == "let" and _has_person_payload(form, "additional_tenant"):
            additional_tenant_member = UnitService._upsert_member_from_form(
                form=form,
                prefix="additional_tenant",
                company_id=company_id,
                client_id=unit.client_id,
                is_owner=False,
            )
            db.session.flush()

            additional_tenant_link = UnitMembership(
                unit_id=unit.id,
                member_id=additional_tenant_member.id,
                role="tenant",
                is_primary=False,
                is_current=True,
                tenancy_start_date=_parse_date(form.get("additional_tenant_tenancy_start_date")),
                tenancy_end_date=_parse_date(form.get("additional_tenant_tenancy_end_date")),
                notes=_clean(form.get("additional_tenant_notes")),
            )
            additional_tenant_link.is_current = additional_tenant_link.tenancy_end_date is None
            db.session.add(additional_tenant_link)

        if occupancy_status != "let":
            current_tenant_links = UnitMembership.query.filter(
                UnitMembership.unit_id == unit.id,
                UnitMembership.role.in_(("tenant", "resident")),
                UnitMembership.is_current.is_(True),
            ).all()
            for current_tenant_link in current_tenant_links:
                current_tenant_link.is_current = False

    @staticmethod
    def _current_membership(unit_id: int, role: str) -> Optional[UnitMembership]:
        return (
            UnitMembership.query.filter_by(
                unit_id=unit_id,
                role=role,
                is_current=True,
            )
            .order_by(UnitMembership.is_primary.desc(), UnitMembership.id.desc())
            .first()
        )

    @staticmethod
    def _current_co_owner_membership(unit_id: int) -> Optional[UnitMembership]:
        return (
            UnitMembership.query.filter_by(
                unit_id=unit_id,
                role="owner",
                is_current=True,
                is_primary=False,
            )
            .order_by(UnitMembership.id.desc())
            .first()
        )

    @staticmethod
    def _upsert_member_from_form(
        form,
        prefix: str,
        company_id: int,
        client_id: int,
        is_owner: bool,
        existing_member: Optional[Member] = None,
    ) -> Member:
        member = existing_member or Member(company_id=company_id, client_id=client_id)
        member.company_id = company_id
        member.client_id = client_id
        member.is_owner = is_owner
        member.is_active = True

        for field in [
            "first_name",
            "last_name",
            "email",
            "phone",
            "alternate_phone",
            "postal_address_line1",
            "postal_address_line2",
            "postal_city",
            "postal_region",
            "postal_postcode",
            "postal_country",
            "preferred_contact_method",
        ]:
            setattr(member, field, _clean(form.get(f"{prefix}_{field}")))

        if existing_member is None:
            db.session.add(member)

        return member

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

    # ------------------------------------------------------------
    # WORKS / MAINTENANCE SNAPSHOT
    # ------------------------------------------------------------
    @staticmethod
    def get_unit_works_summary(unit_id: int) -> Dict[str, Any]:
        work_orders = (
            WorkOrder.query.filter(WorkOrder.unit_id == unit_id)
            .order_by(WorkOrder.created_at.desc())
            .all()
        )
        maintenance_requests = (
            MaintenanceRequest.query.filter(MaintenanceRequest.unit_id == unit_id)
            .order_by(MaintenanceRequest.created_at.desc())
            .all()
        )

        open_work_orders = [item for item in work_orders if _is_open_status(item.status)]
        closed_work_orders = [item for item in work_orders if not _is_open_status(item.status)]
        open_maintenance_requests = [
            item for item in maintenance_requests if _is_open_status(item.status)
        ]

        return {
            "open_work_orders": open_work_orders,
            "closed_work_orders": closed_work_orders,
            "open_maintenance_requests": open_maintenance_requests,
            "open_work_order_count": len(open_work_orders),
            "closed_work_order_count": len(closed_work_orders),
            "open_maintenance_request_count": len(open_maintenance_requests),
            "open_total": len(open_work_orders) + len(open_maintenance_requests),
            "total_work_orders": len(work_orders),
            "total_maintenance_requests": len(maintenance_requests),
        }

    @staticmethod
    def get_unit_work_order(unit_id: int, work_order_id: int, company_id: int) -> Optional[WorkOrder]:
        return (
            WorkOrder.query.join(Unit, WorkOrder.unit_id == Unit.id)
            .filter(
                WorkOrder.id == work_order_id,
                WorkOrder.unit_id == unit_id,
                Unit.company_id == company_id,
            )
            .first()
        )

    @staticmethod
    def reopen_work_order(unit_id: int, work_order_id: int, company_id: int) -> bool:
        work_order = UnitService.get_unit_work_order(unit_id, work_order_id, company_id)
        if not work_order:
            return False

        if _is_open_status(work_order.status):
            return True

        work_order.status = "Open"
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
        links = (
            UnitMembership.query.join(Member)
            .filter(
                UnitMembership.unit_id == unit_id,
                UnitMembership.role == "owner",
                UnitMembership.is_current.is_(True),
            )
            .order_by(UnitMembership.is_primary.desc(), UnitMembership.id.asc())
            .all()
        )
        return [{"member": link.member, "link": link} for link in links]

    # ------------------------------
    # CURRENT TENANTS
    # ------------------------------
    @staticmethod
    def get_current_tenants(unit_id: int) -> List[Dict[str, Any]]:
        links = (
            UnitMembership.query.join(Member)
            .filter(
                UnitMembership.unit_id == unit_id,
                UnitMembership.role.in_(("tenant", "resident")),
                UnitMembership.is_current.is_(True),
            )
            .order_by(UnitMembership.is_primary.desc(), UnitMembership.id.asc())
            .all()
        )
        return [{"member": link.member, "link": link} for link in links]

    # ------------------------------
    # FULL OWNERSHIP HISTORY
    # ------------------------------
    @staticmethod
    def get_ownership_history(unit_id: int) -> List[Dict[str, Any]]:
        links = (
            UnitMembership.query.join(Member)
            .filter(
                UnitMembership.unit_id == unit_id,
                UnitMembership.role == "owner",
            )
            .order_by(UnitMembership.ownership_start_date.asc(), UnitMembership.id.asc())
            .all()
        )
        return [{"member": link.member, "link": link} for link in links]

    # ------------------------------
    # FULL TENANCY HISTORY
    # ------------------------------
    @staticmethod
    def get_tenancy_history(unit_id: int) -> List[Dict[str, Any]]:
        links = (
            UnitMembership.query.join(Member)
            .filter(
                UnitMembership.unit_id == unit_id,
                UnitMembership.role.in_(("tenant", "resident")),
            )
            .order_by(UnitMembership.tenancy_start_date.asc(), UnitMembership.id.asc())
            .all()
        )
        return [{"member": link.member, "link": link} for link in links]

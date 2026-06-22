from datetime import date
from decimal import Decimal
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.extensions import db
from app.models.client.client import Client
from app.models.members.member import Member
from app.models.members.unit import Unit
from app.models.members.unit_membership import UnitMembership


CLIENT_NAME = "Matthew Lavery"


def upsert_member(company_id, client_id, payload, is_owner):
    member = Member.query.filter_by(company_id=company_id, client_id=client_id, email=payload["email"]).first()
    if not member:
        member = Member(company_id=company_id, client_id=client_id, email=payload["email"])
        db.session.add(member)

    member.first_name = payload["first_name"]
    member.last_name = payload["last_name"]
    member.phone = payload.get("phone")
    member.alternate_phone = payload.get("alternate_phone")
    member.preferred_contact_method = payload.get("preferred_contact_method", "email")
    member.postal_address_line1 = payload.get("address1")
    member.postal_address_line2 = payload.get("address2")
    member.postal_city = payload.get("city", "Dublin")
    member.postal_region = payload.get("region", "Dublin")
    member.postal_postcode = payload.get("postcode")
    member.postal_country = payload.get("country", "Ireland")
    member.is_owner = is_owner
    member.is_active = True
    member.is_owner_occupier = payload.get("is_owner_occupier", False)
    db.session.flush()
    return member


def upsert_link(unit, member, role, is_primary, start=None, end=None, notes=None):
    link = UnitMembership.query.filter_by(unit_id=unit.id, member_id=member.id, role=role).first()
    if not link:
        link = UnitMembership(unit_id=unit.id, member_id=member.id, role=role)
        db.session.add(link)

    link.is_primary = is_primary
    link.is_current = end is None
    link.notes = notes
    if role == "owner":
        link.ownership_start_date = start
        link.ownership_end_date = end
    else:
        link.tenancy_start_date = start
        link.tenancy_end_date = end
    return link


def clear_test_relationships(unit):
    UnitMembership.query.filter_by(unit_id=unit.id).delete(synchronize_session=False)


def seed():
    app = create_app()
    with app.app_context():
        client = Client.query.filter(Client.name.ilike(CLIENT_NAME)).first()
        if not client:
            raise RuntimeError(f"Client not found: {CLIENT_NAME}")

        client.property_name = "Matthew Lavery Test Development"
        client.address_line1 = "53A Rathgar Avenue"
        client.city = "Dublin"
        client.region = "Dublin"
        client.country = "Ireland"
        client.postal_code = "D06K5K2"
        client.number_of_units = 15
        client.units_apartments = 12
        client.units_commercial = 2
        client.units_other = 1
        client.number_of_blocks = 3
        client.block_names = "Glenasmole, Dodder View, Rathgar Hall"
        client.cores_per_block = "Glenasmole: Core 1, Core 2; Dodder View: Core 1; Rathgar Hall: Core A"
        client.is_gar_monitored = True
        client.ai_governance_score = 84
        client.ai_health_index = 78
        client.ai_compliance_index = 91
        client.ai_advice_summary = "Test development seeded for unit, ownership, occupancy and GAR AI workflow review."

        company_id = client.company_id
        units = [
            {
                "number": "1", "label": "Apartment Glenasmole 1", "block": "Glenasmole", "core": "Core 1",
                "floor": "Ground", "parking": "CP-01", "storage": "ST-01", "occupancy": "owner_occupied",
                "owner": ("Aisling", "Byrne", "aisling.byrne@example.com", "0867001101"),
                "co_owner": ("Conor", "Byrne", "conor.byrne@example.com", "0867001102"),
                "service": "Standard Schedule", "amount": "1850.00",
            },
            {
                "number": "2", "label": "Apartment Glenasmole 2", "block": "Glenasmole", "core": "Core 1",
                "floor": "Ground", "parking": "CP-02", "occupancy": "let",
                "owner": ("Niamh", "Walsh", "niamh.walsh@example.com", "0867001103"),
                "tenants": [("Sean", "Murphy", "sean.murphy@example.com", "0877001104"), ("Leah", "Kelly", "leah.kelly@example.com", "0877001105")],
                "letting": ("Bohan Hyland", "014913000", "info@bohanhyland.ie", "14 Rathgar Road", "Dublin 6"),
                "service": "Standard Schedule", "amount": "1925.50",
            },
            {
                "number": "3", "label": "Apartment Glenasmole 3", "block": "Glenasmole", "core": "Core 1",
                "floor": "First", "parking": "CP-03", "occupancy": "vacant",
                "owner": ("Declan", "O'Neill", "declan.oneill@example.com", "0867001106"),
                "sale_status": "for_sale", "conveyancing_status": "information_requested",
                "service": "Standard Schedule", "amount": "1810.00",
            },
            {
                "number": "4", "label": "Apartment Glenasmole 4", "block": "Glenasmole", "core": "Core 2",
                "floor": "First", "parking": "CP-04", "occupancy": "let",
                "owner": ("Orla", "Lavery", "laveryorla@gmail.com", "014913000"),
                "tenants": [("Eoin", "Doyle", "eoin.doyle@example.com", "0877001107")],
                "letting": ("Ray Cooke Lettings", "014030720", "lettings@raycooke.ie", "Unit 7 Village Green", "Dublin 24"),
                "service": "Standard Schedule", "amount": "1960.00",
            },
            {
                "number": "5", "label": "Apartment Glenasmole 5", "block": "Glenasmole", "core": "Core 2",
                "floor": "Second", "parking": "CP-05", "occupancy": "owner_occupied",
                "owner": ("Gus", "Silva", "gus.silva@example.com", "0861282677"),
                "co_owner": ("Matthew", "Lavery", "laverymatthew85@gmail.com", "014913000"),
                "service": "Standard Schedule", "amount": "2040.00",
            },
            {
                "number": "6", "label": "Apartment Dodder View 6", "block": "Dodder View", "core": "Core 1",
                "floor": "Ground", "parking": "CP-06", "occupancy": "let",
                "portfolio": ("social_housing", "Dublin Housing Partnership", "DHP-ML-006"),
                "owner": ("Dublin", "Housing Partnership", "housing@example.org", "018880001"),
                "tenants": [("Marta", "Nowak", "marta.nowak@example.com", "0877001108"), ("Piotr", "Nowak", "piotr.nowak@example.com", "0877001109")],
                "service": "Standard Schedule", "amount": "1885.00",
            },
            {
                "number": "7", "label": "Apartment Dodder View 7", "block": "Dodder View", "core": "Core 1",
                "floor": "First", "parking": "CP-07", "occupancy": "owner_occupied",
                "owner": ("Sarah", "Kavanagh", "sarah.kavanagh@example.com", "0867001110"),
                "service": "Standard Schedule", "amount": "1995.00",
            },
            {
                "number": "8", "label": "Apartment Dodder View 8", "block": "Dodder View", "core": "Core 1",
                "floor": "Second", "parking": "CP-08", "occupancy": "let",
                "portfolio": ("multi_property_owner", "Patrick Nolan Portfolio", "PN-03"),
                "owner": ("Patrick", "Nolan", "patrick.nolan@example.com", "0867001111"),
                "tenants": [("Hannah", "Lee", "hannah.lee@example.com", "0877001112")],
                "letting": ("Owen Reilly", "016770010", "management@owenreilly.ie", "41 Forbes Quay", "Dublin 2"),
                "service": "Standard Schedule", "amount": "2025.75",
            },
            {
                "number": "9", "label": "Apartment Rathgar Hall 9", "block": "Rathgar Hall", "core": "Core A",
                "floor": "Ground", "parking": "CP-09", "occupancy": "vacant",
                "owner": ("Maeve", "Ryan", "maeve.ryan@example.com", "0867001113"),
                "service": "Standard Schedule", "amount": "1765.00",
            },
            {
                "number": "10", "label": "Apartment Rathgar Hall 10", "block": "Rathgar Hall", "core": "Core A",
                "floor": "First", "parking": "CP-10", "occupancy": "owner_occupied",
                "owner": ("Brian", "Fitzgerald", "brian.fitzgerald@example.com", "0867001114"),
                "co_owner": ("Aoife", "Fitzgerald", "aoife.fitzgerald@example.com", "0867001115"),
                "service": "Standard Schedule", "amount": "2150.00",
            },
            {
                "number": "11", "label": "Penthouse Rathgar Hall 11", "block": "Rathgar Hall", "core": "Core A",
                "floor": "Third", "parking": "CP-11", "storage": "ST-11", "occupancy": "owner_occupied",
                "owner": ("Elaine", "McCarthy", "elaine.mccarthy@example.com", "0867001116"),
                "sale_status": "sale_agreed", "conveyancing_status": "queries_open",
                "service": "Standard Schedule", "amount": "2850.00",
            },
            {
                "number": "12", "label": "Apartment Rathgar Hall 12", "block": "Rathgar Hall", "core": "Core A",
                "floor": "Third", "parking": "CP-12", "occupancy": "let",
                "owner": ("Kevin", "Dunne", "kevin.dunne@example.com", "0867001117"),
                "tenants": [("Tom", "Brennan", "tom.brennan@example.com", "0877001118"), ("Amira", "Hassan", "amira.hassan@example.com", "0877001119")],
                "letting": ("Hooke & MacDonald", "016318402", "lettings@hookemacdonald.ie", "118 Lower Baggot Street", "Dublin 2"),
                "service": "Standard Schedule", "amount": "2210.25",
            },
            {
                "number": "C-001", "label": "Commercial Unit C-001", "block": "Glenasmole", "core": "Street Front",
                "category": "Commercial", "type": "Commercial", "floor": "Ground", "occupancy": "let",
                "portfolio": ("investment_company", "Oakline Property Investments Ltd", "OPI-C001"),
                "owner": ("Oakline", "Investments", "accounts@oakline.example.com", "018881212"),
                "tenants": [("Green Bean", "Cafe", "manager@greenbean.example.com", "014441212")],
                "service": "Commercial Schedule", "amount": "4250.00",
            },
            {
                "number": "C-002", "label": "Commercial Unit C-002", "block": "Dodder View", "core": "Street Front",
                "category": "Commercial", "type": "Commercial", "floor": "Ground", "occupancy": "vacant",
                "owner": ("Rathgar", "Pharmacy Ltd", "directors@rathgarpharmacy.example.com", "014440020"),
                "sale_status": "preparing_for_sale",
                "service": "Commercial Schedule", "amount": "3980.00",
            },
            {
                "number": "S-001", "label": "Storage Suite S-001", "block": "Rathgar Hall", "core": "Basement",
                "category": "Storage / Locker", "type": "Other", "floor": "Basement", "occupancy": "unknown",
                "owner": ("Management", "Company", "admin@matthewlavery-test.example.com", "014913000"),
                "service": "No Service Charge", "amount": "0.00",
            },
        ]

        seed_numbers = {data["number"] for data in units}
        extras = Unit.query.filter(Unit.client_id == client.id, ~Unit.unit_number.in_(seed_numbers)).all()
        for extra in extras:
            extra.is_active = False
            extra.status = "Inactive"
            extra.notes = "Inactive legacy/test unit hidden from the Matthew Lavery 15-unit seed directory."

        for index, data in enumerate(units, start=1):
            unit = Unit.query.filter_by(client_id=client.id, unit_number=data["number"]).first()
            if not unit:
                unit = Unit(client_id=client.id, company_id=company_id, unit_number=data["number"])
                db.session.add(unit)

            unit.company_id = company_id
            unit.unit_label = data["label"]
            unit.unit_name = data["label"]
            unit.unit_type = data.get("type", "Apartment")
            unit.unit_category = data.get("category", "Residential")
            unit.block_name = data["block"]
            unit.core_name = data["core"]
            unit.floor_number = data["floor"]
            unit.parking_label = data.get("parking")
            unit.storage_label = data.get("storage")
            unit.occupancy_status = data["occupancy"]
            unit.status = "Active"
            unit.is_active = True
            unit.is_occupied = data["occupancy"] in {"owner_occupied", "let"}
            unit.service_charge_scheme = data["service"]
            unit.service_charge_amount = Decimal(data["amount"])
            unit.billing_frequency = "Annual"
            unit.financial_year_start = date(2026, 1, 1)
            unit.financial_year_end = date(2026, 12, 31)
            unit.sale_status = data.get("sale_status")
            unit.conveyancing_status = data.get("conveyancing_status")
            unit.notes = f"Seeded test data row {index} for Matthew Lavery Owners Directory."
            unit.ai_summary = f"GAR AI test context for {data['label']}: {data['occupancy'].replace('_', ' ')} unit in {data['block']}."
            unit.gar_recommendations = "Review ownership, occupancy and service charge visibility in the test dashboard."
            unit.gar_feedback = "Seeded for UI testing."

            if data.get("portfolio"):
                unit.owner_portfolio_type, unit.owner_portfolio_name, unit.owner_portfolio_reference = data["portfolio"]
                unit.owner_portfolio_notes = "Portfolio ownership should show linked units to the owner body/company in Members Logix without exposing owner-only details to tenants."
            else:
                unit.owner_portfolio_type = None
                unit.owner_portfolio_name = None
                unit.owner_portfolio_reference = None
                unit.owner_portfolio_notes = None

            if data.get("letting"):
                name, phone, email, address, city = data["letting"]
                unit.letting_agent_name = name
                unit.letting_agent_phone = phone
                unit.letting_agent_email = email
                unit.letting_agent_address_line1 = address
                unit.letting_agent_city = city
                unit.letting_agent_country = "Ireland"
                unit.letting_agent_notes = "Seeded letting agent contact for test workflow."
            else:
                unit.letting_agent_name = None
                unit.letting_agent_phone = None
                unit.letting_agent_email = None
                unit.letting_agent_address_line1 = None
                unit.letting_agent_city = None
                unit.letting_agent_country = None
                unit.letting_agent_notes = None

            db.session.flush()
            clear_test_relationships(unit)

            owner_first, owner_last, owner_email, owner_phone = data["owner"]
            owner = upsert_member(company_id, client.id, {
                "first_name": owner_first,
                "last_name": owner_last,
                "email": owner_email,
                "phone": owner_phone,
                "address1": f"{data['number']} {data['block']}",
                "city": "Dublin",
                "postcode": "D06 TEST",
                "is_owner_occupier": data["occupancy"] == "owner_occupied",
            }, is_owner=True)
            upsert_link(unit, owner, "owner", True, date(2023, 1, min(index, 28)), notes="Seeded primary owner.")

            if data.get("co_owner"):
                co_first, co_last, co_email, co_phone = data["co_owner"]
                co_owner = upsert_member(company_id, client.id, {
                    "first_name": co_first,
                    "last_name": co_last,
                    "email": co_email,
                    "phone": co_phone,
                    "address1": f"{data['number']} {data['block']}",
                    "city": "Dublin",
                    "postcode": "D06 TEST",
                }, is_owner=True)
                upsert_link(unit, co_owner, "owner", False, date(2023, 2, min(index, 28)), notes="Seeded co-owner.")

            for tenant_index, tenant_data in enumerate(data.get("tenants", []), start=1):
                tenant_first, tenant_last, tenant_email, tenant_phone = tenant_data
                tenant = upsert_member(company_id, client.id, {
                    "first_name": tenant_first,
                    "last_name": tenant_last,
                    "email": tenant_email,
                    "phone": tenant_phone,
                    "address1": f"{data['number']} {data['block']}",
                    "city": "Dublin",
                    "postcode": "D06 TEST",
                }, is_owner=False)
                upsert_link(
                    unit,
                    tenant,
                    "tenant",
                    tenant_index == 1,
                    date(2026, min(tenant_index + 1, 12), min(index, 28)),
                    notes="Seeded current tenant." if tenant_index == 1 else "Seeded additional current tenant.",
                )

        db.session.commit()
        print(f"Seeded {len(units)} Matthew Lavery units with owners, co-owners, tenants, letting agents and portfolio data.")


if __name__ == "__main__":
    seed()

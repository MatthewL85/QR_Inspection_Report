from datetime import datetime
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.extensions import db
from app.models.client.client import Client
from app.models.client.key_info import ClientKeyInfo
from app.models.core.user import User


CLIENT_NAME = "Matthew Lavery"


SECTIONS = [
    {
        "title": "Site Access and Entry",
        "content": """Primary entrance: Rathgar Avenue pedestrian gate.
Vehicle access: basement ramp beside Glenasmole block.
Pedestrian gate test code: 2468A.
Vehicle gate test code: 1357B.
Key safe location: inside management store beside Rathgar Hall basement entrance.
Key safe test code: 9080.
Access rule: contractors must call the site contact before attending occupied units and must sign in with the management company for common area works.
Out of hours: emergency attendance only unless authorised by the Property Manager.""",
        "tags": ["access", "gate", "keys", "contractor"],
        "rank": 10,
        "completeness": 0.92,
        "risk": 0.22,
    },
    {
        "title": "Emergency Contacts and Escalation",
        "content": """Managing agent emergency line: 01 491 3000.
Property Manager: Matthew Lavery, matthew@logix.com.
Assistant Manager cover: Review Assistant, assistant@logixpm.test.
Fire or life safety emergency: call emergency services first, then notify the managing agent.
Water leak escalation: isolate local stop valve if safe, notify impacted units, then route to approved plumbing contractor.
Electrical emergency: isolate affected area if safe and route to electrical contractor only.
GAR note: emergency records should link back to Works Logix work orders and contractor attendance history.""",
        "tags": ["emergency", "contacts", "escalation", "gar"],
        "rank": 20,
        "completeness": 0.9,
        "risk": 0.35,
    },
    {
        "title": "Blocks, Cores and Common Areas",
        "content": """Development blocks: Glenasmole, Dodder View, Rathgar Hall.
Glenasmole cores: Core 1 and Core 2.
Dodder View cores: Core 1 and Street Front.
Rathgar Hall cores: Core A and Basement.
Common areas include entrances, corridors, stairwells, basement car park, bin store, meter room, plant room and landscaped courtyard.
Unit references should be recorded as block / core / unit number where available, for example Glenasmole / Core 1 / 4.""",
        "tags": ["structure", "blocks", "cores", "units"],
        "rank": 30,
        "completeness": 0.88,
        "risk": 0.12,
    },
    {
        "title": "Utilities, Plant and Isolation",
        "content": """Main electrical intake: Rathgar Hall basement electrical room.
Water stop valve: basement plant room, labelled ML-WATER-MAIN.
Gas isolation: external cabinet at rear service lane, labelled ML-GAS-01.
Lift plant: Rathgar Hall roof access hatch, authorised lift contractor only.
Door entry controller: Glenasmole comms cupboard.
CCTV recorder: management store, network cabinet shelf 2.
Contractors must record any isolation, outage or reinstatement in Works Logix before leaving site.""",
        "tags": ["utilities", "plant", "isolation", "safety"],
        "rank": 40,
        "completeness": 0.86,
        "risk": 0.42,
    },
    {
        "title": "Fire Safety and Life Safety",
        "content": """Fire alarm panel: Rathgar Hall main lobby.
Emergency lighting test point: basement plant room.
Fire exits: each block stairwell exits to the landscaped courtyard and Rathgar Avenue.
Fire doors must not be wedged open.
Hot works require written authorisation and evidence of contractor insurance.
Any life safety defect must be logged as urgent in Works Logix and flagged to GAR for compliance visibility.
Inspection records and certificates should be stored in Documents when Finance Logix and GAR document extraction are enabled.""",
        "tags": ["fire", "life safety", "compliance", "documents"],
        "rank": 50,
        "completeness": 0.84,
        "risk": 0.5,
    },
    {
        "title": "Waste, Cleaning and Pest Control",
        "content": """Bin store: basement level beside car park exit.
Collection days: general waste Tuesday, recycling Friday.
Cleaning frequency: common halls twice weekly, glass and high-touch points weekly.
Spillage response: isolate area, photograph issue, clean and log the action in Works Logix.
Pest control bait points: basement bin store and rear service lane.
Residents should not leave bulky waste in the bin store without prior written approval.""",
        "tags": ["waste", "cleaning", "pest control", "works"],
        "rank": 60,
        "completeness": 0.82,
        "risk": 0.25,
    },
    {
        "title": "Parking, Deliveries and Site Restrictions",
        "content": """Visitor parking: two marked visitor bays at basement entrance.
Contractor parking: loading bay only, maximum 30 minutes unless authorised.
No parking in front of the vehicle gate or fire access route.
Deliveries: contractors should use Rathgar Avenue entrance and avoid blocking resident access.
Noise-sensitive hours: avoid noisy works before 08:00 or after 18:00 Monday to Friday, and before 10:00 on Saturdays.
Weekend works require prior approval from the managing agent.""",
        "tags": ["parking", "deliveries", "restrictions"],
        "rank": 70,
        "completeness": 0.8,
        "risk": 0.2,
    },
    {
        "title": "Approved Contractor Rules",
        "content": """Contractors must review the job docket before attendance.
Contractors must upload before and after photos for any repair where evidence is available.
Progress updates should be visible to management by default; completion updates should be visible to all parties unless restricted for a valid reason.
Materials used and private labour notes remain contractor-only.
Any access failure, resident no-show or safety issue must be recorded on the job docket on the same day.
Completed works must be submitted for PM/Admin review before the work order can move to invoice-ready.""",
        "tags": ["contractor", "job docket", "evidence", "invoicing"],
        "rank": 80,
        "completeness": 0.88,
        "risk": 0.18,
    },
]


def _summary(content: str) -> str:
    text = " ".join((content or "").split())
    return text[:180] + ("..." if len(text) > 180 else "")


def _approver_id():
    user = (
        User.query.filter(User.email == "owner@example.com").first()
        or User.query.filter(User.role.in_(["Super Admin", "Admin"])).first()
        or User.query.first()
    )
    return user.id if user else None


def seed():
    app = create_app()
    with app.app_context():
        client = Client.query.filter(Client.name.ilike(CLIENT_NAME)).first()
        if not client:
            raise RuntimeError(f"Client not found: {CLIENT_NAME}")

        approver_id = _approver_id()
        created = 0
        updated = 0
        now = datetime.utcnow()

        for payload in SECTIONS:
            section = ClientKeyInfo.query.filter_by(
                client_id=client.id,
                title=payload["title"],
            ).first()
            if not section:
                section = ClientKeyInfo(client_id=client.id, title=payload["title"])
                db.session.add(section)
                created += 1
            else:
                updated += 1

            content = payload["content"].strip()
            section.content = content
            section.status = "active"
            section.approved_by_id = approver_id
            section.approved_at = section.approved_at or now
            section.last_submitted_by_id = approver_id
            section.ai_parsed_text = content
            section.ai_parsed_summary = _summary(content)
            section.ai_extracted_data = {
                "source": "seed_matthew_lavery_key_site_info",
                "section": payload["title"],
                "client": CLIENT_NAME,
                "operational_use": ["Works Logix", "Contractor Logix", "Members Logix", "GAR"],
            }
            section.ai_tags = ["key-site-info", *payload["tags"]]
            section.ai_redaction_hints = {
                "contains_test_access_codes": "true" if "code" in content.lower() else "false",
                "do_not_email_publicly": "true",
            }
            section.ai_visibility_flags = {
                "share_in_dash_tiles": True,
                "works_logix_ready": True,
                "contractor_logix_ready": True,
                "gar_query_ready": True,
            }
            section.ai_scorecard = {
                "completeness": payload["completeness"],
                "risk": payload["risk"],
                "seeded_test_record": True,
            }
            section.ai_rank = payload["rank"]

        db.session.commit()
        print(
            f"Seeded Matthew Lavery key site info: {created} created, {updated} updated, "
            f"{len(SECTIONS)} active sections."
        )


if __name__ == "__main__":
    seed()

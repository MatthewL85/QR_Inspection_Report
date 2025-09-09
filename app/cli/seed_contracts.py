from __future__ import annotations

import json
import click
from datetime import date

from app.extensions import db
from app.models.contracts import ContractTemplate, ContractTemplateVersion


HTML_TEMPLATE_PSRA_FULL = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Property Services Agreement — {{ data.client.display_name or contract.client.name }}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/pdf.css') }}">
  <style>
    :root { --accent: {{ (data.branding.primary_hex or '#2196F3') if data.branding else '#2196F3' }}; }
    .accent{border-left:4px solid var(--accent);padding-left:8px}
    .kv th{width:28%;text-align:left}
    .muted{color:#666}
    .small{font-size:10pt}
  </style>
</head>
<body>

  <h1 class="accent">Property Services Agreement</h1>
  <p class="muted small">PSRA / S43 Form D — 07 October 2022</p>

  <!-- 1. Parties -->
  <h2>1. Parties to the Agreement</h2>
  <table class="kv">
    <tr><th>Client (OMC)</th><td>{{ data.client.display_name or contract.client.name }}</td></tr>
    <tr><th>Client Address</th><td>{{ data.client.postal_address or contract.client.address or '' }}</td></tr>
    {% if data.client.authorised %}
      <tr><th>Authorised Person</th><td>{{ data.client.authorised.name }} · {{ data.client.authorised.role or '' }} · {{ data.client.authorised.contact or '' }}</td></tr>
    {% endif %}
    <tr><th>Agent Legal Name</th><td>{{ data.agent.legal_name }}</td></tr>
    <tr><th>Trading As</th><td>{{ data.agent.trade_name or '—' }}</td></tr>
    <tr><th>Business Address</th><td>{{ data.agent.address }}</td></tr>
    <tr><th>PSRA Licence</th><td>{{ data.agent.psra_license }}</td></tr>
    <tr><th>Contact</th><td>{{ data.agent.phone }} · {{ data.agent.email }} · {{ data.agent.website }}</td></tr>
  </table>

  <!-- 2. Licence (declarative) -->
  <h2>2. Licence</h2>
  <p class="small">The Agent confirms they hold a current licence issued by the PSRA under the Property Services (Regulation) Act 2011.</p>

  <!-- 3. Services scope -->
  <h2>3. Property Services to be Provided</h2>
  <p class="small">The Client appoints the Agent for the duration of the Agreement to provide the services set out in Schedule II in relation to the Development in Schedule I.</p>

  <!-- 4. Duration -->
  <h2>4. Duration of Agreement</h2>
  <table class="kv">
    <tr><th>Start</th><td>{{ (data.term.start or contract.start_date)|default('', true) }}</td></tr>
    <tr><th>End</th><td>{{ (data.term.end or contract.end_date)|default('', true) }}</td></tr>
    <tr><th>Cooling Off</th><td>{{ 'Yes' if data.term.cooling_off else 'No' }}</td></tr>
  </table>

  <!-- 5. Obligations (condensed flags) -->
  <h2>5. Obligations of the Agent</h2>
  <p class="small">The Agent will act diligently, competently and in the Client’s best interests, and confirms no conflict of interest exists.</p>
  <h2>6. Obligations of the Client</h2>
  <p class="small">The Client confirms ownership/authority, disclosure of material matters, and maintenance of adequate insurances.</p>

  <!-- 7. Fees -->
  <h2>7. Fees, Outlays & Invoicing</h2>
  <table class="kv">
    <tr><th>Base Fee (ex VAT)</th><td>{{ contract.currency }} {{ '%.2f'|format(data.fees.base_ex_vat|default(0.0)) }}</td></tr>
    <tr><th>VAT %</th><td>{{ data.fees.vat_rate|default(23) }}</td></tr>
    <tr><th>Review</th><td>{{ data.fees.review or '3% annually in October' }}</td></tr>
    <tr><th>Invoicing</th>
        <td>{{ (data.fees.invoice.frequency ~ ', ' ~ data.fees.invoice.method ~ ', ' ~ (data.fees.invoice.due_days|string) ~ ' days')
               if data.fees and data.fees.invoice else 'Monthly, Standing Order, 30 days' }}</td></tr>
  </table>
  {% if data.fees and data.fees.additional %}
    <h3>Additional Charges</h3>
    <table>
      <thead><tr><th>Service</th><th class="text-right">Amount (ex VAT)</th></tr></thead>
      <tbody>
      {% for row in data.fees.additional %}
        <tr>
          <td>{{ row.label }}</td>
          <td class="text-right">{{ contract.currency }} {{ '%.2f'|format(row.amount|default(0.0)) }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  {% endif %}

  <!-- 8–12 condensed legal boilerplate shown as flags -->
  <h2>8–12. Legal & Compliance (Summary)</h2>
  <ul class="small">
    <li>Delegation/Procurement per Schedule II Part II; invoices paid within approved limits.</li>
    <li>Termination: {{ data.termination.notice_weeks or 12 }} weeks’ notice; material breach and statutory events apply.</li>
    <li>Client Account Banking: see Section 10 / Schedule data.</li>
    <li>Conflicts/Inducements prohibited; AML reporting obligations observed.</li>
    <li>PI Insurance: {{ data.insurance.pi_insurer }} · Policy {{ data.insurance.policy }}</li>
  </ul>

  <!-- 9–12 Banking / Insurance detail -->
  <h2>Banking & Client Money</h2>
  <table class="kv">
    <tr><th>Bank</th><td>{{ data.banking.name }}</td></tr>
    <tr><th>BIC</th><td>{{ data.banking.bic }}</td></tr>
    <tr><th>Branch</th><td>{{ data.banking.address }}</td></tr>
    <tr><th>Interest Policy</th><td>{{ data.banking.interest_policy or 'As per Client Moneys Regulations' }}</td></tr>
  </table>

  <div class="page-break"></div>

  <!-- SCHEDULE I: Development -->
  <h2>SCHEDULE I — Development</h2>
  <table class="kv">
    <tr><th>Name</th><td>{{ data.development.name }}</td></tr>
    <tr><th>Address</th><td>{{ data.development.address }}</td></tr>
    <tr><th>Folio</th><td>{{ data.development.folio or '—' }}</td></tr>
    <tr><th>Residential Units</th><td>{{ data.development.meta.res_units or '—' }}</td></tr>
    <tr><th>Commercial Units</th><td>{{ data.development.meta.com_units or '—' }}</td></tr>
    <tr><th>Blocks / Floors</th><td>{{ data.development.meta.blocks or '—' }} / {{ data.development.meta.floors or '—' }}</td></tr>
  </table>
  {% if data.development.meta.ancillary %}
    <p><em>Ancillary:</em> {{ data.development.meta.ancillary | join(', ') }}</p>
  {% endif %}

  <!-- SCHEDULE II: Services -->
  <h2>SCHEDULE II — Particulars of Services</h2>

  <h3>A. Accounting Services</h3>
  {% if data.schedule_ii.part_i.accounting %}
    <ul class="small">
      {% for item in data.schedule_ii.part_i.accounting %}<li>{{ item }}</li>{% endfor %}
    </ul>
  {% else %}<p class="small muted">—</p>{% endif %}

  <h3>B. Corporate Services</h3>
  {% if data.schedule_ii.part_i.corporate %}
    <ul class="small">
      {% for item in data.schedule_ii.part_i.corporate %}<li>{{ item }}</li>{% endfor %}
    </ul>
  {% else %}<p class="small muted">—</p>{% endif %}

  <h3>C. Insurance Management</h3>
  {% if data.schedule_ii.part_i.insurance_mgmt %}
    <ul class="small">
      {% for item in data.schedule_ii.part_i.insurance_mgmt %}<li>{{ item }}</li>{% endfor %}
    </ul>
  {% else %}<p class="small muted">—</p>{% endif %}

  <h3>D. Estate Management</h3>
  {% if data.schedule_ii.part_i.estate_mgmt %}
    <ul class="small">
      {% for item in data.schedule_ii.part_i.estate_mgmt %}<li>{{ item }}</li>{% endfor %}
    </ul>
  {% else %}<p class="small muted">—</p>{% endif %}

  <h3>Part II — Procurement on behalf of Client</h3>
  {% if data.schedule_ii.part_ii %}
    <ul class="small">{% for item in data.schedule_ii.part_ii %}<li>{{ item }}</li>{% endfor %}</ul>
  {% else %}<p class="small muted">—</p>{% endif %}

  <h3>Part III — Out-of-hours Emergency</h3>
  <table class="kv">
    <tr><th>Provider</th><td>{{ data.emergency.provider }}</td></tr>
    <tr><th>Contact</th><td>{{ data.emergency.phone }} · {{ data.emergency.email }}</td></tr>
    <tr><th>Annual Fee (ex VAT)</th><td>{{ contract.currency }} {{ '%.2f'|format(data.emergency.annual_fee_ex_vat|default(0.0)) }}</td></tr>
    {% if data.schedule_ii.part_iii and data.schedule_ii.part_iii.notes %}
      <tr><th>Notes</th><td>{{ data.schedule_ii.part_iii.notes }}</td></tr>
    {% endif %}
  </table>

  <h3>Part IV — Additional Services (agreed in advance)</h3>
  {% if data.schedule_ii.part_iv %}
    <table>
      <thead><tr><th>Service</th><th class="text-right">Fee (ex VAT)</th></tr></thead>
      <tbody>
        {% for row in data.schedule_ii.part_iv %}
          <tr>
            <td>{{ row.label }}</td>
            <td class="text-right">
              {% if row.amount is defined %}{{ contract.currency }} {{ '%.2f'|format(row.amount|default(0.0)) }}{% else %}TBA{% endif %}
            </td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  {% else %}<p class="small muted">—</p>{% endif %}

  <div class="page-break"></div>

  <!-- SCHEDULE III: Records -->
  <h2>SCHEDULE III — Records to be kept by Agent</h2>
  {% if data.records_schedule_iii %}
    <ul class="small">{% for line in data.records_schedule_iii %}<li>{{ line }}</li>{% endfor %}</ul>
  {% else %}<p class="small muted">—</p>{% endif %}

  <!-- Signatures -->
  <h2>Signatures</h2>
  <table>
    <tbody>
      <tr>
        <td style="width:50%; padding-right:20px;">
          <div class="signature-line"></div>
          <div class="signature-label">Agent Signature</div>
          <p class="muted small">
            {{ data.signatures.agent.name }} · {{ data.signatures.agent.role }} · Licence {{ data.signatures.agent.licence_no }}
          </p>
          <p class="small">Date: {{ data.signatures.agent.date or '' }}</p>
        </td>
        <td style="width:50%; padding-left:20px;">
          <div class="signature-line"></div>
          <div class="signature-label">Client Signature</div>
          {% if data.signatures.client and data.signatures.client|length > 0 %}
            <p class="muted small">
              {{ data.signatures.client[0].name }} · {{ data.signatures.client[0].role or '' }}
            </p>
            <p class="small">Date: {{ data.signatures.client[0].date or '' }}</p>
          {% else %}
            <p class="muted small">Name: ____________________</p>
            <p class="small">Date: ____________________</p>
          {% endif %}
        </td>
      </tr>
    </tbody>
  </table>

</body>
</html>
"""

FORM_SCHEMA_PSRA_FULL = {
    "sections": [
        # Parties
        {"key": "client", "title": "Client (OMC)",
         "fields": [
             {"path": "client.display_name", "label": "Display Name", "type": "text", "required": True},
             {"path": "client.postal_address", "label": "Postal Address", "type": "textarea"},
             {"path": "client.authorised.name", "label": "Authorised Person Name", "type": "text"},
             {"path": "client.authorised.role", "label": "Authorised Role", "type": "text"},
             {"path": "client.authorised.contact", "label": "Authorised Contact Details", "type": "textarea"},
         ]},
        {"key": "agent", "title": "Agent Details",
         "fields": [
             {"path": "agent.legal_name", "label": "Agent Legal Name", "type": "text", "required": True},
             {"path": "agent.trade_name", "label": "Trading As", "type": "text"},
             {"path": "agent.psra_license", "label": "PSRA Licence", "type": "text", "required": True},
             {"path": "agent.address", "label": "Business Address", "type": "textarea", "required": True},
             {"path": "agent.phone", "label": "Phone", "type": "text"},
             {"path": "agent.email", "label": "Email", "type": "email"},
             {"path": "agent.website", "label": "Website", "type": "text"},
         ]},
        # Term & fees
        {"key": "term", "title": "Term",
         "fields": [
             {"path": "term.start", "label": "Start Date", "type": "date", "required": True},
             {"path": "term.end", "label": "End Date", "type": "date", "required": True},
             {"path": "term.cooling_off", "label": "Cooling Off Applies", "type": "checkbox"},
         ]},
        {"key": "fees", "title": "Fees & Invoicing",
         "fields": [
             {"path": "fees.base_ex_vat", "label": "Base Fee (ex VAT)", "type": "money", "required": True},
             {"path": "fees.vat_rate", "label": "VAT %", "type": "number", "min": 0, "max": 100},
             {"path": "fees.review", "label": "Annual Review", "type": "text", "help": "e.g. 3% annually in October"},
             {"path": "fees.invoice.frequency", "label": "Invoice Frequency", "type": "text"},
             {"path": "fees.invoice.due_days", "label": "Invoice Due Days", "type": "number"},
             {"path": "fees.invoice.method", "label": "Payment Method", "type": "text"},
         ],
         "tables": [
             {"path": "fees.additional", "title": "Additional Charges", "add_label": "Add Charge",
              "columns": [{"path": "label", "label": "Service", "type": "text"},
                          {"path": "amount", "label": "Amount (ex VAT)", "type": "money"}]}
         ]},
        # Banking & Insurance
        {"key": "banking", "title": "Banking & Client Account",
         "fields": [
             {"path": "banking.name", "label": "Bank Name", "type": "text"},
             {"path": "banking.bic", "label": "BIC", "type": "text"},
             {"path": "banking.address", "label": "Bank Address", "type": "textarea"},
             {"path": "banking.interest_policy", "label": "Interest Policy", "type": "text"},
         ]},
        {"key": "insurance", "title": "Professional Indemnity Insurance",
         "fields": [
             {"path": "insurance.pi_insurer", "label": "Insurer", "type": "text"},
             {"path": "insurance.policy", "label": "Policy Number", "type": "text"},
             {"path": "insurance.address", "label": "Insurer Address", "type": "textarea"},
         ]},
        # Schedule I — Development
        {"key": "development", "title": "Schedule I — Development",
         "fields": [
             {"path": "development.name", "label": "Name", "type": "text"},
             {"path": "development.address", "label": "Address", "type": "textarea"},
             {"path": "development.folio", "label": "Folio", "type": "text"},
             {"path": "development.meta.res_units", "label": "Residential Units", "type": "text"},
             {"path": "development.meta.com_units", "label": "Commercial Units", "type": "text"},
             {"path": "development.meta.blocks", "label": "Blocks", "type": "text"},
             {"path": "development.meta.floors", "label": "Floors", "type": "text"},
         ],
         "tables": [
             {"path": "development.meta.ancillary", "title": "Ancillary Facilities", "add_label": "Add Facility",
              "columns": [{"path": "label", "label": "Name", "type": "text"}]}
         ]},
        # Schedule II — Part I Services (as long lists you can curate per site)
        {"key": "schedule_ii.part_i", "title": "Schedule II — Part I: Services Provided Directly",
         "fields": [
             {"path": "schedule_ii.part_i.accounting", "label": "Accounting — Bullets", "type": "textarea",
              "help": "One per line"},
             {"path": "schedule_ii.part_i.corporate", "label": "Corporate — Bullets", "type": "textarea",
              "help": "One per line"},
             {"path": "schedule_ii.part_i.insurance_mgmt", "label": "Insurance Mgmt — Bullets", "type": "textarea",
              "help": "One per line"},
             {"path": "schedule_ii.part_i.estate_mgmt", "label": "Estate Mgmt — Bullets", "type": "textarea",
              "help": "One per line"},
         ]},
        # Schedule II — Part II Procurement (simple list)
        {"key": "schedule_ii.part_ii", "title": "Schedule II — Part II: Procurement (List)",
         "fields": [
             {"path": "schedule_ii.part_ii", "label": "Procurement Items (one per line)", "type": "textarea"}
         ]},
        # Schedule II — Part III Emergency notes (provider fields already captured under emergency)
        {"key": "schedule_ii.part_iii", "title": "Schedule II — Part III: Emergency Notes",
         "fields": [
             {"path": "schedule_ii.part_iii.notes", "label": "Additional Notes", "type": "textarea"}
         ]},
        # Schedule II — Part IV Additional Services with pricing
        {"key": "schedule_ii.part_iv", "title": "Schedule II — Part IV: Additional Services",
         "tables": [
             {"path": "schedule_ii.part_iv", "title": "Service + Fee", "add_label": "Add Service",
              "columns": [{"path": "label", "label": "Service", "type": "text"},
                          {"path": "amount", "label": "Fee (ex VAT; blank for TBA)", "type": "money"}]}
         ]},
        # Schedule III — Records kept
        {"key": "records_schedule_iii", "title": "Schedule III — Records",
         "fields": [
             {"path": "records_schedule_iii", "label": "Records (one per line)", "type": "textarea",
              "help": "Paste the list; one per line"}
         ]},
        # Emergency & Termination & Branding
        {"key": "emergency", "title": "Emergency Services",
         "fields": [
             {"path": "emergency.provider", "label": "Provider", "type": "text"},
             {"path": "emergency.phone", "label": "Phone", "type": "text"},
             {"path": "emergency.email", "label": "Email", "type": "email"},
             {"path": "emergency.annual_fee_ex_vat", "label": "Annual Fee (ex VAT)", "type": "money"},
         ]},
        {"key": "termination", "title": "Termination",
         "fields": [{"path": "termination.notice_weeks", "label": "Notice Weeks", "type": "number"}]},
        {"key": "branding", "title": "Branding",
         "fields": [{"path": "branding.primary_hex", "label": "Primary Color (HEX)", "type": "text"}]},
        {"key": "signatures", "title": "Signatures",
         "fields": [
             {"path": "signatures.agent.name", "label": "Agent Signatory", "type": "text"},
             {"path": "signatures.agent.role", "label": "Agent Role", "type": "text"},
             {"path": "signatures.agent.licence_no", "label": "Agent Licence No.", "type": "text"},
             {"path": "signatures.agent.date", "label": "Agent Sign Date (YYYY-MM-DD)", "type": "text"},
         ],
         "tables": [
             {"path": "signatures.client", "title": "Client Signatories", "add_label": "Add Signatory",
              "columns": [{"path": "name", "label": "Name", "type": "text"},
                          {"path": "role", "label": "Role", "type": "text"},
                          {"path": "date", "label": "Date (YYYY-MM-DD)", "type": "text"}]}
         ]},
    ]
}


@click.command("seed-contract-template-ie")
def seed_contract_template_ie():
    """
    Seed/Update: PSRA (IE) Property Services Agreement template + FULL version (Schedules II & III).
    """
    tpl = (ContractTemplate.query
           .filter_by(jurisdiction="IE", authority="PSRA",
                      name="Property Services Agreement (PSRA Form D)")
           .first())
    if not tpl:
        tpl = ContractTemplate(
            jurisdiction="IE",
            authority="PSRA",
            name="Property Services Agreement (PSRA Form D)",
            description="PSRA / S43 Form D — 07 Oct 2022 (full schedules)",
            is_active=True,
        )
        db.session.add(tpl)
        db.session.flush()

    ver = (ContractTemplateVersion.query
           .filter_by(template_id=tpl.id, version_label="PSRA-FormD-2022-Full")
           .first())

    clause_map = {
        "termination_notice_weeks": 12,
        "vat_default": 23,
        "invoice_due_days_default": 30,
        "jurisdiction": "IE",
        "authority": "PSRA",
        "form_date": "2022-10-07"
    }

    if not ver:
        ver = ContractTemplateVersion(
            template_id=tpl.id,
            version_label="PSRA-FormD-2022-Full",
            effective_from=date(2022, 10, 7),
            source_url="https://www.psr.ie/licensees/letters-of-engagement/",
            checksum=None,
            html_template=HTML_TEMPLATE_PSRA_FULL,
            ai_summary="Full PSRA Form D (07 Oct 2022) with Schedules II & III rendered from data_json.",
            ai_clause_map=json.dumps(clause_map),
            ai_status="Published",
            form_schema=json.dumps(FORM_SCHEMA_PSRA_FULL),
        )
        db.session.add(ver)
    else:
        ver.html_template = HTML_TEMPLATE_PSRA_FULL
        ver.form_schema = json.dumps(FORM_SCHEMA_PSRA_FULL)
        ver.ai_clause_map = json.dumps(clause_map)
        ver.ai_status = "Published"

    db.session.commit()
    click.echo("✅ Seeded/updated PSRA (IE) template: PSRA-FormD-2022-Full")

# Document Template Ownership Matrix

Status: active document ownership control note

Purpose: prevent document templates from becoming tangled as LogixPM, Works Logix, Contractor Logix, Finance Logix, Director Logix, Members Logix and HR Logix grow independently.

The platform may share rendering services, branding primitives and PDF/export tooling. Document ownership does not move just because the renderer is shared.

## Core Rule

The module that creates and controls the business document owns that document template, its numbering rules, its approval flow and its settings.

Other modules may view, reference, approve, reject, pay or archive the document through governed workflows, but they do not own the template unless they create the document.

## Ownership Matrix

| Document Type | Owning Module | View / Action By Other Modules | Boundary Rule |
| --- | --- | --- | --- |
| Work order | Works Logix / Property Management Logix | Contractor Logix can accept, reject, update and complete assigned work. Members Logix can see permitted status. Finance Logix can reference approved payment handoff. | Contractors must not edit the work-order template. |
| Work-order pack for contractor | Works Logix / Property Management Logix | Contractor Logix can view the assigned pack and download permitted output. | The pack is a management-side issue instruction, not a contractor-created document. |
| Member maintenance request | Members Logix | Works Logix can triage, ask for detail, reject or convert. GAR can summarise source-backed history. | Management can act on the request but does not own the member-submitted source record. |
| Job docket | Contractor Logix | Works Logix can view submitted completion evidence. Finance Logix may reference approved payment readiness. | PM/Admin users must not own or edit contractor job-docket templates. |
| Contractor completion report | Contractor Logix | Works Logix can approve, return or close. Members Logix may see visible completion notes. | Contractor-created completion evidence stays contractor-owned unless copied into a governed Works audit record. |
| Contractor quotation response | Contractor Logix | Works Logix and Director Logix can review, compare and approve/reject. Finance Logix may reference an approved quote. | Management owns the quotation request; contractors own their quote responses. |
| Quotation request | Works Logix / Property Management Logix | Contractor Logix can decline or respond. Director Logix can review/vote where configured. | Contractors must not own the quotation request template. |
| Contractor payment request | Contractor Logix | Works Logix can review readiness. Finance Logix can intake, approve and post through finance workflow. | Payment request is contractor-originated; finance invoice/ledger records are Finance-owned. |
| Supplier invoice record | Finance Logix | Works Logix may link source work. Contractor Logix may see payment status for its own submitted requests. | Finance owns invoice, approval, ledger and payment records. |
| Service charge statement / balance notice | Finance Logix | Members Logix may show owner-visible balances. GAR can answer with finance visibility controls. | Members Logix displays permitted finance output but does not own finance templates. |
| Contract / PSRA renewal document | Property Management Logix | Finance Logix may see value/expiry data. GAR can summarise risks. | Contract templates stay with the management module. |
| Key site information export | Property Management Logix | Contractor Logix can see permitted contractor-facing sections. Members/Directors can see permitted sections. | Contractors may propose site-info updates but do not own published management site-info templates. |
| Director pack / governance report | Director Logix | Property Management Logix and Finance Logix can supply source data. | Director pack owns governance presentation, not the underlying source facts. |
| HR policy / staff document | HR Logix | Core Platform may manage user identity. Other modules do not own HR documents. | HR templates must not leak into management, contractor or member settings. |

## Numbering Rules

- Work-order numbers belong to Works Logix / Property Management Logix.
- Job-docket numbers belong to Contractor Logix.
- Contractor job numbers may be contractor-owned external references.
- Payment-request numbers belong to Contractor Logix until Finance creates Finance-owned invoice or ledger records.
- Finance document numbers belong to Finance Logix.

When two organisations both use the same visible short number, the platform should display a safe prefix or source context, such as management-company code plus work-order number, to avoid ambiguity.

## Settings Placement

Document template settings should appear inside the owning module settings area:

- Property Management / Works settings for work orders, quotation requests, contract documents and key site exports.
- Contractor Logix settings for job dockets, contractor quotation responses, contractor payment requests and contractor completion reports.
- Finance Logix settings for invoices, payment runs, statements, balance notices and finance reports.
- Director Logix settings for board packs, approval documents and governance reports.
- Members Logix settings for portal notices and member-facing request confirmations.
- HR Logix settings for staff documents, HR letters and policies.

The shared Settings Centre may list connected module settings, but saving a template must route to the owning module endpoint.

## Red Flags

Stop and review the boundary if:

- a contractor setting edits a work-order template;
- a LogixPM setting edits a contractor job-docket template;
- a member portal page edits finance invoice or ledger templates;
- a shared PDF renderer decides document ownership;
- a document is generated without source record, owner module and visibility metadata.

## Guarded By

Primary checks:

```powershell
.\venv\Scripts\python.exe scripts\contractor_document_template_boundary_check.py
.\venv\Scripts\python.exe scripts\module_settings_registry_check.py
.\venv\Scripts\python.exe scripts\module_access_security_boundary_check.py
.\venv\Scripts\python.exe scripts\module_service_contract_check.py
.\venv\Scripts\python.exe scripts\platform_documentation_contract_check.py
```

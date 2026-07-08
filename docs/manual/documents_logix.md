# Documents Logix

Status: foundation operating guide

Last updated: 2026-06-08

## Purpose

Documents Logix will provide the governed document and file layer used across LogixPM.

Documents should be linked back to source records such as clients, developments, units, works, contracts, compliance records, finance records or users. They should not live as disconnected files.

## Current Integration Points

Current source records include:

- general documents
- client compliance documents
- media files linked to clients or units
- exported file/report logs

## GAR Metadata Query

GAR can now answer permitted document metadata questions from source records.

The current query can summarise:

- document counts
- expiry dates
- items expiring within 90 days
- items needing manual review
- GAR parsing readiness
- exported file logs
- source references

This is metadata-only. GAR does not yet read full file contents, extract clauses, interpret signed contracts, parse invoices or expose file paths.

## Future Scope

Documents Logix should later add:

- governed document ingestion
- document classification
- OCR and structured extraction
- source-cited AI summaries
- approval and redaction workflows
- immutable final documents
- role-aware download and sharing controls

GAR should read from those services once they exist. GAR should not own document governance directly.

## Core Document Template Foundation

The platform now has a shared Core Document Template foundation for branded, governed documents across modules.

This is the source layer for future:

- Works Logix work orders
- Contractor Logix Job Dockets
- Contractor Logix Payment Requests
- Works Logix Quotation Requests
- Contractor Logix Quotation Responses
- Quotations
- Finance Logix Invoices
- Contracts Logix agreements
- GAR reports

Templates can be global defaults or company-specific records. They hold document type, module, logo mode, branding source, terms text, footer text, numbering prefix, supported output formats and required context keys.

This means logos, terms and conditions, payment request wording, invoice wrappers and PDF-ready layouts should not be rebuilt separately in each module.

The current foundation resolves the right template payload and branding context. It does not yet generate final PDFs. Generated final documents should later be stored as locked/auditable `Document` records, linked back to their source work order, job docket, invoice, quote, contract or GAR report.

Template setup is available through `Settings -> Document Templates`.

The settings page groups templates by the module that owns the document:

- Property Management Logix owns work orders and management-side quote requests.
- Contractor Logix owns job dockets, contractor quote responses and contractor-created payment requests.
- Finance Logix owns invoices once the finance ledger workflow is built.
- Contracts Logix owns agreement templates.
- GAR owns source-backed report wrappers.

Shared handoff documents should still show where they are reviewed. For example, a Contractor Logix Payment Request is created by the contractor, but reviewed through Works Logix and future Finance Logix. That does not make it a LogixPM-created document.

Document previews and future generated outputs now share the same rendering foundation. The preview screen uses governed sample data, while live documents should pass their source work order, job docket, quote, invoice, contract or GAR record into the same renderer. This keeps on-screen previews, future PDFs and stored final documents aligned instead of creating separate document logic in each module.

The foundation is protected by:

```text
.\venv\Scripts\python.exe scripts\document_template_foundation_check.py
```

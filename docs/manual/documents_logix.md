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

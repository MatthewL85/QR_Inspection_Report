# HR Logix

Status: foundation operating guide

Last updated: 2026-05-28

## Purpose

HR Logix will manage internal staff profile, policy, leave and employee lifecycle records.

## Future Scope

HR Logix should support:

- employee profile records
- staff contact information
- leave requests
- policy acknowledgements
- employment documents
- reviews and performance records
- future staff mobile self-service

## Current Integration Points

The Team Manager already captures user profile information used across the platform, including:

- full name
- email
- role
- company
- mobile phone
- direct line
- extension
- account status

When Logix HR is active, creating a new platform user should also create or link the HR profile.

GAR can now query the Team Manager source records for permitted Super Admin/Admin users. This covers team directory counts, roles, contact fields and client assignment gaps.

GAR must not answer HR leave, rota, policy, employment-document or performance questions until HR Logix has its own source-backed services.

## Important Rule

HR Logix should link to the core `user_id`. It should not duplicate login identity or role permission control.

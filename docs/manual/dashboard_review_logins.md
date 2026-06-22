# Dashboard Review Logins

Status: local development review aid

Purpose: seed a predictable set of local login accounts so each current dashboard can be reviewed from the correct role perspective.

Run:

```text
.\venv\Scripts\python.exe scripts\seed_dashboard_review_users.py
```

All seeded review accounts use:

```text
Password: review2026
PIN: 2026
```

## Accounts

| Area | Email | Username | Opens |
| --- | --- | --- | --- |
| Super Admin | `review.superadmin@logixpm.test` | `review_superadmin` | `/super-admin/dashboard` |
| Admin Portal | `review.admin@logixpm.test` | `review_admin` | `/admin-portal/dashboard` |
| Property Manager | `review.pm@logixpm.test` | `review_pm` | `/pm/dashboard` |
| Assistant | `review.assistant@logixpm.test` | `review_assistant` | `/assistant/dashboard` |
| Assistant Manager / Cover | `review.assistant.manager@logixpm.test` | `review_assistant_manager` | `/assistant/dashboard` |
| Finance Logix | `review.finance@logixpm.test` | `review_finance` | `/finance/dashboard` |
| Contractor Logix | `review.contractor@logixpm.test` | `review_contractor` | `/contractor/dashboard` |
| Director Logix | `review.director@logixpm.test` | `review_director` | `/director/dashboard` |
| Members Logix - Owner | `review.member@logixpm.test` | `review_member` | `/members/dashboard` |
| Members Logix - Resident | `review.resident@logixpm.test` | `review_resident` | `/members/dashboard` |

The script is idempotent. Running it again updates the same accounts.

## HR Logix Note

HR Logix currently has data/model foundation and HR profile linking support, but it does not yet have a dedicated `/hr` dashboard. HR should be reviewed later once the HR module receives its own route, dashboard and role-gated workflow.

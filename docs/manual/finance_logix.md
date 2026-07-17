# Finance Logix

Status: shell operating guide

Last updated: 2026-07-11

## Purpose

Finance Logix will own the financial records for developments and units.

## Future Scope

Finance Logix should manage:

- budgets
- service charges
- invoices
- payments
- arrears
- supplier costs
- financial reports
- service charge balances visible to permitted owners

## Current Integration Points

The unit and client screens already reserve finance connection points such as:

- service charge balance
- service charge scheme
- service charge percentage
- billing frequency
- financial year period

Finance users also have a read-only GAR finance digest feed at:

```text
/finance/gar/feed.json
```

Financial Controllers are scoped to their assigned developments through `assigned_fc_id`. Broader Finance users can see the company finance context where their role permits it.

The Finance dashboard now surfaces a GAR Finance Digest using source-backed portfolio, development health and Works intelligence signals. This is only a digest; Finance Logix remains the owner of ledgers, invoices, service charges, arrears and financial reporting.

The Finance dashboard also includes a read-only Payment Request Intake. This shows contractor Payment Requests only after Works Logix has reviewed them and marked them `Ready for Finance`. The intake links back to the shared source-backed review pack, but it does not create an invoice, approve an invoice, post a ledger entry or mark a payment as made.

The Finance dashboard also includes Ask GAR. Finance users can ask source-backed questions in their permitted finance scope. Where the question relies on live debtor, arrears, budget, payment or ledger services that are not ready yet, GAR should explain that the module is not query-ready rather than inventing an answer.

Finance Logix has a module-owned Connections page at `/finance/settings/connections`. This is where a standalone Finance Logix workspace should manage native Logix links and future finance-owned adapters. Native Logix connections use organisation UID, module subscription and governed connection codes. External accounting systems such as Sage, Xero or QuickBooks should be added later as Finance-owned adapters, because Finance Logix owns ledger mapping, invoice sync, payment references and reconciliation rules.

## GAR Readiness

GAR can recognise finance questions such as:

- debtors by development
- arrears by owner or unit
- budget spent versus budget approved
- invoice and payment status
- service charge balances

However, GAR should not answer these as live financial facts until Finance Logix exposes validated, role-gated query services for the source records.

The current GAR capability registry marks Finance Logix as `foundation_present_not_query_ready`. This means the model foundations exist, but live answers such as `Tell me the debtors in Matthew Lavery` must wait until debtor, budget, invoice, payment and ledger services are completed and tested.

## Important Rule

Finance Logix should own ledgers and transaction records. Unit and client screens should show summaries, not duplicate finance records.

Works Logix can hand a contractor Payment Request into Finance readiness, but Finance Logix must remain the owner of invoice approval, ledger posting, payment runs and supplier reconciliation when those workflows are built.

Finance Logix settings should not be hidden inside Contractor Logix or Property Management settings when Finance is purchased independently. In a connected LogixPM suite, the combined Settings Centre can link to the same Finance-owned setup surface.

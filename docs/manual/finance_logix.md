# Finance Logix

Status: shell operating guide

Last updated: 2026-05-28

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

The Finance dashboard also includes Ask GAR. Finance users can ask source-backed questions in their permitted finance scope. Where the question relies on live debtor, arrears, budget, payment or ledger services that are not ready yet, GAR should explain that the module is not query-ready rather than inventing an answer.

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

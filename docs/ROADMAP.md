# Roadmap and current boundaries

This page separates shipped functionality from possible future work. It is not a delivery schedule or a claim that the hub supports every accounting workflow.

## Available in v0.2.0

- A navigable hub with paths for owners, accountants and finance teams.
- Bank-versus-ledger transaction matching and exception exports.
- AR/AP aging, intercompany pair review and trust-balance arithmetic.
- Construction estimating, earned-value and cost-to-complete scenarios.
- Weekly cash forecasts, annual driver projections, DCF sensitivities and acquisition screening.
- Disk-backed large-file ledger validation/aggregation and a reproducible million-row benchmark.
- Reusable CSV registers, a management-report outline, fictional case studies and test workflows.

## Candidate improvements

| Area | Next useful increment | Evidence needed before describing it as supported |
|---|---|---|
| Construction | Schedule-based project cash flow, retention and committed-cost import | Independently checked schedules and exception tests |
| M&A | Integrated financial statements, purchase-price allocation and debt amortization | Balanced statement controls, purchase-accounting review and scenario tests |
| Multi-entity finance | Explicit elimination journals, consolidation mapping and FX translation | Entity/currency policy, eliminations reconciliation and ownership treatment |
| Data connectors | QuickBooks/Xero/Buildium import adapters | Authorized API access, data mapping, reconciliation and failure handling |
| Team deployment | Review permissions, audit records, backups and deployment monitoring | Access-control tests, recovery tests and operational ownership |
| Templates | Formula-driven XLSX models and further industry variants | Independent formula controls, render checks and clear accounting assumptions |

Only the first section is included in this release. Contributions should begin with a specific user problem and an anonymized or fictional reproducible example.

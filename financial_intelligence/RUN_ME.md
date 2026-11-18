# Run the interactive Finance Intelligence Lab

From the repository root:

```bash
python -m pip install -r financial_intelligence/requirements-dashboard.txt
streamlit run financial_intelligence/dashboard.py
```

Run automated checks:

```bash
python -m pytest financial_intelligence/test_models.py financial_intelligence/test_enterprise.py -q
```

Try the supplied `sample_ledger.csv` under **CSV aggregation**.

## Data and scale

CSV processing streams rows rather than storing the entire input file, but the in-memory set of unique IDs and group totals grows with distinct IDs/groups. This is not yet a bounded-memory enterprise ingestion system. A production design needs durable deduplication, database indexes, job queues, observability, access controls, and measured load tests. Only one currency can be aggregated per run; no intercompany eliminations or consolidation are performed.

**Financial caution:** These simplified models do not replace a construction estimator, professional valuation, audit, or regulatory compliance process. Do not use actual confidential customer records in a public demo deployment.

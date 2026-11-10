# Contributing

Thank you for helping improve the toolkit. Contributions should solve a real problem or improve the project for users.

## Accounting examples and bugs

Open an issue describing the expected result, actual result, and the smallest **fictional** bank/ledger CSV example that reproduces the problem. Include the date window and browser name. Do not include client records, account numbers, payroll details, credentials, or other private information.

Potential duplicate flags and unmatched rows are intentionally conservative. If suggesting a matching change, explain how it avoids pairing unrelated transactions or using one row twice.

## Code changes

1. Discuss substantial new features in an issue first.
2. Fork the repository and make a focused change.
3. Add a test for a meaningful new behavior or bug fix. The engine lives inside the `reconciliation-core` script in `apex-reconcile.html`.
4. Run `node --test tests/reconciliation.test.cjs`.
5. For interface changes, open the HTML file, run the demo, try an invalid CSV, check the exports, and check a narrow window.
6. Submit a pull request explaining the problem, change, and validation.

Keep money arithmetic in integer cents. Keep every account/currency separate. Do not add network calls, tracking, external scripts, or storage of financial data without first discussing the change and its implications.

Keep changes focused and explain how they help users or maintainers.

Use respectful language. Disclose material AI assistance and review generated changes before submitting. By contributing, you offer your contribution under the repository's MIT licence.

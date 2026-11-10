"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "apex-reconcile.html"), "utf8");
const source = html.match(/<script id="reconciliation-core">([\s\S]*?)<\/script>/)[1];
const sandbox = { module: { exports: {} } };
vm.runInNewContext(source, sandbox);
const A = sandbox.module.exports;
const header = "id,date,description,amount,reference,account,currency\n";
function csv(rows) { return header + rows.join("\n"); }
function transaction(id, overrides = {}) {
  const row = { id, date: "2026-10-01", description: "Example", amount: "10.00", reference: "", account: "Operating", currency: "USD", ...overrides };
  return [row.id, row.date, row.description, row.amount, row.reference, row.account, row.currency].map(value => '"' + String(value).replaceAll('"', '""') + '"').join(",");
}
function compare(bank, ledger, options) { return A.reconcile(A.readTransactions(csv(bank), "bank"), A.readTransactions(csv(ledger), "ledger"), options); }
const b = overrides => transaction("B1", overrides), l = overrides => transaction("L1", overrides);

test("CSV supports BOM, CRLF, commas, escaped quotes and multiline fields", () => {
  const data = A.readTransactions('\uFEFF' + header + 'B1,2026-10-01,"Example, ""quoted""\ncontinued",10.00,R1,Operating,USD\r\n', "bank");
  assert.equal(data[0].description, 'Example, "quoted"\ncontinued');
  assert.equal(data[0].line, 2);
});
test("malformed quoted CSV is rejected", () => {
  for (const value of ['a,b\n"unclosed,b', 'a,b\nabc"def,b', 'a,b\n"abc"def,b']) assert.throws(() => A.parseCSV(value));
});
test("amounts use exact integer cents", () => {
  assert.equal(A.moneyToCents("0.10") + A.moneyToCents("0.20"), 30n);
  assert.equal(A.moneyToCents("(1,234.56)"), -123456n);
  assert.equal(A.formatMoney(-1n), "-0.01");
  assert.equal(A.moneyToCents("+45"), 4500n);
});
test("invalid money formats and excessive precision are rejected", () => {
  for (const value of ["1.234", "1,23", "1e4", "Infinity", "$10", "NaN", "", "(-12)", "10000000000000.00"])
    assert.throws(() => A.moneyToCents(value), undefined, value);
});
test("calendar dates are validated without timezone ambiguity", () => {
  assert.equal(A.dateToDay("2024-02-29") - A.dateToDay("2024-02-28"), 1);
  for (const value of ["2026-02-29", "2026-02-30", "01/02/2026", "2026-13-01"])
    assert.throws(() => A.dateToDay(value));
});
test("required columns, row lengths and duplicate IDs are validated", () => {
  assert.throws(() => A.readTransactions("date,amount\n2026-10-01,1", "bank"), /missing columns/);
  assert.throws(() => A.readTransactions(header + "only,three,cells", "bank"), /Expected 7 columns/);
  assert.throws(() => A.readTransactions(csv([b(), b()]), "bank"), /Duplicate row id/);
  assert.throws(() => A.readTransactions(header.replace("reference", "id") + b(), "bank"), /unique/);
  assert.throws(() => A.readTransactions(header, "bank"), /no transaction rows/);
});
test("missing optional IDs receive traceable physical line IDs", () => {
  const rows = A.readTransactions("date,description,amount,account,currency\n2026-10-01,Example,10,Operating,USD\n", "bank");
  assert.equal(rows[0].id, "bank-line-2");
});
test("unique reference, same amount and nearby date create one suggestion", () => {
  const r = compare([b({ reference: "REF1" })], [l({ reference: "ref1", date: "2026-10-03", description: "Different wording" })]);
  assert.equal(r.matches.length, 1); assert.equal(r.matches[0].dayDifference, 2); assert.equal(r.exceptions.length, 0);
});
test("same reference with a different amount stays unresolved", () => {
  const r = compare([b({ reference: "REF1", amount: "10" })], [l({ reference: "REF1", amount: "9.99" })]);
  assert.equal(r.matches.length, 0); assert.equal(r.exceptions.length, 2); assert.match(r.exceptions[0].reason, /0.01 USD/);
});
test("same reference outside date window stays unresolved", () => {
  const r = compare([b({ reference: "REF1" })], [l({ reference: "REF1", date: "2026-10-05" })], { days: 3 });
  assert.equal(r.matches.length, 0); assert.match(r.exceptions[0].reason, /outside/);
});
test("an exact date, amount and normalized description can suggest a match", () => {
  const r = compare([b({ description: "  OFFICE  Supplies " })], [l({ description: "office supplies" })]);
  assert.equal(r.matches.length, 1); assert.match(r.matches[0].rule, /description/);
});
test("conflicting nonempty references override otherwise exact details", () => {
  const r = compare([b({ reference: "A" })], [l({ reference: "B" })]);
  assert.equal(r.matches.length, 0); assert.match(r.exceptions[0].reason, /references conflict/);
});
test("potential duplicates are retained and never matched", () => {
  const r = compare([b({ reference: "R1" }), transaction("B2", { reference: "R1" })], [l({ reference: "R1" })]);
  assert.equal(r.matches.length, 0); assert.equal(r.duplicateCount, 2); assert.equal(r.exceptions.length, 3);
  assert.equal(r.balances[0].bankCents, 2000n);
});
test("reused references with different dates are held for review", () => {
  const r = compare([b({ reference: "R1" }), transaction("B2", { reference: "R1", date: "2026-10-02" })], [l({ reference: "R1" })]);
  assert.equal(r.matches.length, 0); assert.equal(r.duplicateCount, 0); assert.match(r.exceptions[0].reason, /Repeated reference/);
});
test("same amount alone never becomes an automatic suggestion", () => {
  const r = compare([b({ description: "Incoming transfer" })], [l({ description: "Invoice A" }), transaction("L2", { description: "Invoice B" })]);
  assert.equal(r.matches.length, 0); assert.equal(r.exceptions[0].candidateCount, 2);
});
test("accounts are kept separate even when all other fields match", () => {
  const r = compare([b({ reference: "R1", account: "Savings" })], [l({ reference: "R1", account: "Operating" })]);
  assert.equal(r.matches.length, 0); assert.equal(r.exceptions[0].candidateCount, 0); assert.equal(r.balances.length, 2);
});
test("currencies are kept separate and are never converted", () => {
  const r = compare([b({ reference: "R1", currency: "EUR" })], [l({ reference: "R1", currency: "USD" })]);
  assert.equal(r.matches.length, 0); assert.equal(r.balances.length, 2); assert.equal(r.exceptions[0].candidateCount, 0);
});
test("opposite signs cannot match", () => {
  const r = compare([b({ amount: "-10", reference: "R1" })], [l({ amount: "10", reference: "R1" })]);
  assert.equal(r.matches.length, 0); assert.match(r.exceptions[0].reason, /amount differs/);
});
test("zero amount rows require manual review", () => {
  const r = compare([b({ amount: "0" })], [l({ amount: "0" })]);
  assert.equal(r.matches.length, 0); assert.match(r.exceptions[0].reason, /Zero-amount/);
});
test("invalid date-window settings are rejected", () => {
  for (const days of [-1, 8, 1.5, "3", NaN]) assert.throws(() => compare([b()], [l()], { days }));
});
test("demo has the documented results and preserves every input row", () => {
  const bank = A.readTransactions(fs.readFileSync(path.join(root, "samples/bank.csv"), "utf8"), "bank");
  const ledger = A.readTransactions(fs.readFileSync(path.join(root, "samples/ledger.csv"), "utf8"), "ledger");
  const r = A.reconcile(bank, ledger);
  assert.equal(r.matches.length, 4); assert.equal(r.bankExceptionCount, 6); assert.equal(r.ledgerExceptionCount, 6); assert.equal(r.duplicateCount, 2);
  assert.equal(r.matches.length + r.bankExceptionCount, bank.length);
  assert.equal(r.matches.length + r.ledgerExceptionCount, ledger.length);
  const usd = r.balances.find(row => row.account === "Operating" && row.currency === "USD");
  assert.equal(A.formatMoney(usd.bankCents), "6579.50"); assert.equal(A.formatMoney(usd.ledgerCents), "7419.50");
  assert.equal(A.formatMoney(usd.bankCents - usd.ledgerCents), "-840.00");
  assert.equal(new Set(r.matches.map(m => m.bank.id)).size, r.matches.length);
  assert.equal(new Set(r.matches.map(m => m.ledger.id)).size, r.matches.length);
  const pairs = rows => rows.map(m => `${m.bank.id}:${m.ledger.id}`).sort().join("|");
  assert.equal(pairs(r.matches), pairs(A.reconcile([...bank].reverse(), [...ledger].reverse()).matches));
  for (const balance of r.balances) {
    const remaining = r.exceptions.filter(e => e.row.account === balance.account && e.row.currency === balance.currency);
    const difference = remaining.reduce((total, e) => total + (e.row.source === "bank" ? e.row.cents : -e.row.cents), 0n);
    assert.equal(balance.bankCents - balance.ledgerCents, difference);
  }
});
test("CSV exports mark suggestions for review and preserve numeric signs", () => {
  const r = compare([b({ amount: "-10" })], [l({ amount: "-10" })]);
  const output = A.exportReport(r, "matches");
  assert.match(output, /REVIEW_REQUIRED/); assert.match(output, /"-10.00"/); assert.doesNotMatch(output, /"'-10.00"/);
  assert.equal(A.parseCSV(output).length, 2);
});
test("CSV export neutralizes spreadsheet formula prefixes in user text", () => {
  const r = compare([b({ description: '=HYPERLINK("https://example.invalid","x")', reference: "@example" })], [l({ description: "Other" })]);
  const output = A.exportReport(r, "exceptions");
  const rows = A.parseCSV(output);
  assert.ok(rows[1].cells[7].startsWith("'=")); assert.ok(rows[1].cells[8].startsWith("'@"));
});
test("embedded sample data exactly matches the downloadable sample files", () => {
  const data = { window: {} };
  vm.runInNewContext(html.match(/<script id="sample-data">([\s\S]*?)<\/script>/)[1], data);
  for (const source of ["bank", "ledger"]) assert.equal(data.window.APEX_SAMPLES[source], fs.readFileSync(path.join(root, `samples/${source}.csv`), "utf8"));
});
test("oversized input is rejected rather than silently truncated", () => {
  const rows = Array.from({ length: 5001 }, (_, i) => transaction(`B${i}`));
  assert.throws(() => A.readTransactions(csv(rows), "bank"), /maximum 5,000/);
});
test("large ambiguous groups report all candidates while bounding the ID list", () => {
  const left = Array.from({ length: 500 }, (_, i) => transaction(`B${i}`, { description: `Bank item ${i}` }));
  const right = Array.from({ length: 500 }, (_, i) => transaction(`L${i}`, { description: `Ledger item ${i}` }));
  const r = compare(left, right);
  assert.equal(r.matches.length, 0); assert.equal(r.exceptions[0].candidateCount, 500); assert.equal(r.exceptions[0].candidateIds.length, 10);
});

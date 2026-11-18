"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const {TextEncoder}=require("node:util");
const root=path.resolve(__dirname,".."),html=fs.readFileSync(path.join(root,"tools/accounting-workbench.html"),"utf8");
const sandbox={module:{exports:{}},TextEncoder};
vm.runInNewContext(html.match(/<script id="workbench-core">([\s\S]*?)<\/script>/)[1],sandbox);
const W=sandbox.module.exports;
const openHeader=["id","party","invoice_date","due_date","amount","paid","currency","entity"];
const transferHeader=["id","date","entity","counterparty","reference","amount","currency"];
const encode=(headers,rows)=>[headers,...rows.map(row=>headers.map(name=>row[name]))].map(row=>row.map(cell=>'"'+String(cell??"").replaceAll('"','""')+'"').join(",")).join("\r\n")+"\r\n";
const invoice=(id,changes={})=>({id,party:"Example Customer",invoice_date:"2026-01-01",due_date:"2026-11-19",amount:"100.00",paid:"0",currency:"USD",entity:"Example Ltd",...changes});
const transfer=(id,changes={})=>({id,date:"2026-11-18",entity:"Parent",counterparty:"Property",reference:"T-001",amount:"-1000",currency:"USD",...changes});
const openItems=rows=>W.readOpenItems(encode(openHeader,rows));
const transfers=rows=>W.readTransfers(encode(transferHeader,rows));
const other=changes=>transfer("B",{entity:"Property",counterparty:"Parent",amount:"1000",...changes});
const trustValues=(changes={})=>({as_of_date:"2026-11-19",entity:"Example Property",trust_account:"Client trust",currency:"USD",statement_balance:"12500",deposits_in_transit:"1000",outstanding_payments:"500",book_balance:"13000",client_liability_balance:"13000",...changes});

test("amount parsing stays exact and rejects unsupported precision or non-finite input",()=>{
  assert.equal(W.moneyToCents("0.10")+W.moneyToCents("0.20"),30n);
  assert.equal(W.moneyToCents("(1,234.56)"),-123456n);
  assert.equal(W.formatMoney(-1n),"-0.01");
  for(const value of["nan","Infinity","1e3","1.234","$1.00","1,00","10000000000000"])
    assert.throws(()=>W.moneyToCents(value));
});
test("date checks reject impossible dates and year zero",()=>{
  assert.equal(W.dateToDay("2024-02-29")-W.dateToDay("2024-02-28"),1);
  for(const value of["2026-02-29","2026-02-30","20260101","0000-01-01","19/11/2026"])
    assert.throws(()=>W.dateToDay(value));
});
test("CSV handles quoted commas, escaped quotes, BOM and multiline labels",()=>{
  const data="\uFEFF"+encode(openHeader,[invoice("1",{party:'Example, "quoted"\ncontinued'})]);
  const row=W.readOpenItems(data)[0];
  assert.equal(row.party,'Example, "quoted"\ncontinued');assert.equal(row.line,2);
  for(const text of['a,b\n"unfinished','a,b\nx"y,z','a,b\n"x"y,z'])assert.throws(()=>W.parseCSV(text));
});
test("schema, record width and unique IDs are mandatory",()=>{
  assert.throws(()=>W.readOpenItems("id,amount\nx,1\n"),/Missing columns/);
  assert.throws(()=>W.readOpenItems(openHeader.join(",")+"\nx,too,few\n"),/expected/);
  assert.throws(()=>openItems([invoice("x"),invoice("x")]),/duplicate id/);
  assert.throws(()=>openItems([invoice("")]),/id is required/);
  assert.throws(()=>W.readOpenItems(openHeader.join(",")+"\n"),/no data rows/);
  assert.throws(()=>W.readOpenItems(openHeader.join(",")+",amount\n"),/unique/);
});
test("nonblank records with empty CSV cells are rejected rather than silently skipped",()=>{
  const valid=encode(openHeader,[invoice("good")]);
  assert.throws(()=>W.readOpenItems(valid+",,,,,,,\n"),/id is required/);
  assert.throws(()=>W.readOpenItems(valid+'""\n'),/expected/);
  assert.equal(W.readOpenItems(valid+"\n  \n").length,1);
});
test("aging buckets have exact due-date boundaries",()=>{
  const due=["2026-11-19","2026-11-18","2026-10-20","2026-10-19","2026-09-20","2026-09-19","2026-08-21","2026-08-20"];
  const r=W.ageOpenItems(openItems(due.map((d,i)=>invoice(String(i),{due_date:d}))),"2026-11-19");
  assert.deepEqual(Array.from(r.rows,x=>x.bucket),["Current","1–30","1–30","31–60","31–60","61–90","61–90","91+"]);
  assert.equal(r.groups[0].totals.Current,10000n);assert.equal(r.groups[0].totals["1–30"],20000n);
  assert.equal(r.groups[0].totals["31–60"],20000n);assert.equal(r.groups[0].totals["61–90"],20000n);
  assert.equal(r.groups[0].totals["91+"],10000n);assert.equal(r.groups[0].openCents,80000n);
  assert.equal(r.openCount,8);assert.equal(r.overdueCount,7);
});
test("partial payments reduce open balances without losing exact cents",()=>{
  const r=W.ageOpenItems(openItems([invoice("1",{amount:"10.30",paid:"10.20"}),invoice("2",{amount:"0.20"})]),"2026-11-19");
  assert.equal(r.groups[0].openCents,30n);
});
test("future invoices remain in output but cannot enter aging totals",()=>{
  const r=W.ageOpenItems(openItems([invoice("future",{invoice_date:"2026-11-20",amount:"1000"}),invoice("settled",{paid:"100"})]),"2026-11-19");
  assert.equal(r.futureCount,1);assert.equal(r.settledCount,1);assert.equal(r.openCount,0);
  assert.equal(r.rows.length,2);assert.equal(r.rows[0].status,"FUTURE_INVOICE_EXCLUDED");
  assert.equal(r.rows[0].openCents,100000n);assert.equal(r.rows[0].includedCents,0n);
  assert.equal(r.groups[0].openCents,0n);assert.match(W.exportAging(r),/FUTURE_INVOICE_EXCLUDED/);
});
test("credits and overpayments need separate review instead of misleading aging",()=>{
  for(const changes of[{amount:"-1"},{paid:"-1"},{amount:"1",paid:"2"}])assert.throws(()=>openItems([invoice("x",changes)]),/nonnegative/);
});
test("aging never mixes currencies or different entities",()=>{
  const r=W.ageOpenItems(openItems([invoice("1"),invoice("2",{currency:"EUR"}),invoice("3",{entity:"Another Ltd"}),invoice("4",{entity:"  example   ltd "})]),"2026-11-19");
  assert.equal(r.groups.length,3);
  assert.equal(r.groups.find(g=>g.entity==="Example Ltd"&&g.currency==="USD").openCents,20000n);
});
test("aging preserves exact very large totals beyond JavaScript Number precision",()=>{
  const r=W.ageOpenItems(openItems(Array.from({length:100},(_,i)=>invoice(String(i),{amount:"9999999999999.99"}))),"2026-11-19");
  assert.equal(W.formatMoney(r.groups[0].openCents),"999999999999999.00");
});
test("reciprocal entities, exact reference and opposite amounts produce one suggestion",()=>{
  const r=W.reviewTransfers(transfers([transfer("A",{entity:" parent "}),other({counterparty:" PARENT ",date:"2026-11-20"})]),3);
  assert.equal(r.pairs.length,1);assert.equal(r.pairs[0].dayDifference,2);assert.equal(r.exceptions.length,0);
  assert.match(W.exportTransfers(r),/PAIR_REVIEW_REQUIRED/);
});
test("all mismatched transfer cases stay unresolved",()=>{
  const cases=[{amount:"999.99"},{amount:"-1000"},{date:"2026-11-23"},{currency:"EUR"},{reference:"t-001"},{entity:"Parent",counterparty:"Property"}];
  for(const changes of cases){const r=W.reviewTransfers(transfers([transfer("A"),other(changes)]),3);assert.equal(r.pairs.length,0);assert.equal(r.exceptions.length,2);}
});
test("missing references, zero amounts and same-entity rows are held",()=>{
  for(const rows of[[transfer("A",{reference:""}),other({reference:""})],[transfer("A",{amount:"0"}),other({amount:"0"})],[transfer("A",{counterparty:"Parent"}),transfer("B",{counterparty:"Parent",amount:"1000"})]]){
    const r=W.reviewTransfers(transfers(rows));assert.equal(r.pairs.length,0);assert.equal(r.exceptions.length,2);
  }
});
test("ambiguous reference groups are preserved, not greedily paired",()=>{
  const r=W.reviewTransfers(transfers([transfer("A"),other(),other({id:"C"})]));
  assert.equal(r.pairs.length,0);assert.equal(r.exceptions.length,3);
  assert.equal(r.exceptions.find(e=>e.row.id==="A").candidateCount,2);
  assert.match(r.exceptions[0].reason,/Repeated reference/);
});
test("distinct transfer references match independently and preserve all source rows",()=>{
  const data=transfers([transfer("A"),other(),transfer("C",{reference:"T-002",amount:"-5"}),other({id:"D",reference:"T-002",amount:"5"}),transfer("E",{reference:"missing"})]);
  const r=W.reviewTransfers(data),reversed=W.reviewTransfers([...data].reverse());
  assert.equal(2*r.pairs.length+r.exceptions.length,data.length);
  const pairs=x=>x.pairs.map(p=>[p.left.id,p.right.id].sort().join(":")).sort().join("|");
  assert.equal(pairs(r),pairs(reversed));
  const ids=[...r.pairs.flatMap(p=>[p.left.id,p.right.id]),...r.exceptions.map(e=>e.row.id)];
  assert.equal(new Set(ids).size,data.length);
  const exported=W.parseCSV(W.exportTransfers(r));assert.equal(exported.length,data.length+1);
});
test("candidate counts remain complete while displayed ID lists are bounded",()=>{
  const data=[transfer("A"),...Array.from({length:100},(_,i)=>other({id:"B"+i}))];
  const r=W.reviewTransfers(transfers(data));
  const row=r.exceptions.find(e=>e.row.id==="A");
  assert.equal(row.candidateCount,100);assert.equal(row.candidateIds.length,10);assert.equal(r.exceptions.length,101);
});
test("date-window configuration is validated",()=>{
  for(const days of[-1,8,1.5,"3",NaN])assert.throws(()=>W.reviewTransfers(transfers([transfer("A"),other()]),days));
});
test("trust check reports arithmetic agreement without approving reconciliation",()=>{
  const r=W.trustCheck(trustValues());
  assert.equal(r.adjustedBank,1300000n);assert.equal(r.bankBookDifference,0n);assert.equal(r.bookLiabilityDifference,0n);
  assert.equal(r.status,"ARITHMETIC_AGREEMENT_REVIEW_REQUIRED");
  assert.match(W.exportTrust(r),/ARITHMETIC_AGREEMENT_REVIEW_REQUIRED/);
});
test("trust differences cannot cancel each other into a false agreement",()=>{
  const r=W.trustCheck(trustValues({book_balance:"12999"}));
  assert.equal(r.bankBookDifference,100n);assert.equal(r.bookLiabilityDifference,-100n);
  assert.equal(r.bankLiabilityDifference,0n);assert.equal(r.status,"DIFFERENCE_TO_INVESTIGATE");
});
test("trust adjustments are nonnegative and account/date/currency context is required",()=>{
  for(const changes of[{deposits_in_transit:"-1"},{outstanding_payments:"-1"},{entity:""},{trust_account:""},{currency:"US"},{as_of_date:"2026-02-30"},{entity:undefined}])assert.throws(()=>W.trustCheck(trustValues(changes)));
});
test("CSV exports neutralize dangerous textual prefixes and preserve numeric signs",()=>{
  const ar=W.ageOpenItems(openItems([invoice("=X",{party:'=HYPERLINK("https://example.invalid","x")',entity:"@entity"})]),"2026-11-19");
  const detail=W.parseCSV(W.exportAging(ar))[1].cells;
  assert.equal(detail[2],"'=X");assert.ok(detail[5].startsWith("'="));assert.equal(detail[4],"'@entity");
  const r=W.reviewTransfers(transfers([transfer("=A",{reference:"@REF"}),other({reference:"@REF"})]));
  const rows=W.parseCSV(W.exportTransfers(r));
  assert.equal(rows[1].cells[1],"'=A");assert.equal(rows[1].cells[6],"'@REF");assert.equal(rows[1].cells[8],"-1000.00");
  const trust=W.parseCSV(W.exportTrust(W.trustCheck(trustValues({entity:"=1+1"}))))[1].cells;
  assert.equal(trust[1],"'=1+1");
});
test("summary exports conserve all included balances and keep currencies separate",()=>{
  const r=W.ageOpenItems(openItems([invoice("1",{amount:"50",paid:"10"}),invoice("2",{amount:"7",currency:"EUR"})]),"2026-11-19");
  const rows=W.parseCSV(W.exportAging(r,true));
  assert.equal(rows.length,3);assert.equal(rows[1].cells[8],"40.00");assert.equal(rows[2].cells[8],"7.00");
});
test("browser size and row caps reject oversized files",()=>{
  assert.throws(()=>openItems(Array.from({length:5001},(_,i)=>invoice(String(i)))),/5,000/);
  assert.throws(()=>W.readOpenItems("x".repeat(3*1024*1024+1)),/3 MiB/);
  assert.throws(()=>W.readOpenItems("é".repeat(2*1024*1024)),/3 MiB/);
});
test("embedded demos parse and agree with current downloadable templates",()=>{
  const context={window:{}};vm.runInNewContext(html.match(/<script id="workbench-samples">([\s\S]*?)<\/script>/)[1],context);
  const samples=context.window.APEX_WORKBENCH_SAMPLES;
  for(const[type,filename]of[["ar","ar_open_items.csv"],["ap","ap_open_items.csv"],["transfers","intercompany_transfers.csv"]])
    assert.equal(samples[type].replaceAll("\r\n","\n"),fs.readFileSync(path.join(root,"templates",filename),"utf8").replaceAll("\r\n","\n"));
  const aging=W.ageOpenItems(W.readOpenItems(samples.ar),"2026-11-19");
  assert.equal(aging.openCount,3);assert.equal(aging.overdueCount,1);assert.equal(aging.groups[0].openCents,430000n);
  const review=W.reviewTransfers(W.readTransfers(samples.transfers));
  assert.equal(review.pairs.length,1);assert.equal(review.exceptions.length,4);assert.equal(review.rowCount,6);
});
test("page is self-contained and renders user data through textContent",()=>{
  assert.doesNotMatch(html,/<script\b[^>]*\bsrc=/i);assert.doesNotMatch(html,/\b(?:fetch|XMLHttpRequest|WebSocket|localStorage|sessionStorage)\b/);
  assert.doesNotMatch(html,/\.innerHTML\s*=/);assert.match(html,/connect-src 'none'/);
  const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);
  assert.equal(new Set(ids).size,ids.length);
  const ui=html.match(/<script id="workbench-ui">([\s\S]*?)<\/script>/)[1];
  for(const[,id]of ui.matchAll(/\$\("([a-z-]+)"\)/g))assert.ok(ids.includes(id),"Missing DOM ID "+id);
  new vm.Script(ui); // Parse the actual browser UI, not a duplicate implementation.
});

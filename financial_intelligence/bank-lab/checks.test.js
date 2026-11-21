"use strict";
const assert=require("node:assert/strict"), M=require("./engine.js"),{readInputs}=require("./run.js");
const {filings:db,anchors}=readInputs(),rows=db.filings;
assert.equal(new Set(rows.map(r=>r.bank+" "+r.end)).size,172);
for(const r of rows)assert.deepEqual(M.checks(r).map(x=>x.status),Array(6).fill("Pass"),r.bank+" "+r.end);
const a=anchors[0],r=rows.find(x=>x.end===a.end&&x.bank===a.bank),eps=M.annualEPS(rows,a.bank,a.end);
const damaged=structuredClone(r);damaged.values.assets+=2;
assert.equal(M.checks(damaged)[0].status,"Review");
delete damaged.values.assets;assert.equal(M.checks(damaged)[0].status,"Unavailable");
assert.throws(()=>M.scenario(a,eps,{...M.defaults,cost:3,growth:3}));
assert.throws(()=>M.scenario(a,eps,{...M.defaults,payout:NaN}));
assert.throws(()=>M.merger(a,a,eps,eps,1,0,1));
for(const anchor of anchors){
 const stock=rows.find(x=>x.end===anchor.end&&x.bank===anchor.bank);
 const trailing=M.annualEPS(rows,anchor.bank,anchor.end);
 const unchanged=M.scenario(anchor,trailing,M.defaults);
 assert.ok(Math.abs(unchanged.modelDifference)<1e-9);
 assert.equal(M.earningsStress(stock,0,0,0).common,stock.values.common_net);
 const shock=M.earningsStress(stock,50,50,0);
 assert.ok(shock.common<stock.values.common_net);
 assert.ok(M.scenario(anchor,trailing,{...M.defaults,loss:shock.hit}).capital<unchanged.capital);
 const base=M.forecast(stock,anchor,M.planDefaults),stress=M.forecast(stock,anchor,{...M.planDefaults,depositGrowth:-10});
 assert.ok(stress.at(-1).wholesale>base.at(-1).wholesale);
 for(const y of [...base,...stress])assert.ok(Math.abs(y.difference)<1e-6);
}
const bt=M.backtest(rows);
assert.equal(bt.length,32);
for(const x of bt)assert.ok(x.input_filed<x.year+"-12-31");
console.log("Historical controls, loss transmission, funding, valuation identity and invalid settings passed.");

"use strict";
// Offline run. A new output directory protects previous results.
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const M=require("./engine.js");
const home=__dirname;
const sha=s=>crypto.createHash("sha256").update(s).digest("hex");
function readInputs(){
  const lock=JSON.parse(fs.readFileSync(path.join(home,"inputs.lock.json"),"utf8"));
  function load(name){
    const data=fs.readFileSync(path.join(home,name));
    if(sha(data)!==lock[name])throw Error("Input checksum mismatch: "+name);
    return JSON.parse(data);
  }
  return {filings:load("filings.json"),anchors:load("anchors.json")};
}
function csv(rows){
  const keys=Object.keys(rows[0]);
  function cell(v){return '"'+String(v??"").replaceAll('"','""')+'"';}
  return [keys,...rows.map(r=>keys.map(k=>r[k]))].map(r=>r.map(cell).join(",")).join("\n")+"\n";
}
function generate(dir){
  const {filings,anchors}=readInputs(), rows=filings.filings;
  const totals={Pass:0,Review:0,Unavailable:0}, controls=[], valuations=[],forecasts=[],deals=[],backtest=M.backtest(rows);
  const seen=new Set();
  for(const r of rows){
    const key=r.bank+r.end;if(seen.has(key))throw Error("Duplicate filing "+key);seen.add(key);
    for(const check of M.checks(r)){totals[check.status]++;controls.push({bank:r.bank,period:r.end,...check,source:r.source})}
  }
  for(const a of anchors){
    const r=rows.find(x=>x.bank===a.bank&&x.end===a.end);
    if(M.checks(r).some(c=>c.status!=="Pass"))throw Error("Anchor statements require review: "+a.bank+" "+a.end);
    const eps=M.annualEPS(rows,a.bank,a.end),multiples=M.multiples(a,eps);
    const capitalGap=Math.abs(a.cet1/a.rwa*100-a.cet1_percent);
    if(capitalGap>.05)throw Error("CET1 tie exceeds published rounding.");
    for(const [name,shock,credit,rwa,roe,cost] of [["Reference",0,0,0,12,10],["Funding pressure",25,20,5,11,11],["Combined stress",75,80,12,9,12]]){
      const e=M.earningsStress(r,shock,credit,0),s=M.scenario(a,eps,{...M.defaults,loss:e.hit,rwaChange:rwa,roe,cost});
      if(Math.abs(s.modelDifference)>1e-8)throw Error("Valuation cross-check failed.");
      valuations.push({bank:a.bank,period:a.end,case:name,deposit_cost_bps:shock,credit_cost_bps:credit,assumed_tax_relief_pct:0,rwa_growth_pct:rwa,long_run_roe_pct:roe,cost_of_equity_pct:cost,payout_pct:M.defaults.payout,terminal_growth_pct:M.defaults.growth,eps,price_proxy:multiples.price,pe:multiples.pe,pb:multiples.pb,ptbv:multiples.ptbv,reported_cet1_pct:a.cet1_percent,capital_check_diff_pp:capitalGap,stressed_cet1_pct:s.capital,stressed_pretax_m:e.pretax,stressed_common_income_m:e.common,residual_value:s.residualValue,dividend_value:s.dividendValue,difference:s.modelDifference,capital_source:a.source,book_source:a.book_source,price_source:a.market_source});
    }
    for(const [name,drivers] of [["Reference",M.planDefaults],["Funding pressure",{...M.planDefaults,depositGrowth:-5,marginMove:-25,creditMove:25}],["Combined stress",{...M.planDefaults,loanGrowth:5,depositGrowth:-10,marginMove:-50,creditMove:75}]]){
      for(const year of M.forecast(r,a,drivers))forecasts.push({bank:a.bank,period:r.end,case:name,...drivers,payout_assumption_pct:drivers.payout,...year,source:a.source});
    }
    for(const target of anchors.filter(x=>x.bank!==a.bank&&x.end===a.end)){
      const other=rows.find(x=>x.bank===target.bank&&x.end===target.end);
      const ratio=M.referencePrice(target)/M.referencePrice(a), shareRatio=other.values.diluted_shares/r.values.diluted_shares;
      const m=M.merger(a,target,eps,M.annualEPS(rows,target.bank,target.end),ratio,0,shareRatio);
      deals.push({buyer:a.bank,target:target.bank,period:a.end,exchange_ratio:ratio,aftertax_synergy_per_target_share:0,...m});
    }
  }
  const wape=k=>100*backtest.reduce((s,x)=>s+Math.abs(x[k]),0)/backtest.reduce((s,x)=>s+Math.abs(x.actual),0);
  const summary={cutoff:filings.cutoff,filings:rows.length,controls:totals,forecast_years:forecasts.length,cases:valuations.length,merger_screens:deals.length,forecast_observations:backtest.length,trend_wape_pct:wape("error"),flat_wape_pct:wape("flat_error")};
  const target=path.resolve(dir);
  if(fs.existsSync(target))throw Error("Choose a new output directory.");
  const parent=path.dirname(target);fs.mkdirSync(parent,{recursive:true});
  const tmp=fs.mkdtempSync(path.join(parent,".bank-run-"));
  try{
    for(const [name,data] of Object.entries({checks:controls,scenarios:valuations,forecasts,mergers:deals,backtest}))fs.writeFileSync(path.join(tmp,name+".csv"),csv(data));
    fs.writeFileSync(path.join(tmp,"summary.json"),JSON.stringify(summary,null,2)+"\n");
    fs.renameSync(tmp,target);
  }catch(e){fs.rmSync(tmp,{recursive:true,force:true});throw e}
  console.log(JSON.stringify(summary,null,2));
  if(totals.Review)process.exitCode=1;
}
if(require.main===module){try{generate(process.argv[2]||"bank-results")}catch(e){console.error(e.message);process.exitCode=2}}
module.exports={readInputs};

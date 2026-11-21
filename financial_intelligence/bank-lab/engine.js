"use strict";
// Monetary amounts and share counts in millions, except per-share values.
const BankModel = (() => {
  const fields = {
    assets:"Total assets",liabilities:"Total liabilities",equity:"Total equity incl. noncontrolling interests",
    deposits:"Deposits",net_loans:"Net loans",interest_income:"Interest income",interest_expense:"Interest expense",
    nii:"Net interest income",fees_other:"Noninterest income",opex:"Noninterest expense",
    provisions:"Provision / benefits and claims (issuer definition)",pretax:"Pretax income",
    tax:"Income taxes",continuing_net:"Income from continuing operations incl. noncontrolling interests",
    parent_net:"Net income attributable to parent",common_net:"Income available to common shareholders",
    eps:"Diluted earnings per share ($)",diluted_shares:"Weighted average diluted shares (millions)",
    cash_open:"Opening cash (filing definition)",operating:"Operating cash flow",
    investing:"Investing cash flow",financing:"Financing cash flow",fx:"FX effect on cash",
    change:"Reported net change in cash",cash:"Closing cash (filing definition)"
  };
  function checks(row) {
    const v=row.values, list=[];
    function test(name, positive, negative) {
      const missing=[...positive,...negative].filter(key=>!Number.isFinite(v[key]));
      const sum=keys=>keys.reduce((s,k)=>s+v[k],0);
      const difference=missing.length?null:sum(positive)-sum(negative);
      list.push({name,difference,missing:missing.join(", "),status:missing.length?"Unavailable":Math.abs(difference)<=1?"Pass":"Review"});
    }
    test("Balance sheet",["assets"],["liabilities","equity"]);
    test("Net interest income",["interest_income"],["interest_expense","nii"]);
    test("Pretax income",["nii","fees_other"],["opex","provisions","pretax"]);
    test("Tax bridge",["pretax"],["tax",["BAC","JPM"].includes(row.bank)?"parent_net":"continuing_net"]);
    test("Cash rollforward",["cash_open","change"],["cash"]);
    // Wells Fargo presents the change from its three sections in the reviewed periods.
    const reviewedWells=row.bank==="WFC" && (row.cash_sections_only || ["2025-12-31","2026-09-30"].includes(row.end));
    test("Cash flow sections",reviewedWells?["operating","investing","financing"]:["operating","investing","financing","fx"],["change"]);
    return list;
  }
  function limits(x,min,max,name) {
    if(!Number.isFinite(x)||x<min||x>max)throw Error(name+" must be between "+min+" and "+max+".");
  }
  function annualEPS(rows,bank,end) {
    const find=d=>rows.find(r=>r.bank===bank && r.end===d)?.values.eps;
    if(end.endsWith("12-31"))return find(end);
    const prior=Number(end.slice(0,4))-1;
    const values=[find(end),find(prior+"-12-31"),find(prior+end.slice(4))];
    return values.every(Number.isFinite)?values[0]+values[1]-values[2]:null;
  }
  const referencePrice=a=>a.holdings_dollars/a.holdings_shares;
  function multiples(a,eps) {
    const price=referencePrice(a);
    return {price,pe:eps>0?price/eps:null,pb:price/a.bvps,ptbv:price/a.tbvps};
  }
  const defaults={roe:12,cost:10,growth:3,payout:45,loss:0,rwaChange:0};
  function scenario(a,eps,p) {
    limits(p.roe,0.1,40,"Long-run return on equity (%)");limits(p.cost,1,35,"Cost of equity (%)");
    limits(p.growth,0,15,"Long-run growth (%)");limits(p.payout,0,100,"Annual payout (%)");
    limits(p.loss,0,a.cet1,"After-tax capital loss ($m)");limits(p.rwaChange,-50,100,"RWA change (%)");
    if(p.growth>=p.cost||p.growth>p.roe)throw Error("Growth must be below cost of equity and may not exceed long-run return on equity.");
    if(!Number.isFinite(eps)||!Number.isFinite(a.bvps)||a.bvps<=0)throw Error("Annual earnings and positive common book value are required.");
    const rate=p.cost/100, g=p.growth/100, terminalROE=p.roe/100, startROE=eps/a.bvps;
    let book=a.bvps,pv=0,divPV=0;const years=[];
    for(let year=1;year<=5;year++){
      const roe=startROE+(terminalROE-startROE)*year/5, earnings=book*roe;
      const dividend=Math.max(earnings,0)*p.payout/100, residual=earnings-book*rate;
      const closing=book+earnings-dividend;
      if(closing<=0)throw Error("Scenario exhausts common book value.");
      const discount=(1+rate)**year;
      years.push({year,opening:book,roe,earnings,dividend,closing,residual,pv:residual/discount});
      pv+=residual/discount;divPV+=dividend/discount;book=closing;
    }
    const terminalRI=book*(terminalROE-rate)/(rate-g)/(1+rate)**5;
    const residualValue=a.bvps+pv+terminalRI;
    const dividendValue=divPV+book*(terminalROE-g)/(rate-g)/(1+rate)**5;
    const capital=(a.cet1-p.loss)/(a.rwa*(1+p.rwaChange/100))*100;
    return {years,residualValue,dividendValue,modelDifference:residualValue-dividendValue,capital,capitalMove:(capital-a.cet1/a.rwa*100)*100,terminalRI};
  }
  function earningsStress(r,depositCost,creditCost,taxRate){
    limits(depositCost,0,500,"Incremental deposit cost (bp)");
    limits(creditCost,0,500,"Incremental credit provision (bp)");
    limits(taxRate,0,50,"Tax relief (%)");
    const v=r.values;
    if(![v.net_loans,v.deposits,v.pretax,v.nii,v.common_net].every(Number.isFinite))throw Error("The selected filing lacks a stress input.");
    const months=Number(r.end.slice(5,7));
    const funding=v.deposits*depositCost/10000*months/12;
    const credit=v.net_loans*creditCost/10000*months/12;
    const hit=(funding+credit)*(1-taxRate/100);
    return {funding,credit,nii:v.nii-funding,pretax:v.pretax-funding-credit,common:v.common_net-hit,hit};
  }
  function forecast(r,a,params){
    const v=r.values,p=params;
    for(const key of ["loanGrowth","depositGrowth","feeGrowth","expenseGrowth"])limits(p[key],-30,40,key+" (%)");
    limits(p.marginMove,-200,200,"Margin change (bp)");limits(p.creditMove,0,500,"Extra provision (bp)");
    limits(p.fundingRate,0,25,"Wholesale funding rate (%)");limits(p.riskWeight,0,200,"Incremental loan risk weight (%)");
    limits(p.payout,0,100,"Payout (%)");
    const year=Number(r.end.slice(0,4)),days=(Date.parse(r.end)-Date.UTC(year,0,1))/86400000+1;
    const factor=((Date.UTC(year+1,0,1)-Date.UTC(year,0,1))/86400000)/days;
    const margin=v.nii*factor/a.avg_earning_assets+p.marginMove/10000;
    const tax=v.tax/v.pretax, noncommon=(v.pretax-v.tax-v.common_net)*factor;
    let loans=v.net_loans,deposits=v.deposits,fees=v.fees_other*factor,expense=v.opex*factor;
    let wholesale=0,retained=0;const years=[];
    for(let y=1;y<=3;y++){
      const newLoans=loans*(1+p.loanGrowth/100),newDeposits=deposits*(1+p.depositGrowth/100);
      const avgLoans=(loans+newLoans)/2;
      const earningAssets=a.avg_earning_assets+avgLoans-v.net_loans;
      if(earningAssets<=0)throw Error("Forecast earning assets must remain positive.");
      const nii=margin*earningAssets-wholesale*p.fundingRate/100;
      const provision=avgLoans*(v.provisions*factor/v.net_loans+p.creditMove/10000);
      fees*=1+p.feeGrowth/100;expense*=1+p.expenseGrowth/100;
      const pretax=nii+fees-expense-provision, common=pretax-Math.max(pretax,0)*tax-noncommon;
      const payout=Math.max(common,0)*p.payout/100;retained+=common-payout;
      const fundingNeed=(newLoans-v.net_loans)-(newDeposits-v.deposits)-retained;
      wholesale=Math.max(0,fundingNeed);const liquidity=Math.max(0,-fundingNeed);
      const assets=v.assets+(newLoans-v.net_loans)+liquidity;
      const liabilities=v.liabilities+(newDeposits-v.deposits)+wholesale,equity=v.equity+retained;
      const difference=assets-liabilities-equity,rwa=a.rwa+(newLoans-v.net_loans)*p.riskWeight/100;
      if(rwa<=0 || Math.abs(difference)>1e-6)throw Error("Forward balance sheet or RWA check failed.");
      years.push({year:y,loans:newLoans,deposits:newDeposits,earningAssets,nii,fees,expense,provision,pretax,common,payout,wholesale,liquidity,assets,liabilities,equity,difference,rwa,cet1:(a.cet1+retained)/rwa*100});
      loans=newLoans;deposits=newDeposits;
    }
    return years;
  }
  const planDefaults={loanGrowth:3,depositGrowth:3,feeGrowth:2,expenseGrowth:2,marginMove:0,creditMove:0,fundingRate:5,riskWeight:80,payout:45};
  function merger(buyer,target,buyerEPS,targetEPS,exchangeRatio,synergyPerTargetShare,targetToBuyerShares){
    if(buyer.bank===target.bank||buyer.end!==target.end)throw Error("Choose distinct banks and a common date.");
    limits(exchangeRatio,0.001,20,"Exchange ratio");limits(synergyPerTargetShare,-50,50,"After-tax synergy per target share");
    if(!(buyerEPS>0)||!Number.isFinite(targetEPS)||!(targetToBuyerShares>0))throw Error("Positive buyer EPS and a valid share ratio are required.");
    const proForma=(buyerEPS+(targetEPS+synergyPerTargetShare)*targetToBuyerShares)/(1+exchangeRatio*targetToBuyerShares);
    const offer=exchangeRatio*referencePrice(buyer);
    return {proForma,accretion:(proForma/buyerEPS-1)*100,offer,premium:(offer/referencePrice(target)-1)*100};
  }
  function backtest(rows){
    const out=[];
    for(const r of rows.filter(r=>r.form==="10-K")){
      const prior=n=>rows.find(x=>x.bank===r.bank&&x.end===(Number(r.end.slice(0,4))-n)+"-12-31");
      const last=prior(1),earlier=prior(2);if(!last||!earlier||last.filed>=r.end)continue;
      const a=r.values.nii,b=last.values.nii,c=earlier.values.nii;if(![a,b,c].every(x=>Number.isFinite(x)&&x>0))continue;
      const forecast=b*(1+Math.max(-.15,Math.min(.15,b/c-1)));
      out.push({bank:r.bank,year:r.end.slice(0,4),input_filed:last.filed,prior_prior_source:earlier.source,prior_source:last.source,actual_source:r.source,forecast,actual:a,flat:b,error:forecast-a,flat_error:b-a});
    }
    return out;
  }
  return {fields,checks,scenario,defaults,forecast,planDefaults,earningsStress,multiples,merger,annualEPS,referencePrice,backtest};
})();
if(typeof module!=="undefined" && module.exports)module.exports=BankModel;

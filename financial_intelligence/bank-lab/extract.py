"""Build the public snapshot from locally cached SEC files (see README)."""
import argparse
import json
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from lxml import html

HERE = Path(__file__).resolve().parent
BANKS = {"JPM":19617, "BAC":70858, "C":831001, "WFC":72971}
# Each candidate must describe the same line and population.
FIELDS = {
    "assets":"Assets", "liabilities":"Liabilities",
    "equity":"StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest|StockholdersEquity",
    "deposits":"Deposits", "net_loans":"wfc:FinancingReceivableAndNetInvestmentInLeaseExcludingAccruedInterestAfterAllowanceForCreditLoss|FinancingReceivableExcludingAccruedInterestAfterAllowanceForCreditLoss",
    "interest_income":"InterestAndDividendIncomeOperating|InterestIncomeOperating", "interest_expense":"InterestExpenseOperating|InterestExpense",
    "nii":"InterestIncomeExpenseNet", "fees_other":"NoninterestIncome", "opex":"NoninterestExpense",
    "provisions":"c:ProvisionForCreditLossBenefitsAndClaimsExpenseReversal|bac:FinancingReceivableExcludingAccruedInterestAndOffBalanceSheetLiabilityCreditLossProvisionReversal|ProvisionForLoanLeaseAndOtherLosses",
    "pretax":"IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "tax":"IncomeTaxExpenseBenefit", "parent_net":"NetIncomeLoss",
    "continuing_net":"IncomeLossFromContinuingOperationsIncludingPortionAttributableToNoncontrollingInterest",
    "common_net":"NetIncomeLossAvailableToCommonStockholdersBasic", "eps":"EarningsPerShareDiluted",
    "diluted_shares":"WeightedAverageNumberOfDilutedSharesOutstanding", "cash":"CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    "cash_open":"CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    "change":"CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect",
    "operating":"NetCashProvidedByUsedInOperatingActivities","investing":"NetCashProvidedByUsedInInvestingActivities",
    "financing":"NetCashProvidedByUsedInFinancingActivities","fx":"EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
}
INSTANT = {"assets","liabilities","equity","deposits","net_loans","cash","cash_open"}
TAGS = {k:[t if ":" in t else "us-gaap:"+t for t in v.split("|")] for k,v in FIELDS.items()}
CITI_CASH = "us-gaap:CashAndCashEquivalentsAtCarryingValue"
CITI_FLOWS = {k:TAGS[k][0]+"ContinuingOperations" for k in ("operating","investing","financing")}
WANTED = {CITI_CASH,*CITI_FLOWS.values()} | {tag for tags in TAGS.values() for tag in tags}
def ix_facts(path, cik):
    """Read selected consolidated facts. Choose highest declared precision within a context."""
    doc=html.parse(str(path))
    contexts={}
    for ctx in doc.xpath('//*[name()="xbrli:context"]'):
        if ctx.xpath('.//*[name()="xbrli:segment" or name()="xbrli:scenario"]'): continue
        ident=ctx.xpath('.//*[name()="xbrli:identifier"]/text()')
        if not ident or int(ident[0]) != cik: continue
        parts={e.tag.split(":")[-1]:e.text for e in ctx.iter()}
        contexts[ctx.get("id")]=(parts.get("startdate"),parts.get("enddate") or parts["instant"])
    units={}
    for unit in doc.xpath('//*[name()="xbrli:unit"]'):
        measures=tuple(unit.xpath('.//*[name()="xbrli:measure"]/text()'))
        units[unit.get('id')]={('iso4217:USD',):'USD',('xbrli:shares',):'shares',('iso4217:USD','xbrli:shares'):'USD/shares'}.get(measures)
    result={}
    for e in doc.xpath('//*[name()="ix:nonfraction"]'):
        tag,context=e.get("name"),contexts.get(e.get("contextref"))
        if tag not in WANTED or not context or e.get("xsi:nil")=="true":continue
        unit=units.get(e.get("unitref"))
        if unit is None:continue
        raw="".join(e.itertext()).strip().replace(",","")
        if raw in {"—","–","-"}:raw="0"
        if not raw:continue
        value=Decimal(raw).scaleb(int(e.get("scale","0"))) * (-1 if e.get("sign")=="-" else 1)
        key=(tag,*context,unit)
        prec=e.get('decimals','0')
        precision=999 if prec.upper()=='INF' else int(prec)
        old=result.get(key)
        if old and precision==old[0] and value!=old[1]:
            raise ValueError(f"Conflicting equally precise inline facts in {path}: {key}")
        if old is None or precision>old[0]:result[key]=(precision,value)
    return {key:val for key,(_,val) in result.items()}

def build(cache, cutoff):
    output=[]; dictionary=[]
    for ticker,cik in BANKS.items():
        data=json.loads((cache/f'{ticker}.json').read_text())
        if data['cik']!=cik:raise ValueError(f"Unexpected CIK for {ticker}")
        gaap=data['facts']['us-gaap']; records=defaultdict(dict); filings={}
        for f in gaap['Assets']['units']['USD']:
            end=f['end']; yr=int(end[:4]); form=f['form']
            fp={'03-31':'Q1','06-30':'Q2','09-30':'Q3','12-31':'FY'}.get(end[5:])
            if yr<2016 or (f.get('fy')!=yr and f['accn']!='0000072971-17-000339') or f.get('fp')!=fp or form!=('10-K' if fp=='FY' else '10-Q') or f['filed']>cutoff:continue
            meta=(f['accn'],f['filed'],form)
            if end in filings and filings[end]!=meta:raise ValueError(f"Multiple original filings {ticker} {end}")
            filings[end]=meta
        # Some SEC companyfacts snapshots lag published inline submissions.
        for end,acc,filed in [('2026-03-31','0000831001-26-000019','2026-05-07'),('2026-06-30','0000831001-26-000045','2026-08-06'),('2026-09-30','0000831001-26-000056','2026-11-05')]:
            if ticker=='C' and filed<=cutoff:filings[end]=(acc,filed,'10-Q')
        accessions={v[0] for v in filings.values()}
        for tag in WANTED:
            ns,term=tag.split(':')
            for unit,series in data['facts'].get(ns,{}).get(term,{}).get('units',{}).items():
                for x in series:
                    if x['accn'] not in accessions:continue
                    key=(tag,x.get('start'),x['end'],unit)
                    value=Decimal(str(x['val']))
                    current=records[x['accn']].get(key)
                    if current is not None and current!=value:raise ValueError(f"Conflicting facts {key}")
                    records[x['accn']][key]=value
        for end,(acc,filed,form) in sorted(filings.items()):
            yr=int(end[:4]); start=f'{yr}-01-01'
            only_three=False
            extra=cache/f"{ticker}-{end}.htm"
            if extra.is_file():
                records[acc].update(ix_facts(extra,cik))
                if ticker=="WFC":
                    for table in html.parse(str(extra)).xpath("//table"):
                        fact_names={n.get("name") for n in table.xpath(".//*[@contextref]")}
                        required={TAGS[k][0] for k in ("operating","investing","financing","change")}
                        if required.issubset(fact_names) and "exchange rate" not in table.text_content().lower():only_three=True
            if end in ('2025-12-31','2026-09-30') or (ticker=='C' and yr==2026):
                name=f'{ticker}-{yr}.htm' if ticker!='C' or yr!=2026 else f'c-{end.replace("-","")}.htm'
                records[acc].update(ix_facts(cache/name,cik))
            values={}; tags={}
            for field,candidates in TAGS.items():
                period_start=None if field in INSTANT else start
                period_end=f'{yr-1}-12-31' if field=='cash_open' else end
                unit={'eps':'USD/shares','diluted_shares':'shares'}.get(field,'USD')
                if ticker=="C" and yr==2018 and field in ("cash","cash_open"):
                    candidates=[*candidates,CITI_CASH]
                if ticker=="C" and yr==2019 and field in CITI_FLOWS:
                    candidates=[*candidates,CITI_FLOWS[field]]
                for tag in candidates:
                    value=records[acc].get((tag,period_start,period_end,unit))
                    if value is None:continue
                    if tag not in dictionary:dictionary.append(tag)
                    values[field]=float(value if field=='eps' else value/1_000_000)
                    tags[field]=dictionary.index(tag);break
            output.append(dict(bank=ticker,end=end,filed=filed,form=form,accession=acc,cash_sections_only=only_three,
                source=f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace("-","")}/{acc}-index.htm',values=values,tags=tags))
    return dict(cutoff=cutoff,tag_dictionary=dictionary,filings=output)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("cache",type=Path);p.add_argument("--cutoff",default="2026-11-21");p.add_argument("--out",type=Path,default=HERE/"filings.json")
    a=p.parse_args();date.fromisoformat(a.cutoff)
    from supplement import enrich
    contents=json.dumps(enrich(build(a.cache,a.cutoff),a.cache/"reports"),separators=(',',':'),allow_nan=False)
    a.out.write_text(contents+'\n')

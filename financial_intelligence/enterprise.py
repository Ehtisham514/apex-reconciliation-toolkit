"""Auditable, streaming CSV ledger aggregation. Standard library only."""
import csv
import hashlib
from collections import defaultdict
from datetime import date
from decimal import Decimal
REQUIRED={'transaction_id','date','entity','project','account','amount','currency'}
def aggregate_csv(path, expected_currency='USD', max_errors=100):
    totals=defaultdict(Decimal); seen=set(); errors=[]; accepted=0
    digest=hashlib.sha256()
    with open(path,'rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''): digest.update(chunk)
    with open(path,newline='',encoding='utf-8-sig') as source:
        reader=csv.DictReader(source)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise ValueError('Missing required CSV columns')
        for line,row in enumerate(reader,2):
            try:
                key=row['transaction_id'].strip()
                if not key or key in seen: raise ValueError('Blank/duplicate ID')
                date.fromisoformat(row['date'])
                if row['currency'].strip().upper()!=expected_currency.upper(): raise ValueError('Currency mismatch')
                entity=row['entity'].strip(); account=row['account'].strip()
                if not entity or not account: raise ValueError('Missing entity/account')
                value=Decimal(row['amount'])
                if not value.is_finite(): raise ValueError('Non-finite amount')
                seen.add(key)
                totals[(entity,row['project'].strip(),account)]+=value
                accepted+=1
            except (ValueError,TypeError,ArithmeticError) as exc:
                errors.append({'line':line,'error':str(exc)})
                if len(errors)>=max_errors: raise ValueError('Too many invalid rows') from exc
    return {'sha256':digest.hexdigest(),'accepted_rows':accepted,'rejected_rows':len(errors),
            'errors':errors,'totals':[{'entity':e,'project':p,'account':a,'amount':str(v)}
            for (e,p,a),v in sorted(totals.items())]}

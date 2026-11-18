import csv
from financial_intelligence.enterprise import aggregate_csv

def test_streamed_totals_and_duplicates(tmp_path):
    p=tmp_path/'ledger.csv'
    with p.open('w',newline='') as f:
        w=csv.writer(f)
        w.writerow(['transaction_id','date','entity','project','account','amount','currency'])
        w.writerow(['a','2026-01-01','E','P','Cash','100.10','USD'])
        w.writerow(['b','2026-01-02','E','P','Cash','-25.05','USD'])
        w.writerow(['b','2026-01-02','E','P','Cash','999','USD'])
    r=aggregate_csv(p)
    assert r['accepted_rows']==2
    assert r['rejected_rows']==1
    assert r['totals'][0]['amount']=='75.05'

def test_rejects_currency_mismatch(tmp_path):
    p=tmp_path/'ledger.csv'
    p.write_text('transaction_id,date,entity,project,account,amount,currency\\na,2026-01-01,E,P,Cash,10,EUR\\n'.replace('\\n','\n'))
    r=aggregate_csv(p)
    assert r['accepted_rows']==0
    assert r['rejected_rows']==1

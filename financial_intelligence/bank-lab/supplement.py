"""Fill historical tag gaps from SEC-rendered statement rows in the same accession."""
from datetime import datetime
from pathlib import Path
import re
from openpyxl import load_workbook

def enrich(data, folder):
    dictionary=data['tag_dictionary']
    for r in data['filings']:
        path=Path(folder)/(r['bank']+'-'+r['end']+'.xlsx')
        if not path.is_file():continue
        book=load_workbook(path,read_only=True,data_only=True)
        end=datetime.strptime(r['end'],'%Y-%m-%d')
        for sheet in book.worksheets[:16]:
            rows=iter(sheet.values);headers=next(rows,())
            if not headers:continue
            title=str(headers[0]).lower()
            if 'consolidated' not in title or 'parenthetical' in title or '$ in millions' not in title:continue
            cash='cash flow' in title
            if not cash and 'statement of income' not in title and 'statements of income' not in title:continue
            dates=next(rows,());months=None;columns=[]
            for i in range(1,min(len(headers),len(dates))):
                m=re.fullmatch(r'(\d+) Months Ended',str(headers[i]),re.I)
                if m:months=int(m[1])
                try:dt=datetime.strptime(str(dates[i]).replace('.','').replace('Sept ','Sep '),'%b %d, %Y')
                except ValueError:continue
                if dt==end and months==end.month:columns.append(i)
            if len(columns)!=1:continue
            idx=columns[0]; candidates={}; has_fx=False
            for row in rows:
                if not row or not row[0]:continue
                label=' '.join(str(row[0]).lower().split()); k=None
                if cash:
                    if 'exchange rate' in label:has_fx=True
                    for field in ('operating','investing','financing'):
                        if label.startswith('net cash') and field+' activities' in label:k=field
                    if label.startswith('effect of exchange rate') and 'cash' in label:k='fx'
                    if re.match(r'(net )?(change|increase|decrease|\(decrease\)|\(increase\)).{0,26}in cash',label):k='change'
                    if label.startswith('cash') and re.search(r' (at |, )?(the )?beginning of| at january 1',label):k='cash_open'
                    if label.startswith('cash') and (re.search(r' (at |, )?(the )?end of (the )?(period|year)',label) or ' at '+end.strftime('%B %d').lower() in label):k='cash'
                else:
                    if label in ('provision for credit losses','total provisions for credit losses and for benefits and claims'):k='provisions'
                    if ('before income tax' in label or 'before taxes' in label) and label.startswith(('income','loss')):k='pretax'
                if k and idx<len(row) and type(row[idx]) in (float,int):
                    candidates.setdefault(k,[]).append((row[idx],str(row[0])))
            for k,choices in candidates.items():
                if k in r['values'] or len({v for v,_ in choices})!=1:continue
                value,label=choices[0];loc='Financial_Report.xlsx / '+sheet.title+' / '+label
                if loc not in dictionary:dictionary.append(loc)
                r['values'][k]=value;r['tags'][k]=dictionary.index(loc)
            if cash and r['bank']=='WFC' and not has_fx and all(k in candidates for k in ('operating','investing','financing','change')):
                r['cash_sections_only']=True
        book.close()
    return data

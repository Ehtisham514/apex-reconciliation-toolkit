"""Interactive prototype: pip install streamlit; streamlit run financial_intelligence/dashboard.py"""
import streamlit as st
from decimal import Decimal
try:
    from financial_intelligence.models import ConstructionLine,construction_estimate,cash_forecast,dcf,acquisition_case
    from financial_intelligence.enterprise import aggregate_csv
except ModuleNotFoundError:
    from models import ConstructionLine,construction_estimate,cash_forecast,dcf,acquisition_case
    from enterprise import aggregate_csv
st.set_page_config(page_title='Finance Intelligence Lab',layout='wide')
st.title('Finance Intelligence Lab')
st.caption('Illustrative only — not an audited estimate or investment recommendation. Do not upload confidential data to untrusted deployments.')
tab=st.sidebar.selectbox('Model',['Construction','13-week cash','DCF valuation','Acquisition','CSV aggregation'])
if tab=='Construction':
    q=st.number_input('Quantity',min_value=0.,value=100.)
    unit=st.number_input('Material unit cost',min_value=0.,value=120.)
    hours=st.number_input('Labor hours',min_value=0.,value=50.)
    wage=st.number_input('Hourly labor cost',min_value=0.,value=35.)
    waste=st.slider('Waste %',0,100,5)/100
    overhead=st.slider('Overhead %',0,100,10)/100
    contingency=st.slider('Contingency %',0,100,8)/100
    margin=st.slider('Target margin %',0,95,20)/100
    result=construction_estimate([ConstructionLine(*map(lambda x:Decimal(str(x)),[q,unit,hours,wage,waste]))],overhead,contingency,margin)
elif tab=='13-week cash':
    opening=st.number_input('Opening cash',value=100000.)
    receipts=st.number_input('Weekly receipts',value=30000.)
    payments=st.number_input('Weekly payments',value=35000.)
    minimum=st.number_input('Minimum cash',value=25000.)
    result=cash_forecast(opening,[receipts]*13,[payments]*13,minimum)
    st.line_chart({'Closing':[float(x['closing']) for x in result],'Funding gap':[float(x['funding_gap']) for x in result]})
elif tab=='DCF valuation':
    flows=st.text_input('Annual unlevered free cash flows','100000,120000,140000,160000,180000')
    rate=st.number_input('Discount rate (%)',value=12.,min_value=0.01)
    growth=st.number_input('Terminal growth (%)',value=3.)
    debt=st.number_input('Net debt',value=200000.)
    try: result=dcf([x.strip() for x in flows.split(',')],str(rate/100),str(growth/100),str(debt))
    except ValueError as exc: st.error(str(exc));st.stop()
elif tab=='Acquisition':
    ebitda=st.number_input('Target EBITDA',value=500000.)
    multiple=st.number_input('EBITDA multiple',value=5.,min_value=0.)
    debt=st.number_input('Acquisition debt',value=1000000.,min_value=0.)
    interest=st.number_input('Debt interest (%)',value=8.,min_value=0.)
    synergies=st.number_input('Annual synergies',value=100000.)
    integration=st.number_input('Integration cost',value=150000.,min_value=0.)
    try: result=acquisition_case(ebitda,multiple,debt,str(interest/100),synergies,integration)
    except ValueError as exc: st.error(str(exc));st.stop()
else:
    upload=st.file_uploader('Upload CSV with transaction_id,date,entity,project,account,amount,currency',type='csv')
    if upload is None: st.stop()
    import tempfile,os
    with tempfile.NamedTemporaryFile(suffix='.csv',delete=False) as f:
        f.write(upload.getvalue()); name=f.name
    try: result=aggregate_csv(name)
    finally: os.unlink(name)
if isinstance(result,dict):
    st.json({k:str(v) if isinstance(v,Decimal) else v for k,v in result.items()})
else:
    st.dataframe([{k:str(v) for k,v in row.items()} for row in result],hide_index=True)

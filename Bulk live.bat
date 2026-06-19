@echo off
cd /d "D:\TradeNepse\Bulk live market"
start "" streamlit run app.py
timeout /t 5
start "" http://localhost:8501
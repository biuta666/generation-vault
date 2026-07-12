@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Starting Generation Vault...
python -m streamlit run src/ui/app.py --server.port 8501 --server.headless true
pause

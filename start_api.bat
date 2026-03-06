@echo off
REM ══════════════════════════════════════════════════════════════
REM Yorglass IK Chatbot API - Baslatma Scripti
REM ══════════════════════════════════════════════════════════════
REM Bu dosya dogrudan cift tiklayarak veya Windows Servisi
REM olarak calistirmak icin kullanilir.
REM ══════════════════════════════════════════════════════════════

cd /d "%~dp0"
echo [%date% %time%] IK Chatbot API baslatiliyor...
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000
pause

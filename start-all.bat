@echo off
title SI PERKARA - Semua Server (Backend + Web)
echo ============================================
echo  Menjalankan Backend LangChain + Web Next.js
echo  Backend: http://localhost:8000/health
echo  Web    : http://localhost:3000
echo ============================================
cd /d "%~dp0"
start "SI PERKARA - Backend" cmd /k start-backend.bat
timeout /t 5 /nobreak >nul
start "SI PERKARA - Web" cmd /k start-app.bat
echo Kedua server dijalankan di jendela terpisah.
pause

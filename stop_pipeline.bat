@echo off
echo 🛑 Shutting down EV Battery Pipeline...

:: Force kill all running Python processes (Publisher & Subscriber)
taskkill /F /IM python.exe /T >nul 2>&1

:: Force kill Streamlit (Dashboard)
taskkill /F /IM streamlit.exe /T >nul 2>&1

echo ✅ All terminals stopped and reset.
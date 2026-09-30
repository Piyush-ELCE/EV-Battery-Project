@echo off
echo 🚀 Starting EV Battery Pipeline...

echo [1/4] Starting InfluxDB Server...
:: Opens a new window and runs InfluxDB
start "InfluxDB" cmd /k "C:\Program Files\InfluxData\influxdb2_windows_amd64\influxd.exe"
:: Give the database 3 seconds to fully boot up
timeout /t 3 /nobreak >nul

echo [2/4] Starting MQTT Subscriber (ML Engine)...
start "Subscriber" cmd /k "python 2_subscriber.py"
timeout /t 2 /nobreak >nul

echo [3/4] Starting MQTT Publisher (Data Generator)...
start "Publisher" cmd /k "python 3_publisher.py"
timeout /t 2 /nobreak >nul

echo [4/4] Starting Streamlit Dashboard...
start "Dashboard" cmd /k "streamlit run 4_dashboard.py"

echo ✅ All systems launched!
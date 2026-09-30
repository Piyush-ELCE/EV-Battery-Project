@echo off
echo Starting EV Battery Intelligence Pipeline...
echo ===========================================

:: 1. Start the Subscriber in a new terminal window
echo [1/3] Starting MQTT Subscriber & ML Engine...
start "Subscriber (ML & DB)" cmd /k "python 2_subscriber.py"

:: Wait 2 seconds to give the subscriber time to connect to HiveMQ
timeout /t 2 /nobreak > nul

:: 2. Start the Publisher in a new terminal window
echo [2/3] Starting Sensor Telemetry Publisher...
start "Publisher (Edge Device)" cmd /k "python 3_publisher.py"

:: Wait 2 seconds before launching the UI
timeout /t 2 /nobreak > nul

:: 3. Start the Streamlit Dashboard in the current window
echo [3/3] Launching Streamlit Dashboard...
streamlit run 4_dashboard.py
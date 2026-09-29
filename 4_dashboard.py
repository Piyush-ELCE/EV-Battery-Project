import streamlit as st
import json
import time

# Set up the webpage layout
st.set_page_config(page_title="EV Battery Dashboard", layout="wide")
st.title("🔋 EV Battery Live Telemetry")
st.markdown("Real-time monitoring of IoT edge node data.")

# Create an empty container that we will overwrite every second
placeholder = st.empty()

# Infinite loop to keep the dashboard updating
while True:
    try:
        # Read the latest data saved by the subscriber
        with open("latest_telemetry.json", "r") as f:
            data = json.load(f)

        # Draw the UI inside the placeholder
        with placeholder.container():
            # Top row of metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Temperature", f"{data['cell_temp_C']} °C")
            col2.metric("Voltage", f"{data['voltage_V']} V")
            col3.metric("Current", f"{data['current_A']} A")
            col4.metric("SOC", f"{data['soc_percent']} %")

            st.divider()

            # Bottom row of metrics
            col5, col6, col7 = st.columns(3)
            col5.metric("Internal Resistance", f"{data['resistance_ohms']} Ω")
            col6.metric("Capacity", f"{data['capacity_Ah']} Ah")
            col7.metric("Ambient Temp", f"{data['ambient_temp_C']} °C")

            # Visual Anomaly Warning
            if data['cell_temp_C'] > 35.0:  # Adjust threshold as needed
                st.error("🔥 THERMAL ANOMALY DETECTED: Cell temperature exceeds safe operating limits!")
            
            if data['resistance_ohms'] > 0.025:
                st.warning("⚠️ DEGRADATION WARNING: Internal resistance spiking.")

    except (FileNotFoundError, json.JSONDecodeError):
        with placeholder.container():
            st.info("Waiting for telemetry data... Please start 2_subscriber.py and 3_publisher.py.")
    
    # Wait 1 second before refreshing the screen
    time.sleep(1)
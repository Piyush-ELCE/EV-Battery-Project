import streamlit as st
import pandas as pd
import json
import time

st.set_page_config(page_title="EV Battery Dashboard", layout="wide")
st.title("🔋 EV Battery Live Telemetry")
st.markdown("Real-time monitoring with historical trend tracking.")

# Create the container we will refresh every second
placeholder = st.empty()

# Initialize a Pandas DataFrame to store the last 60 readings
MAX_HISTORY = 60
history_df = pd.DataFrame(columns=["Temperature (°C)", "Current (A)"])

while True:
    try:
        with open("latest_telemetry.json", "r") as f:
            data = json.load(f)

        # 1. Add the newest reading to our history table
        new_row = pd.DataFrame({
            "Temperature (°C)": [data['cell_temp_C']],
            "Current (A)": [data['current_A']]
        })
        # Append new data and drop the oldest if we exceed 60 seconds
        history_df = pd.concat([history_df, new_row], ignore_index=True)
        if len(history_df) > MAX_HISTORY:
            history_df = history_df.tail(MAX_HISTORY)

        # 2. Draw the UI
        with placeholder.container():
            # Top row metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Temperature", f"{data['cell_temp_C']} °C")
            col2.metric("Voltage", f"{data['voltage_V']} V")
            col3.metric("Current", f"{data['current_A']} A")
            col4.metric("SOC", f"{data['soc_percent']} %")

            st.divider()

            # Live Scrolling Charts
            st.subheader("Live Trends (Rolling 60 Seconds)")
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.markdown("**Cell Temperature**")
                st.line_chart(history_df["Temperature (°C)"])
                
            with chart_col2:
                st.markdown("**Current Draw**")
                st.line_chart(history_df["Current (A)"])

            st.divider()

            # Bottom row metrics
            col5, col6, col7 = st.columns(3)
            col5.metric("Internal Resistance", f"{data['resistance_ohms']} Ω")
            col6.metric("Capacity", f"{data['capacity_Ah']} Ah")
            col7.metric("Ambient Temp", f"{data['ambient_temp_C']} °C")

            # Alerts
            if data['cell_temp_C'] > 35.0:
                st.error("🔥 THERMAL ANOMALY DETECTED: Cell temperature exceeds safe operating limits!")
            if data['resistance_ohms'] > 0.025:
                st.warning("⚠️ DEGRADATION WARNING: Internal resistance spiking.")

    except (FileNotFoundError, json.JSONDecodeError):
        with placeholder.container():
            st.info("Waiting for telemetry data... Please start 2_subscriber.py and 3_publisher.py.")
    
    time.sleep(1)
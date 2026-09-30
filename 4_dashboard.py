import streamlit as st
import pandas as pd
import time
from influxdb_client import InfluxDBClient

# --- InfluxDB Setup ---
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "I_75MjVFDIXG_0P7XyeBpxMKTcJbSIDT3n8mcLSxMMSwv0qy0UefDmmNNO98AJFPBAfu-OyoqF_2AjlDe_jDRA=="
INFLUX_ORG = "EV_Project"
INFLUX_BUCKET = "battery_telemetry"

# Connect to the database
client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG, timeout=10000)
query_api = client.query_api()

st.set_page_config(page_title="EV Battery Dashboard", layout="wide")
st.title("🔋 EV Battery Live Telemetry")
st.markdown("Real-time monitoring pulling directly from **InfluxDB**.")

placeholder = st.empty()

# Flux query: "Go to the bucket, grab the last 2 minutes of data, and format it into a table"
flux_query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -2m)
  |> filter(fn: (r) => r["_measurement"] == "battery_status")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
'''

while True:
    try:
        # Fetch data from InfluxDB as a Pandas DataFrame
        df = query_api.query_data_frame(flux_query)

        # InfluxDB sometimes returns a list of DataFrames; we just want the first one
        if type(df) is list and len(df) > 0:
            df = df[0]
        elif type(df) is list:
            df = pd.DataFrame()

        if not df.empty:
            # Sort chronologically
            df = df.sort_values(by="_time")
            
            # Get the absolute latest row for the top metric numbers
            latest = df.iloc[-1]

            with placeholder.container():
                # Top row metrics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Temperature", f"{latest['cell_temp_C']:.2f} °C")
                col2.metric("Voltage", f"{latest['voltage_V']:.3f} V")
                col3.metric("Current", f"{latest['current_A']:.2f} A")
                col4.metric("SOC", f"{latest['soc_percent']:.1f} %")

                st.divider()

                # Live Scrolling Charts using the _time column for the X-axis
                st.subheader("Live Trends (Last 2 Minutes)")
                chart_df = df.set_index("_time")
                
                chart_col1, chart_col2 = st.columns(2)
                with chart_col1:
                    st.markdown("**Cell Temperature (°C)**")
                    st.line_chart(chart_df["cell_temp_C"])
                with chart_col2:
                    st.markdown("**Current Draw (A)**")
                    st.line_chart(chart_df["current_A"])

                st.divider()

                # Bottom row metrics
                col5, col6, col7 = st.columns(3)
                col5.metric("Internal Resistance", f"{latest['resistance_ohms']:.4f} Ω")
                col6.metric("Capacity", f"{latest['capacity_Ah']:.1f} Ah")
                col7.metric("Ambient Temp", f"{latest['ambient_temp_C']:.2f} °C")

                # Alerts
                if latest['cell_temp_C'] > 35.0:
                    st.error("🔥 THERMAL ANOMALY DETECTED: Cell temperature exceeds safe limits!")
                if latest['resistance_ohms'] > 0.025:
                    st.warning("⚠️ DEGRADATION WARNING: Internal resistance spiking.")
        else:
            with placeholder.container():
                st.info("No data found in the last 2 minutes. Start 3_publisher.py to send data.")

    except Exception as e:
        with placeholder.container():
            st.error(f"Error querying InfluxDB: {e}")
    
    # Pause for 2 seconds to avoid spamming the database
    time.sleep(2)
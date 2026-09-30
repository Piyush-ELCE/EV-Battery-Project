import streamlit as st
import pandas as pd
import time
from influxdb_client import InfluxDBClient

# --- 1. Page Configuration (Must be first) ---
st.set_page_config(page_title="EV Battery Command Center", layout="wide", initial_sidebar_state="collapsed")

# Inject Custom CSS to remove top whitespace so scrolling isn't needed
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    h1 { margin-bottom: 0rem; padding-bottom: 0rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. InfluxDB Setup ---
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "I_75MjVFDIXG_0P7XyeBpxMKTcJbSIDT3n8mcLSxMMSwv0qy0UefDmmNNO98AJFPBAfu-OyoqF_2AjlDe_jDRA=="
INFLUX_ORG = "EV_Project"
INFLUX_BUCKET = "battery_telemetry"

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG, timeout=10000)
query_api = client.query_api()

# Header
st.title("🔋 EV Battery Command Center")
placeholder = st.empty()

# Flux Query
flux_query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -2m)
  |> filter(fn: (r) => r["_measurement"] == "battery_status")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
'''

while True:
    try:
        df = query_api.query_data_frame(flux_query)

        if isinstance(df, list) and len(df) > 0:
            df = df[0]
        elif isinstance(df, list):
            df = pd.DataFrame()

        if not df.empty:
            df = df.sort_values(by="_time")
            
            # Get current and previous rows for live 'delta' arrows
            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else latest

            with placeholder.container():
                # --- AI ALERT BANNER ---
                is_ml_anomaly = bool(latest.get("ml_anomaly", False))
                if is_ml_anomaly:
                    st.error("🚨 **AI ANOMALY DETECTED:** Multi-variable behavioral mismatch in Isolation Forest model.")
                else:
                    st.success("✅ **SYSTEM NORMAL:** AI confirms parameters are operating securely.")

                # --- THE HUD (Heads Up Display) 7-COLUMN ROW ---
                c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
                
                # Metric 1: Temp (Inverted delta color so hotter = red)
                temp_diff = latest['cell_temp_C'] - previous['cell_temp_C']
                c1.metric("Cell Temp", f"{latest['cell_temp_C']:.1f} °C", f"{temp_diff:.2f} °C", delta_color="inverse")
                
                # Metric 2: Voltage
                volt_diff = latest['voltage_V'] - previous['voltage_V']
                c2.metric("Voltage", f"{latest['voltage_V']:.2f} V", f"{volt_diff:.2f} V")
                
                # Metric 3: Current
                curr_diff = latest['current_A'] - previous['current_A']
                c3.metric("Current", f"{latest['current_A']:.1f} A", f"{curr_diff:.1f} A", delta_color="off")
                
                # Metric 4: State of Charge
                soc_diff = latest['soc_percent'] - previous['soc_percent']
                c4.metric("Charge (SOC)", f"{latest['soc_percent']:.1f} %", f"{soc_diff:.2f} %")
                
                # Metric 5: Resistance
                res_diff = latest['resistance_ohms'] - previous['resistance_ohms']
                c5.metric("Resistance", f"{latest['resistance_ohms']:.4f} Ω", f"{res_diff:.4f} Ω", delta_color="inverse")
                
                # Metric 6: Capacity
                c6.metric("Capacity", f"{latest['capacity_Ah']:.1f} Ah")
                
                # Metric 7: Ambient Temp
                c7.metric("Ambient Temp", f"{latest['ambient_temp_C']:.1f} °C")

                st.divider()

                # --- COMPACT LIVE CHARTS ---
                chart_df = df.set_index("_time")
                g1, g2, g3 = st.columns(3)
                
                with g1:
                    st.caption("📈 Thermal Trend (°C)")
                    # height=200 keeps the charts short and prevents scrolling
                    st.line_chart(chart_df["cell_temp_C"], height=200)
                
                with g2:
                    st.caption("⚡ Power Draw (Amps)")
                    st.line_chart(chart_df["current_A"], height=200)
                    
                with g3:
                    st.caption("🤖 AI Anomaly Triggers")
                    if "ml_anomaly" in chart_df.columns:
                        st.area_chart(chart_df["ml_anomaly"].astype(int), height=200)

                # --- EMERGENCY HARD ALERTS ---
                if latest['cell_temp_C'] > 35.0:
                    st.warning("🔥 **CRITICAL LIMIT:** Cell temperature breached 35°C threshold!")
                if latest['resistance_ohms'] > 0.025:
                    st.warning("⚠️ **HARDWARE WARNING:** High internal resistance detected.")

        else:
            with placeholder.container():
                st.info("Awaiting telemetry stream... Please start `3_publisher.py`.")

    except Exception as e:
        with placeholder.container():
            st.error(f"Database connection error: {e}")

    time.sleep(1.5)
import streamlit as st
import pandas as pd
import re
import datetime
import os
from influxdb_client_3 import InfluxDBClient3

# --- 1. Page Configuration (Must be first) ---
st.set_page_config(page_title="EV Battery Command Center", layout="wide", initial_sidebar_state="collapsed")

# --- 2. Authentication Gatekeeper (Username & Email) ---
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""

if not st.session_state["logged_in"]:
    st.markdown("""
        <style>
        .block-container { max-width: 500px; padding-top: 5rem; }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("👋 Welcome")
    st.caption("Please register your session to access live telemetry.")

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="e.g. Piyush")
        email = st.text_input("Email Address", placeholder="e.g. piyush@example.com")
        
        submitted = st.form_submit_button("Proceed to Dashboard", use_container_width=True)

        if submitted:
            if not username.strip():
                st.error("❌ Username cannot be empty.")
            elif not email.strip():
                st.error("❌ Email Address cannot be empty.")
            elif not is_valid_email(email):
                st.error("❌ Please enter a valid email address.")
            else:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username.strip()
                st.rerun() 

    st.stop() 


# --- 3. Authenticated Session Setup & Custom UI ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    h1 { margin-bottom: 0rem; padding-bottom: 0rem; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.success(f"Active Session: {st.session_state['username']}")
    if st.button("Log Out", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()

# --- 4. InfluxDB Setup ---
INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_ORG = "piyushkny2006@gmail.com"
INFLUX_DATABASE = "battery_telemetry" 

# Secure Credentials Logic
try:
    INFLUX_TOKEN = st.secrets["INFLUX_TOKEN"]
except (FileNotFoundError, KeyError):
    INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
    
if not INFLUX_TOKEN:
    st.error("Missing Database Credentials. Please set INFLUX_TOKEN in Streamlit secrets or OS environment.")
    st.stop()

# Initialize Client with DNS fallback
client = InfluxDBClient3(
    host=INFLUX_URL, 
    token=INFLUX_TOKEN, 
    org=INFLUX_ORG, 
    database=INFLUX_DATABASE,
    flight_client_options={"tls_roots": None}
)

st.title("🔋 EV Battery Command Center")

sql_query = "SELECT * FROM battery_status ORDER BY time DESC LIMIT 120"

# --- 5. Live Telemetry (Optimized to stop flickering) ---
@st.fragment(run_every=4) 
def live_telemetry():
    
    ui_scaffold = st.container(height=700, border=False) 
    
    with ui_scaffold:
        try:
            df = client.query(query=sql_query, mode="pandas")

            if not df.empty:
                df = df.sort_values(by="time")
                
                latest = df.iloc[-1]
                previous = df.iloc[-2] if len(df) > 1 else latest

                # --- OFFLINE / ONLINE STATUS CHECK ---
                now_utc = pd.Timestamp.utcnow()
                latest_time = pd.to_datetime(latest['time'])
                if latest_time.tzinfo is None:
                     latest_time = latest_time.tz_localize('UTC')
                
                time_diff = (now_utc - latest_time).total_seconds()

                if time_diff > 20:
                    st.warning(f"🟡 **SENSORS OFFLINE:** Live feed disconnected. Viewing last known historical telemetry from {latest_time.strftime('%b %d, %H:%M:%S')} UTC.")
                else:
                    st.success("🟢 **LIVE SENSORS ACTIVE:** Receiving real-time MQTT telemetry.")

                # --- AI ALERT BANNER ---
                is_ml_anomaly = bool(latest.get("ml_anomaly", False))
                if is_ml_anomaly:
                    st.error("🚨 **AI ANOMALY DETECTED:** Multi-variable behavioral mismatch in Isolation Forest model.")

                # --- THE HUD ---
                c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
                
                temp_diff = latest['cell_temp_C'] - previous['cell_temp_C']
                c1.metric("Cell Temp", f"{latest['cell_temp_C']:.1f} °C", f"{temp_diff:.2f} °C", delta_color="inverse")
                
                volt_diff = latest['voltage_V'] - previous['voltage_V']
                c2.metric("Voltage", f"{latest['voltage_V']:.2f} V", f"{volt_diff:.2f} V")
                
                curr_diff = latest['current_A'] - previous['current_A']
                c3.metric("Current", f"{latest['current_A']:.1f} A", f"{curr_diff:.1f} A", delta_color="off")
                
                soc_diff = latest['soc_percent'] - previous['soc_percent']
                c4.metric("Charge (SOC)", f"{latest['soc_percent']:.1f} %", f"{soc_diff:.2f} %")
                
                res_diff = latest['resistance_ohms'] - previous['resistance_ohms']
                c5.metric("Resistance", f"{latest['resistance_ohms']:.4f} Ω", f"{res_diff:.4f} Ω", delta_color="inverse")
                
                c6.metric("Capacity", f"{latest['capacity_Ah']:.1f} Ah")
                c7.metric("Ambient Temp", f"{latest['ambient_temp_C']:.1f} °C")

                st.divider()

                # --- COMPACT LIVE CHARTS ---
                chart_df = df.set_index("time") 
                g1, g2, g3 = st.columns(3)
                
                with g1:
                    st.caption("📈 Thermal Trend (°C)")
                    st.line_chart(chart_df["cell_temp_C"], height=200)
                
                with g2:
                    st.caption("⚡ Power Draw (Amps)")
                    st.line_chart(chart_df["current_A"], height=200)
                    
                with g3:
                    st.caption("🤖 AI Anomaly Triggers")
                    if "ml_anomaly" in chart_df.columns:
                        st.area_chart(chart_df["ml_anomaly"].astype(int), height=200)

                # --- EMERGENCY HARD ALERTS ---
                if latest['cell_temp_C'] > 45.0:
                    st.warning("🔥 **CRITICAL LIMIT:** Cell temperature breached 45°C threshold!")
                if latest['resistance_ohms'] > 0.025:
                    st.warning("⚠️ **HARDWARE WARNING:** High internal resistance detected.")

            else:
                st.info("Awaiting telemetry stream... Please start `3_publisher.py`.")

        except Exception as e:
            st.error(f"Database connection error: {e}")

# Start the background refresh loop
live_telemetry()
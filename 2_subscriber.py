import paho.mqtt.client as mqtt
import json
import influxdb_client
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- InfluxDB Setup ---
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "OzrxMb97pmcfpX1wmoCN5issMFZMltUXRsxzB5UcvHcA6MSzg5do8XvKSSMMoGNpKco8MJ1D_-NQJ2Q8nDbX5g==" # <--- Update this!
INFLUX_ORG = "EV_Project"
INFLUX_BUCKET = "battery_telemetry"

# Connect to the database
db_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = db_client.write_api(write_options=SYNCHRONOUS)
# ----------------------

# Set your anomaly thresholds
TEMP_DELTA_THRESHOLD = 0.5
RESISTANCE_DELTA_THRESHOLD = 0.01
last_temp = None
last_resistance = None

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[CONNECTED] Successfully linked to broker.")
        client.subscribe("piyush/ev/project/battery1")
        print("[SUBSCRIBED] Listening for live data...")

def on_message(client, userdata, msg):
    global last_temp, last_resistance

    try:
        raw_text = msg.payload.decode("utf-8")
        payload = json.loads(raw_text)

        # 1. Package the data for InfluxDB
        point = (
            Point("battery_status")
            .field("voltage_V", payload['voltage_V'])
            .field("current_A", payload['current_A'])
            .field("cell_temp_C", payload['cell_temp_C'])
            .field("ambient_temp_C", payload['ambient_temp_C'])
            .field("soc_percent", payload['soc_percent'])
            .field("resistance_ohms", payload['resistance_ohms'])
            .field("capacity_Ah", payload['capacity_Ah'])
        )

        # 2. Write it permanently to the database!
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        
        # (Keep saving the JSON file temporarily so your Streamlit dashboard doesn't crash)
        with open("latest_telemetry.json", "w") as f:
            json.dump(payload, f)

        # 3. Terminal Printing & Anomaly Logic
        current_temp = payload['cell_temp_C']
        current_res = payload['resistance_ohms']
        temp_delta = (current_temp - last_temp) if last_temp else 0.0
        res_delta = (current_res - last_resistance) if last_resistance else 0.0
        last_temp, last_resistance = current_temp, current_res

        anomaly_flags = []
        if temp_delta > TEMP_DELTA_THRESHOLD:
            anomaly_flags.append(f"🔥 TEMP SPIKE (+{temp_delta:.2f}°C)")
        if res_delta > RESISTANCE_DELTA_THRESHOLD:
            anomaly_flags.append(f"⚠️ RESISTANCE JUMP (+{res_delta:.4f}Ω)")

        print(f"--> [DB SAVED] Temp: {current_temp}°C | Res: {current_res}Ω")
        if anomaly_flags:
            print(f"[ANOMALY] {' | '.join(anomaly_flags)}\n" + "-"*40)

    except Exception as e:
        print(f"[ERROR] Could not process message: {e}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="My_Anomaly_Detector")
client.on_connect = on_connect
client.on_message = on_message

# Ensure this matches where your publisher is sending data (localhost or broker.hivemq.com)
client.connect("broker.hivemq.com", 1883, keepalive=60) 
client.loop_forever()
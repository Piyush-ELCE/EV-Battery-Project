import paho.mqtt.client as mqtt
import json
import influxdb_client
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import joblib
import numpy as np
import warnings

# Suppress scikit-learn version warnings for clean terminal output
warnings.filterwarnings("ignore", category=UserWarning)

# --- Load the ML Model ---
print("Loading ML Model...")
ml_model = joblib.load("isolation_forest_model.pkl")
print("✅ Model loaded!")

# --- InfluxDB Setup ---
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "I_75MjVFDIXG_0P7XyeBpxMKTcJbSIDT3n8mcLSxMMSwv0qy0UefDmmNNO98AJFPBAfu-OyoqF_2AjlDe_jDRA==" 
INFLUX_ORG = "EV_Project"
INFLUX_BUCKET = "battery_telemetry"

db_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = db_client.write_api(write_options=SYNCHRONOUS)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[CONNECTED] Linked to broker.")
        client.subscribe("piyush/ev/project/battery1")
        print("[SUBSCRIBED] Listening for live data...\n")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))

        # 1. Prepare data exactly as the ML model was trained
        live_features = np.array([[
            payload['voltage_V'], payload['current_A'], payload['cell_temp_C'],
            payload['ambient_temp_C'], payload['soc_percent'], payload['resistance_ohms'],
            payload['capacity_Ah']
        ]])

        # 2. Ask the model: Normal (1) or Anomaly (-1)?
        prediction = ml_model.predict(live_features)[0]
        ml_anomaly_detected = True if prediction == -1 else False

        # 3. Package and save everything to InfluxDB
        point = (
            Point("battery_status")
            .field("voltage_V", payload['voltage_V'])
            .field("current_A", payload['current_A'])
            .field("cell_temp_C", payload['cell_temp_C'])
            .field("ambient_temp_C", payload['ambient_temp_C'])
            .field("soc_percent", payload['soc_percent'])
            .field("resistance_ohms", payload['resistance_ohms'])
            .field("capacity_Ah", payload['capacity_Ah'])
            .field("ml_anomaly", ml_anomaly_detected) # <--- New ML Field!
        )
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

        # 4. Terminal Output
        output = f"--> Temp: {payload['cell_temp_C']}°C | Res: {payload['resistance_ohms']}Ω"
        
        if ml_anomaly_detected:
            print(f"🤖 [ML ISOLATION TRIGGERED] Complex anomaly detected!")
            print(output + " << WARNING")
            print("-" * 60)
        else:
            print(output)

    except Exception as e:
        print(f"[ERROR] {e}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="My_Anomaly_Detector")
client.on_connect = on_connect
client.on_message = on_message
client.connect("broker.hivemq.com", 1883, keepalive=60) 
client.loop_forever()
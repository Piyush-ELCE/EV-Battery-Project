import paho.mqtt.client as mqtt
import json
from influxdb_client_3 import InfluxDBClient3, Point # Updated for v3
import joblib
import numpy as np
import warnings
import ssl

# Suppress scikit-learn version warnings for clean terminal output
warnings.filterwarnings("ignore", category=UserWarning)

# --- Load the ML Model ---
print("Loading ML Model...")
ml_model = joblib.load("isolation_forest_model.pkl")
print("✅ Model loaded!")

# --- InfluxDB Cloud v3 Setup ---
# FIXED URL: Removed the /orgs/... path at the end. It must just be the host.
INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com" 
INFLUX_TOKEN = "DKTio2fVRp9gxTKY7JXiASZdodFQ4oj5WBTDcM9ReH7hEAJ2gBJDne6cbrhGHf-9AhFBNLcNjyFCi7lnfTPCrg==" 
INFLUX_ORG = "piyushkny2006@gmail.com"
INFLUX_DATABASE = "battery_telemetry"  # v3 uses "database" instead of "bucket"

# Initialize the v3 Serverless client
db_client = InfluxDBClient3(host=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG, database=INFLUX_DATABASE)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[CONNECTED] Linked to broker.")
        client.subscribe("piyush/ev/project/battery1")
        print("[SUBSCRIBED] Listening for live data...\n")
    else:
        print(f"\n❌ [CONNECTION FAILED] Reason Code: {rc}")

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
            .field("voltage_V", float(payload['voltage_V']))
            .field("current_A", float(payload['current_A']))
            .field("cell_temp_C", float(payload['cell_temp_C']))
            .field("ambient_temp_C", float(payload['ambient_temp_C']))
            .field("soc_percent", float(payload['soc_percent']))
            .field("resistance_ohms", float(payload['resistance_ohms']))
            .field("capacity_Ah", float(payload['capacity_Ah']))
            .field("ml_anomaly", ml_anomaly_detected) 
        )
        
        # v3 Write command (much simpler!)
        db_client.write(record=point)

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

# --- HiveMQ Cloud Secure Connection ---
client.username_pw_set("piyush", "12345678")
client.tls_set(tls_version=ssl.PROTOCOL_TLS)
client.connect("60b7caa4a2af419a9ac318f17098d27c.s1.eu.hivemq.cloud", 8883, keepalive=60)
client.loop_forever()
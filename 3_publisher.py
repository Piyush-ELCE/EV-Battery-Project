import paho.mqtt.client as mqtt
import pandas as pd
import json
import time
import ssl

# 1. Load the generated CSV file
try:
    df = pd.read_csv("battery_telemetry.csv")
    print(f"[LOADED] Found battery_telemetry.csv with {len(df)} rows.")
except FileNotFoundError:
    print("[ERROR] 'battery_telemetry.csv' not found. Run 1_generate_csv.py first!")
    exit()

# 2. Setup the MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="My_Virtual_ESP32")

print("[INFO] Connecting to local Mosquitto broker...")
try:
    # --- HiveMQ Cloud Secure Connection ---
    # 1. Set your username and password
    client.username_pw_set("piyush", "12345678")

    # 2. Enable secure TLS/SSL encryption
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)

    # 3. Connect to your specific Cluster URL on Port 8883
    # Replace the URL below with your actual Cluster URL!
    client.connect("60b7caa4a2af419a9ac318f17098d27c.s1.eu.hivemq.cloud", 8883, keepalive=60)
except ConnectionRefusedError:
    print("\n[CRITICAL ERROR] Connection refused! Mosquitto is not running.")
    print("Fix: Start Mosquitto Broker service before publishing.")
    exit()

client.loop_start()  # Starts a background thread to handle network traffic
print("[STARTED] Streaming data row-by-row (1 row per second)...\n")

# 3. Stream data row by row
for index, row in df.iterrows():
    payload = {
        "timestamp": int(row["timestamp"]),
        "voltage_V": float(row["voltage_V"]),
        "current_A": float(row["current_A"]),
        "cell_temp_C": float(row["cell_temp_C"]),
        "ambient_temp_C": float(row["ambient_temp_C"]),
        "soc_percent": float(row["soc_percent"]),
        "resistance_ohms": float(row["resistance_ohms"]),
        "capacity_Ah": float(row["remaining_capacity_Ah"])
    }

    # Convert Python dictionary into JSON string
    json_payload = json.dumps(payload)

    # Publish to the topic
    client.publish("piyush/ev/project/battery1", json_payload)
    print(f"<-- Published row {index + 1}/{len(df)}: {json_payload}")

    time.sleep(1)  # 1-second delay between readings

print("\n[FINISHED] All data from CSV has been transmitted.")
client.loop_stop()
client.disconnect()
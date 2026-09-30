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
    client.connect("localhost", 1883, keepalive=60)
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
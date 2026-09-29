import paho.mqtt.client as mqtt
import json

# Callback triggered when successfully connected to the broker
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[CONNECTED] Successfully linked to local Mosquitto broker.")
        # Subscribe to topic immediately after connecting
        client.subscribe("ev/battery/telemetry")
        print("[SUBSCRIBED] Listening on 'ev/battery/telemetry'. Waiting for live data...\n")
    else:
        print(f"[ERROR] Connection failed with code: {rc}")

# Callback triggered whenever a message arrives
def on_message(client, userdata, msg):
    try:
        # Decode binary MQTT payload into JSON
        raw_text = msg.payload.decode("utf-8")
        payload = json.loads(raw_text)

        # Print the incoming values
        print(
            f"--> Live Telemetry | "
            f"Temp: {payload['cell_temp_C']}°C (Amb: {payload['ambient_temp_C']}°C) | "
            f"Volt: {payload['voltage_V']}V | "
            f"Current: {payload['current_A']}A | "
            f"SOC: {payload['soc_percent']}% | "
            f"Cap: {payload['capacity_Ah']}Ah | "
            f"Res: {payload['resistance_ohms']}Ω"
        )
    except Exception as e:
        print(f"[PARSE ERROR] Could not decode message: {e}")

# Initialize client using CallbackAPIVersion.VERSION2 (paho-mqtt 2.x standard)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="My_Dashboard")

client.on_connect = on_connect
client.on_message = on_message

print("[INFO] Attempting to connect to Mosquitto at localhost:1883...")

try:
    client.connect("localhost", 1883, keepalive=60)
    # loop_forever blocks execution and continuously listens for incoming packets
    client.loop_forever()
except ConnectionRefusedError:
    print("\n[CRITICAL ERROR] Connection refused! Mosquitto is not running.")
    print("Fix: Open Windows 'Services' app, find 'Mosquitto Broker', and click 'Start'.")
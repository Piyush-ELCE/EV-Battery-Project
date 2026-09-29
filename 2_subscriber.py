import paho.mqtt.client as mqtt
import json

# Global variables to store the previous packet's values for comparison
last_temp = None
last_resistance = None

# Set your anomaly thresholds
TEMP_DELTA_THRESHOLD = 0.5       # Alert if temp rises > 0.5 degrees per tick
RESISTANCE_DELTA_THRESHOLD = 0.01 # Alert if resistance jumps > 0.01 ohms

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[CONNECTED] Successfully linked to broker.")
        client.subscribe("piyush/ev/project/battery1")
        print("[SUBSCRIBED] Listening for live data...\n")
    else:
        print(f"[ERROR] Connection failed with code: {rc}")

def on_message(client, userdata, msg):
    global last_temp, last_resistance

    try:
        raw_text = msg.payload.decode("utf-8")
        payload = json.loads(raw_text)

        current_temp = payload['cell_temp_C']
        current_res = payload['resistance_ohms']

        # 1. Calculate Rate of Change (Delta)
        temp_delta = 0.0
        res_delta = 0.0

        if last_temp is not None:
            temp_delta = current_temp - last_temp
        if last_resistance is not None:
            res_delta = current_res - last_resistance

        # 2. Update memory for the next loop
        last_temp = current_temp
        last_resistance = current_res

        # 3. Check against thresholds
        anomaly_flags = []
        if temp_delta > TEMP_DELTA_THRESHOLD:
            anomaly_flags.append(f"🔥 TEMP SPIKE (+{temp_delta:.2f}°C)")
        
        if res_delta > RESISTANCE_DELTA_THRESHOLD:
            anomaly_flags.append(f"⚠️ RESISTANCE JUMP (+{res_delta:.4f}Ω)")

        # 4. Print the output
        output = (
            f"--> Live | "
            f"Temp: {current_temp}°C (Δ {temp_delta:+.2f}) | "
            f"Volt: {payload['voltage_V']}V | "
            f"Res: {current_res}Ω (Δ {res_delta:+.4f})"
        )

        if anomaly_flags:
            # Print anomalies in a highly visible format
            print(f"\n[ANOMALY DETECTED] {' | '.join(anomaly_flags)}")
            print(output + " << WARNING")
            print("-" * 60)
        else:
            print(output)

    except Exception as e:
        print(f"[PARSE ERROR] Could not decode message: {e}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="My_Anomaly_Detector")
client.on_connect = on_connect
client.on_message = on_message

# Ensure this matches the broker you settled on (localhost or broker.hivemq.com)
client.connect("broker.hivemq.com", 1883, keepalive=60)

client.loop_forever()
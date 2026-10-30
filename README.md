```markdown
# 🔋 Cloud-Integrated EV Battery Telemetry & AI Anomaly Detection System

A real-time, end-to-end IoT monitoring pipeline for Electric Vehicle (EV) battery packs. This system continuously simulates realistic multi-parameter battery telemetry, streams data securely across cloud brokers via MQTT, executes real-time AI anomaly detection using an Isolation Forest model, records time-series measurements in InfluxDB Cloud (v3), and visualizes health metrics on a live Streamlit Command Center.

## 🔗 Live Dashboard
**[Insert your Streamlit Cloud URL here]**

---

## 📌 Architecture Overview

```text
┌───────────────────────────────┐
│       3_publisher.py          │ (Physics Engine & Sensor Simulation)
│   (Simulated ESP32 / BMS)     │
└───────────────┬───────────────┘
                │  MQTT over TLS (Port 8883)
                ▼
┌───────────────────────────────┐
│         HiveMQ Cloud          │ (Fully Managed MQTT Broker)
└───────────────┬───────────────┘
                │  Topic: piyush/ev/project/battery1
                ▼
┌───────────────────────────────┐
│       2_subscriber.py         │ ◄── [isolation_forest_model.pkl]
│   (Edge Inference Worker)     │     (Trained by 5_train_model.py)
└───────────────┬───────────────┘
                │  SQL / InfluxDB v3 Client
                ▼
┌───────────────────────────────┐
│     InfluxDB Cloud (v3)       │ (Serverless Time-Series Database)
└───────────────┬───────────────┘
                │  SQL Queries (Last 120 points & Offline Check)
                ▼
┌───────────────────────────────┐
│       4_dashboard.py          │ (Streamlit Community Cloud)
│   (Live Command Center UI)    │
└───────────────────────────────┘

```

---

## 🚀 Key Engineering Features

* **Edge Physics Simulation (Digital Twin):** Instead of static random numbers, the publisher acts as a Hardware-in-the-Loop (HIL) simulator, dynamically modeling temperature drift, capacity fade, current draw, and resistance curves under load.
* **Real-Time ML Anomaly Detection:** An Isolation Forest machine learning model intercepts the MQTT stream in real-time, instantly detecting multi-variable behavioral mismatches (e.g., normal temperature but abnormal internal resistance) before they trigger static hard-coded thresholds.
* **Asynchronous UI Rendering (`@st.fragment`):** The Command Center utilizes Streamlit's fragment rendering to poll the database every 4 seconds in the background. This provides a flicker-free, native-app experience without reloading the entire web page.
* **Graceful Degradation & Edge Resilience:** The system is engineered to handle network drops. If the physical sensors go offline, the UI does not crash. It gracefully freezes the telemetry charts, calculates the exact time of disconnection, and displays an "Offline Safe Mode" banner for the fleet manager.
* **Cloud-Native & Secure:** Utilizes Serverless InfluxDB v3 for high-speed time-series ingestion via FlightSQL/gRPC, secured behind Streamlit Cloud Secrets management and a frontend session validation gatekeeper.

---

## 🛠️ Tech Stack

* **IoT & Messaging:** Eclipse Paho MQTT, HiveMQ Cloud (TLS 1.2)
* **Machine Learning:** Scikit-Learn (Isolation Forest), Pandas, Joblib
* **Database:** InfluxDB Cloud v3 (SQL-based time-series data)
* **Frontend UI:** Streamlit (Python)
* **Environment:** VS Code, GitHub Integration

---

## 💻 How to Run Locally

If you wish to clone this repository and run the telemetry pipeline on your local Windows machine:

**1. Install Dependencies**

```bash
pip install -r requirements.txt

```

**2. Configure Credentials**
Update the `INFLUX_TOKEN` and HiveMQ credentials inside `2_subscriber.py`, `3_publisher.py`, and `4_dashboard.py` (or use a `.streamlit/secrets.toml` file).

**3. Start the Pipeline**
Use the included batch scripts to automatically manage the local environment. To launch the ML subscriber, edge publisher, and Streamlit dashboard in the correct sequence, double-click or run:

```bash
start.bat

```

To safely shut down the pipeline and terminate all background Python processes when you are finished, run:

```bash
stop.bat

```

---

*Developed as an Electrical & Computer Engineering (ECE) Portfolio Project.*

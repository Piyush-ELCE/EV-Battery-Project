# 🔋 Cloud-Integrated EV Battery Telemetry & AI Anomaly Detection System

A real-time, end-to-end IoT monitoring pipeline for Electric Vehicle (EV) battery packs. This system continuously simulates realistic multi-parameter battery telemetry, streams data securely across cloud brokers via MQTT, executes real-time AI anomaly detection using an Isolation Forest model, records time-series measurements in InfluxDB Cloud (v3), and visualizes health metrics on a live Streamlit Command Center.

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
│        HiveMQ Cloud           │ (Fully Managed MQTT Broker)
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
                │  SQL Queries (Last 2 minutes)
                ▼
┌───────────────────────────────┐
│       4_dashboard.py          │ (Streamlit Community Cloud)
│   (Live Command Center UI)    │
└───────────────────────────────┘
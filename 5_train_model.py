import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

print("Loading historical data...")
df = pd.read_csv("battery_telemetry.csv")

# Updated with your exact CSV column name: remaining_capacity_Ah
features = [
    'voltage_V', 'current_A', 'cell_temp_C', 'ambient_temp_C', 
    'soc_percent', 'resistance_ohms', 'remaining_capacity_Ah'
]
X = df[features]

print("Training Isolation Forest ML Model...")
model = IsolationForest(n_estimators=100, contamination=0.02, random_state=42)
model.fit(X)

joblib.dump(model, "isolation_forest_model.pkl")
print("✅ Model trained and saved successfully as 'isolation_forest_model.pkl'!")
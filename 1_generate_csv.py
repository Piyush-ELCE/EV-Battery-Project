import pandas as pd
import numpy as np
import time

num_samples = 150
current_time = int(time.time())

# 1. Base Variables
timestamps = [current_time + i for i in range(num_samples)]
ambient_temps = np.random.normal(loc=25.0, scale=0.5, size=num_samples) # Steady 25°C room
currents = np.random.normal(loc=15.0, scale=0.4, size=num_samples)      # Steady 15A draw
max_capacity_Ah = 50.0  # 50 Amp-hour cell

# 2. Simulated Dynamic Variables (Physics-based arrays)
voltages = []
cell_temps = []
soc_percent = []
internal_resistances = []

# Initial states
current_soc = 98.0  
current_temp = 30.0
base_resistance = 0.015 # 15 milliohms

for i in range(num_samples):
    # SOC drops based on current drawn (simplified coulomb counting)
    current_soc -= (currents[i] / 3600) * 100 / max_capacity_Ah 
    soc_percent.append(max(0, current_soc)) # Prevent negative SOC
    
    # Internal resistance rises slightly as SOC drops
    # If we trigger an "anomaly" at step 100, resistance spikes
    if i > 100:
        current_resistance = base_resistance + (100 - current_soc)*0.0005 + 0.02 # Sudden spike
        current_temp += 0.8 # Temperature starts climbing rapidly
    else:
        current_resistance = base_resistance + (100 - current_soc)*0.0001
        current_temp += 0.05 # Normal slow heating under load
        
    internal_resistances.append(current_resistance)
    cell_temps.append(current_temp)
    
    # Voltage calculation (V = V_open_circuit - I * R)
    # Open circuit voltage drops as SOC drops (simplified curve)
    voc = 3.3 + (current_soc * 0.009) 
    actual_voltage = voc - (currents[i] * current_resistance)
    voltages.append(actual_voltage)

# 3. Assemble the expanded DataFrame
telemetry_table = pd.DataFrame({
    'timestamp': timestamps,
    'voltage_V': np.round(voltages, 3),
    'current_A': np.round(currents, 3),
    'cell_temp_C': np.round(cell_temps, 2),
    'ambient_temp_C': np.round(ambient_temps, 2),
    'soc_percent': np.round(soc_percent, 2),
    'resistance_ohms': np.round(internal_resistances, 4),
    'remaining_capacity_Ah': np.round(np.array(soc_percent) / 100 * max_capacity_Ah, 2)
})

# 4. Save to CSV
csv_filename = 'battery_telemetry.csv'
telemetry_table.to_csv(csv_filename, index=False)

print(f"File created successfully: {csv_filename} with 8 parameters.")
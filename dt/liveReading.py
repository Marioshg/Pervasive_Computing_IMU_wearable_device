import pickle
import numpy as np
import pandas as pd
from collections import deque
from dataPreprocessing.imusignal import extract_features
from dataCollection.IMUReadings import IMUReader
import time

# Load the trained model and scaler
model = pickle.load(open("dt/model.pkl", "rb"))
scaler = pickle.load(open("dt/scaler.pkl", "rb"))
# Parameters from training
window_size = 100
overlap = 25
step = window_size - overlap

# Queue to store predictions
prediction_queue = deque(maxlen=10)  # Keep last 10 predictions

# Buffer to accumulate raw IMU data
buffer = []
# Initialize IMU reader
reader = IMUReader()
reader.start()
reader.wait_until_connected()

print("Connected to BLE device. Starting live prediction...")

try:
    while True:
        # Get new data from BLE
        new_data = reader.getData()
        
        #if not new_data.empty:
        #    print(f"Received {len(new_data)} new data points")
        
        # Process each new data point
        for _, row in new_data.iterrows():
            data_point = [
                row['x_accel'], 
                row['y_accel'], 
                row['z_accel'], 
                row['x_gyro'], 
                row['y_gyro'], 
                row['z_gyro']
            ]
            buffer.append(data_point)

            # Check if we have enough data for a window
            if len(buffer) >= window_size:
                # Extract the latest window
                window = np.array(buffer[-window_size:])

                # Extract features from the window
                features = extract_features(window)

                # Scale the features with proper column names
                columns = [f'col_{i}' for i in range(len(features))]
                features_df = pd.DataFrame([features], columns=columns)
                features_scaled = scaler.transform(features_df)

                # Make prediction
                prediction = model.predict(features_scaled)[0]

                # Add to queue
                prediction_queue.append(prediction)

                # Print the prediction
                print(f"Predicted gesture: {prediction}")

                # Remove processed samples, keeping overlap for next window
                buffer = buffer[step:]

        # Small delay to prevent busy waiting
        time.sleep(0.01)

except KeyboardInterrupt:
    print("Stopping...")
finally:
    reader.stop()
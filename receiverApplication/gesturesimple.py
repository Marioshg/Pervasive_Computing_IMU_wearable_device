import time
import sys
import numpy as np
from pathlib import Path
from collections import deque

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from dataCollection.IMUReadings import IMUReader
from receiverApplication.inference.inference_factory import InferenceFactory

# Parameters
window_size = 100
overlap = 25
step = window_size - overlap

# Buffer to accumulate raw IMU data
buffer = deque(maxlen=window_size)

def main():
    print("Connecting to IMU...")
    reader = IMUReader()
    reader.start()
    
    if not reader.wait_until_connected(timeout=10.0):
        print("Could not connect to IMU")
        reader.stop()
        return
    
    print("Connected. Starting inference...")
    inference = InferenceFactory.decision_tree(data_provider=lambda: np.array(list(buffer))[:100])
    inference.start()
    
    print("Starting gesture detection. Press Ctrl+C to stop.")
    try:
        while True:
            # Get new data from IMU
            new_data = reader.getData()
            
            if not new_data.empty:
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
                    
                    # Check if we have enough for a window
                    if len(buffer) >= window_size:
                        gesture = inference.getGesture()
                        if gesture is not None:
                            print(f"Detected gesture: {gesture}")
            
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        inference.stop()
        reader.stop()

if __name__ == "__main__":
    main()

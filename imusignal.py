import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
LABELS = ["timestamp", "x_accel", "y_accel", "z_accel", "x_gyro", "y_gyro", "z_gyro"]
class IMUSignal():
    
    """Initialize an empty IMU accelerometer XYZ + gyroscope XYZ signal"""
    def __init__(self):
        self.signal = pd.DataFrame(columns=LABELS)

    
    """Import signal from file"""
    @classmethod
    def from_file(cls, file_csv, expected_size=300):
        instance = cls()
        
        instance.signal = pd.read_csv(file_csv, header=0, index_col=0)
        instance._force_signal_size(expected_size)
        
        return instance        
    
    def append(self, data):
        imu_df = data.copy() if self.signal.empty else pd.concat([imu_df, data], ignore_index=True)
        
    def length(self):
        return len(self.signal.index)
        
    def _force_signal_size(self, expected_size):
        self.signal = self.signal.sort_index()
        
        start = self.signal.index.min()
        end = start + expected_size
        complete_indices = np.arange(start, end)
        
        self.signal = self.signal.reindex(complete_indices)
        self.signal = self.signal.interpolate()
        
    def get_windows(self, window_size, overlap):
        step = window_size - overlap
        
        starts = np.arange(0, len(self.signal) - window_size + 1, step)
        idx = starts[:, None] + np.arange(window_size)
        windowed_values = self.signal.to_numpy()[idx]
        
        return windowed_values
        
    def to_csv(self, filename, **kwargs):
        return self.signal.to_csv(filename, **kwargs)
        
if __name__ == "__main__":
    IMUSignal("./data/Marios/behind_left_1.csv")
    IMUSignal("./data/Marios/get_up_7.csv")
    IMUSignal("./data/Marios/walk_13.csv")
    IMUSignal("./data/Marios/tilt_left_1.csv")
    IMUSignal("./data/Marios/shake_leftright_1.csv")
    IMUSignal("./data/Marios/music_beat_3.csv")
    
    
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
        instance.force_signal_size(expected_size)
        
        return instance        
    
    def append(self, data):
        self.signal = data.copy() if self.signal.empty else pd.concat([self.signal, data], ignore_index=True)
        
    def length(self):
        return len(self.signal.index)
        
    def force_signal_size(self, expected_size):
        self.signal = self.signal.sort_index()
        
        start = self.signal.index.min()
        end = start + expected_size
        complete_indices = np.arange(start, end)
        
        self.signal = self.signal.reindex(complete_indices)
        self.signal = self.signal.interpolate()
        
    def get_raw_windows(self, window_size, overlap, flatten=True):
        step = window_size - overlap
        
        starts = np.arange(0, len(self.signal) - window_size + 1, step)
        idx = starts[:, None] + np.arange(window_size)
        windowed_values = self.signal.to_numpy()[idx]
        
        if flatten:
            windowed_values = windowed_values.reshape(windowed_values.shape[0], -1)
        
        return windowed_values
    
    def to_csv(self, filename, **kwargs):
        return self.signal.to_csv(filename, **kwargs)
        
if __name__ == "__main__":
    IMUSignal.from_file("./data/Marios/behind_left_1.csv")
    IMUSignal.from_file("./data/Marios/get_up_7.csv")
    IMUSignal.from_file("./data/Marios/walk_13.csv")
    IMUSignal.from_file("./data/Marios/tilt_left_1.csv")
    IMUSignal.from_file("./data/Marios/shake_leftright_1.csv")
    IMUSignal.from_file("./data/Marios/music_beat_3.csv")
    
    
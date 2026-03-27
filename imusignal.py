import pandas as pd
import numpy as np

LABELS = ["timestamp", "x_accel", "y_accel", "z_accel", "x_gyro", "y_gyro", "z_gyro"]

class IMUSignal():
    
    def __init__(self):
        """Initialize an empty IMU accelerometer XYZ + gyroscope XYZ signal"""        
        self.signal = pd.DataFrame(columns=LABELS)
        
    
    @classmethod
    def from_file(cls, file_csv, expected_size=300):
        """Import signal from file"""
        
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
        
        
    def diff_gyro(self):
        """Difference the gyroscope data"""
        cols = ['x_gyro', 'y_gyro', 'z_gyro']
        self.signal[cols] = self.signal[cols].diff().fillna(0)
    
    def normalize(self):
        """Normalize data based using z-score"""
        self.signal = (self.signal - self.signal.mean()) / self.signal.std()
    
    def get_raw_windows(self, window_size, overlap, flatten=True):
        """Window the data without window processing. If 'flatten' is False, it will return a list of shape (windowcount, windowsize, 6), 
        otherwise it is (windowcount, windowsize * 6)"""
        step = window_size - overlap
        
        starts = np.arange(0, len(self.signal) - window_size + 1, step)
        idx = starts[:, None] + np.arange(window_size)
        windowed_values = self.signal.to_numpy()[idx]
        
        if flatten:
            windowed_values = windowed_values.reshape(windowed_values.shape[0], -1)
        
        return windowed_values
    
    def _extract_features(self, window):
        # --- basic statistics ---
        mean = window.mean(axis=0)
        std = window.std(axis=0)
        min_ = window.min(axis=0)
        max_ = window.max(axis=0)
        median = np.median(window, axis=0)
        
        q25 = np.percentile(window, 25, axis=0)
        q75 = np.percentile(window, 75, axis=0)

        rms = np.sqrt((window**2).mean(axis=0))
        energy = (window**2).sum(axis=0)

        # --- magnitude (orientation-invariant motion strength) ---
        magnitude = np.linalg.norm(window, axis=1)
        mag_mean = magnitude.mean()
        mag_std = magnitude.std()
        mag_max = magnitude.max()

        # --- dynamics (temporal structure) ---
        diff = np.diff(window, axis=0)
        diff_mean = diff.mean(axis=0)
        diff_std = diff.std(axis=0)

        # zero-crossing rate (oscillation detection)
        zero_crossings = ((window[:-1] * window[1:]) < 0).sum(axis=0)

        # --- correlation between axes (gesture direction patterns) ---
        corr_xy = np.corrcoef(window[:, 0], window[:, 1])[0, 1]
        corr_xz = np.corrcoef(window[:, 0], window[:, 2])[0, 1]
        corr_yz = np.corrcoef(window[:, 1], window[:, 2])[0, 1]

        # handle NaNs from constant signals
        corr_xy = 0 if np.isnan(corr_xy) else corr_xy
        corr_xz = 0 if np.isnan(corr_xz) else corr_xz
        corr_yz = 0 if np.isnan(corr_yz) else corr_yz

        # --- signal range (amplitude of motion) ---
        range_ = max_ - min_

        features = np.concatenate([
            mean, std, min_, max_, median, q25, q75, rms, energy,
            range_,
            diff_mean, diff_std,
            zero_crossings,
            [mag_mean, mag_std, mag_max],
            [corr_xy, corr_xz, corr_yz]
            ])


        return features
    
    def get_feature_windows(self, window_size, overlap):
        """Window the data and extract features from every window."""
        windowed_values = self.get_raw_windows(window_size, overlap, flatten=False)
        features = np.array([self._extract_features(w) for w in windowed_values])
        
        return features
        
    
    def to_csv(self, filename, **kwargs):
        return self.signal.to_csv(filename, **kwargs)
        
if __name__ == "__main__":
    sig = IMUSignal.from_file("./data/Marios/behind_left_1.csv")
    print(sig.length())
    
    print(sig.signal.head())
    ws = sig.get_feature_windows(100, 50)
    print(ws.shape)
    # print(ws[0])    
    ws_norm = sig.get_feature_windows(100, 50, normalize=True)
    print(ws.shape)
    # print(ws_norm[0])    
    
    # sig.normalize()
    # print(sig.signal.head())
    
    # IMUSignal.from_file("./data/Marios/get_up_7.csv")
    # IMUSignal.from_file("./data/Marios/walk_13.csv")
    # IMUSignal.from_file("./data/Marios/tilt_left_1.csv")
    # IMUSignal.from_file("./data/Marios/shake_leftright_1.csv")
    # IMUSignal.from_file("./data/Marios/music_beat_3.csv")
    
    
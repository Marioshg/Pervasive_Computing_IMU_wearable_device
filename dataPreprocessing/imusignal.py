import numpy as np
import pandas as pd

def from_csv(filename, expected_size=300):
    signal = pd.read_csv(filename, header=0, index_col=0)
    return force_signal_size(signal, expected_size)   

def get_raw_windows(signal, window_size, overlap, flatten=True):
	"""Window the data without window processing. If 'flatten' is False, it will return a list of shape (windowcount, windowsize, 6), 
	otherwise it is (windowcount, windowsize * 6)"""
	step = window_size - overlap
	
	starts = np.arange(0, len(signal) - window_size + 1, step)
	idx = starts[:, None] + np.arange(window_size)
	windowed_values = signal.to_numpy()[idx]
	
	if flatten:
		windowed_values = windowed_values.reshape(windowed_values.shape[0], -1)
	
	return windowed_values


def extract_features(signal):
	# --- basic statistics ---
	mean = signal.mean(axis=0)
	std = signal.std(axis=0)
	min_ = signal.min(axis=0)
	max_ = signal.max(axis=0)
	median = np.median(signal, axis=0)
	
	q25 = np.percentile(signal, 25, axis=0)
	q75 = np.percentile(signal, 75, axis=0)

	rms = np.sqrt((signal**2).mean(axis=0))
	energy = (signal**2).sum(axis=0)

	# --- magnitude (orientation-invariant motion strength) ---
	magnitude = np.linalg.norm(signal, axis=1)
	mag_mean = magnitude.mean()
	mag_std = magnitude.std()
	mag_max = magnitude.max()

	# --- dynamics (temporal structure) ---
	diff = np.diff(signal, axis=0)
	diff_mean = diff.mean(axis=0)
	diff_std = diff.std(axis=0)

	# zero-crossing rate (oscillation detection)
	zero_crossings = ((signal[:-1] * signal[1:]) < 0).sum(axis=0)

	# --- correlation between axes (gesture direction patterns) ---
	corr_xy = np.corrcoef(signal[:, 0], signal[:, 1])[0, 1]
	corr_xz = np.corrcoef(signal[:, 0], signal[:, 2])[0, 1]
	corr_yz = np.corrcoef(signal[:, 1], signal[:, 2])[0, 1]

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
        

def force_signal_size(signal, expected_size):
        signal = signal.sort_index()
        
        start = signal.index.min()
        end = start + expected_size
        complete_indices = np.arange(start, end)
        
        signal = signal.reindex(complete_indices)
        signal = signal.interpolate()
        
        return signal
        

def get_feature_windows(signal, window_size, overlap):
        """Window the data and extract features from every window."""
        windowed_values = get_raw_windows(signal, window_size, overlap, flatten=False)
        features = np.array([extract_features(w) for w in windowed_values])
        
        return features
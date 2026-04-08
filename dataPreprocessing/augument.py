# augumentation techniques:
# - time warping (non-linear)
# - time scaling (linear)
# - multiply by a factor
# - mirror left-right
# - mirror left-right
# - 3d rotation (emulate different initial head positions e.g. tilted front/back/left/right)

from os import listdir, path, makedirs
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
from scipy.interpolate import PchipInterpolator

from imusignal import from_csv, force_signal_size

SAMPLE_RATE = 100

def _random_curve(n, loc=0, sigma=0.2, max_freq_hz=4, sample_rate=100):
    duration = n / sample_rate
    peak_count = int(max_freq_hz * duration)

    t = np.arange(n)
    tt = np.linspace(0, n - 1, peak_count + 2)

    # strictly bounded control points
    yy = np.ones(peak_count + 2) * loc
    yy[1:-1] = np.random.normal(loc=loc, scale=sigma, size=peak_count)

    interp = PchipInterpolator(tt, yy)
    curve = interp(t)

    return curve

def random_time_scale(signal):
    """Speeds up or slows down the signal"""
    n = len(signal)
    
    scale = 0.9 + 0.4 * np.random.random_sample()
    new_n = int(n / scale)

    t_old = np.linspace(0, 1, n)
    t_new = np.linspace(0, 1, new_n)

    new_data = {}
    
    for col in signal.columns:
        if col == "timestamp":
            continue
        scaled = np.interp(t_new, t_old, signal[col].values)
        print(scaled.shape)
        
        
        new_data[col] = scaled

    new_signal = pd.DataFrame(new_data)
    new_signal["timestamp"] = np.arange(signal.index.values[0], signal.index.values[0] + new_n)
    new_signal.set_index('timestamp')
    
    new_signal = force_signal_size(new_signal, n)
    
    return new_signal

def random_time_warp(signal: pd.DataFrame, sigma=0.2):
    """Non-linear time warping. Sigma affects the strength of warp"""
    n = len(signal)
    t = np.arange(n)

    curve = _random_curve(n, 1, sigma, 2)
    
    warped_t = np.cumsum(curve)

    warped_t = (warped_t - warped_t.min()) / (warped_t.max() - warped_t.min()) * (n - 1)

    new_data = {}
    new_data["timestamp"] = signal.index.values

    for col in signal.columns:
        if col == "timestamp":
            continue
        new_data[col] = np.interp(t, warped_t, signal[col].values)

    new_signal = pd.DataFrame(new_data)
    new_signal.set_index('timestamp')

    return new_signal

def random_amplitude_scale(signal: pd.DataFrame, sigma=0.8):
    """Multiplies all channels of the signal by a random factor"""
    new_signal = signal.copy()

    factor = 1 - (sigma / 2) + sigma * np.random.random_sample()

    for col in new_signal.columns:
        if col != "timestamp":
            new_signal[col] = new_signal[col] * factor

    return new_signal



# assumes   x -> roll/forward looking axis(tilting head)
#           y -> yaw/pan/vertical axis/(turning head); 
#           z -> pitch/ear axis(nodding);
def random_rotate_3d(df: pd.DataFrame, max_angle_deg=10):
    """Small random 3D rotation applied on accelerator and gyro data """
    # 
    angles = np.deg2rad(np.random.uniform(-max_angle_deg, max_angle_deg, size=3))
    rot = R.from_euler('xyz', angles)

    accel = df[["x_accel", "y_accel", "z_accel"]].values
    gyro  = df[["x_gyro",  "y_gyro",  "z_gyro"]].values

    accel_rot = rot.apply(accel)
    gyro_rot  = rot.apply(gyro)

    new_df = df.copy()
    new_df[["x_accel", "y_accel", "z_accel"]] = accel_rot
    new_df[["x_gyro",  "y_gyro",  "z_gyro"]] = gyro_rot

    return new_df


def augument_take(filename, n_per_take=4):
    augumented_take = []
    expected_size = 200 if 'fast' in filename.split("/")[-1] else 300
    signal = from_csv(filename, expected_size)
    

    for _ in range(n_per_take):

        # TODO add more augumentation techniques
        time_warped = random_time_warp(signal, sigma=0.5)
        amp_scaled = random_amplitude_scale(time_warped)
        rotated: pd.DataFrame = random_rotate_3d(amp_scaled, max_angle_deg=20)
        augumented_take.append(rotated)   
            
    return augumented_take         

def augument_dir(dirpath, out_dirpath):
    if not path.exists(out_dirpath):
        makedirs(out_dirpath)
    
    
    filenames = [f for f in listdir(dirpath) if path.isfile(path.join(dirpath, f))]
    
    gestures = {}

    for filename in filenames:
        augumented_take: list[pd.DataFrame] = augument_take(path.join(dirpath, filename), n_per_take=4)    
          
        slug = "_".join(filename.split("_")[:-1])
        
        for i, aug in enumerate(augumented_take):
            aug.to_csv(path.join(out_dirpath, f"{slug}_AUG_{i+1}"))
 


# FUNCTIONS BELOW ARE NOT FINISHED

def mirror_left_right(signal: pd.DataFrame):
    new_signal = signal.copy()

    new_signal["x_accel"] = -new_signal["x_accel"]
    new_signal["x_gyro"]  = -new_signal["x_gyro"]

    return new_signal

def renoise(signal, sigma=0.7):
    # window_size = 6
    
    # filtered = moving_average(signal, window_size)
    filtered = signal
    
    # print(signal.std())
    
    noise_low = _random_curve(200, sigma=sigma, max_freq_hz=3)
    noise_high = _random_curve(200, sigma=sigma, max_freq_hz=30)
    noise_mult = _random_curve(200, sigma=1, max_freq_hz=4)
    
    total_noise = noise_high * noise_mult + noise_low
    
    noised = filtered + total_noise
    
    return noised


def random_amplitude_warp(signal):
    new_data = {}
    new_data["timestamp"] = signal.index.values.copy()

    shift = _random_curve(len(signal), sigma=1, max_freq_hz=2)

    for col in signal.columns:
        if col == "timestamp":
            continue
        
        channel = signal[col]

        sigma = (channel.max()-channel.min()) * 0.1
        
        new_data[col] = channel + shift * sigma

    new_signal = pd.DataFrame(new_data)
    new_signal.set_index('timestamp')

    return new_signal



if __name__ == "__main__":
   dirpath = path.abspath("./data/Alex")
   out_dirpath = path.abspath("./data/AugAlex")
   
   augument_dir(dirpath, out_dirpath)
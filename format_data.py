from utility import DataOrganiser
from imusignal import IMUSignal
import pandas as pd
import numpy as np
import math
import os

SAMPLE_SEED = 42

def get_mapping() -> dict:
    labels = {
        'look_left': ['look_left', 'look_left_fast', 'look_left_fast_return', 'look_left_return'],
        'tilt_left': ['tilt_left', 'tilt_left_fast', 'tilt_left_fast_return', 'tilt_left_return'],
        'look_right': ['look_right', 'look_right_fast', 'look_right_fast_return', 'look_right_return'],
        'tilt_right': ['tilt_right', 'tilt_right_fast', 'tilt_right_fast_return', 'tilt_right_return'],
        'look_up': ['look_up', 'look_up_fast', 'look_up_fast_return', 'look_up_return'],
        'look_down': ['look_down', 'look_down_fast', 'look_down_fast_return', 'look_down_return'],
        'none': ['idle', 'behind_right_fast', 'music_beat', 'shake_leftright_fast_return', 'look_direction', 'sit_down', 'behind_left', 'shake_leftright_return', 'behind_right_return', 'nod', 'behind_right_fast_return', 'behind_left_return', 'behind_left_fast_return', 'get_up', 'behind_right', 'shake_rightleft_return', 'shake_rightleft_fast', 'shake_leftright', 'look_around', 'shake_leftright_fast', 'jump', 'shake_rightleft', 'walk', 'shake_rightleft_fast_return', 'behind_left_fast']
    }
    return labels

def join_on_mapping(organiser: DataOrganiser, mapping: dict) -> dict:
    '''
    Provide a new dictionary that is joined on the given mapping
    '''
    new_data = {}
    old_data = organiser.recordingDictByGesture
    for label in mapping:
        new_data[label] = []
        old_labels = mapping[label]
        for name in old_labels:
            new_data[label] += (old_data[name])
    return new_data

def process_gesture(files: list[str]) -> list:
    '''
    Process a single gesture; expects a list of CSV files
    '''
    items = []
    for file in files:
        # get the signal, make sure its length is divisible by 100
        expected_size = 200 if 'fast' in file else 300
        signal = IMUSignal.from_file(file, expected_size=expected_size)
        
        windowed = signal.get_raw_windows(100, 0, flatten=True)
        
        items += windowed.tolist()
    return items

def process_gestures(data_files: dict) -> dict:
    data = {}
    length = None
    for gesture, files in data_files.items():
        values = process_gesture(files)
        data[gesture] = values
        
        # keep the smallest number of samples
        if length is None or len(values) < length:
            length = len(values)

    # ensure all gestures have the same length
    for gesture in data.keys():
        values = data[gesture]
        if len(values) == length:
            continue
        # use pandas data frame sampling to ensure correct size
        # sampling is randomized, so should be ok
        df = pd.DataFrame(values)
        df = df.sample(n=length, random_state=SAMPLE_SEED)
        data[gesture] = df.to_numpy().tolist()

    return data

def build_dataframe(data: dict) -> pd.DataFrame:
    rows = []
    for key, inner_lists in data.items():
        for inner_list in inner_lists:
            row = {'label': key} | {f'col_{i}': val for i, val in enumerate(inner_list)}
            rows.append(row)

    df = pd.DataFrame(rows)

    return df

def get_data(data_folder: str) -> pd.DataFrame:
    organiser = DataOrganiser(data_folder)
    organiser.printInfo()

    mapping = get_mapping()
    data_files = join_on_mapping(organiser, mapping)
    print(f'Mapped found files to gestures')

    gestures = process_gestures(data_files)
    df = None
    df = build_dataframe(gestures)
    print(f'Built data frame with {len(df)} entries from gesture data')

    return df

if __name__ == "__main__":
    data_folder = "data"
    filename = "aggregated.csv"
    path = os.path.join(data_folder, filename)
    df = get_data(data_folder)
    df.to_csv(path)
    print(f"Saved data to {path}")
    
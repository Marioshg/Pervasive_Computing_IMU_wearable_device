from utility import DataOrganiser
import pandas as pd
import numpy as np
import math

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
            new_data[label].append(old_data[name])
    return new_data

def process_gesture(files: list[str]) -> list:
    '''
    Process a single gesture; expects a list of CSV files
    '''
    items = []
    for file in files:
        data = pd.read_csv(file)
        size = math.ceil(len(data) / 100)
        data = np.array_split(data, size)
        data = [d.tolist() for d in data]
        items = items + data
    lengths = [len(item) for item in items]
    print(lengths)
    return items

def process_gestures(data_files: dict) -> dict:
    data = {}
    for (gesture, files) in data_files.items():
        data[gesture] = process_gesture(files)
    return data

def get_data():
    organiser = DataOrganiser("data")
    mapping = get_mapping()
    data = join_on_mapping(organiser, mapping)
    d = process_gesture(['data/Marios/look_left_1.csv', 'data/Marios/look_left_2.csv'])

if __name__ == "__main__":
    get_data()
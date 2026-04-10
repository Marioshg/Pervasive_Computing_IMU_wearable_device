import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
import pickle
from pyexpat import model
import pandas as pd
from collections import deque
import sys
from pathlib import Path
import numpy as np

# Go: current file → ../receiverApplication → ../root/dataPreprocessing
imusignal_dir = Path(__file__).resolve().parents[2] / "dataPreprocessing"
sys.path.append(str(imusignal_dir))

from imusignal import extract_features

class DecisionTree:

    model = None
    scaler = None

    @staticmethod
    def setup():
        # Load the trained model and scaler
        DecisionTree.model = pickle.load(open("../dt/model.pkl", "rb"))
        DecisionTree.scaler = pickle.load(open("../dt/scaler.pkl", "rb"))


    @staticmethod
    def predict(data):
        '''
        Data is already windowed.
        Return the prediction.
        '''

        # Extract features from the window
        df = pd.DataFrame(data)
        df = df.to_numpy(dtype=np.float32)
        df = df.reshape(100, 6)
        features = extract_features(df)
        # Scale the features with proper column names
        columns = [f'col_{i}' for i in range(len(features))]
        features_df = pd.DataFrame([features], columns=columns)
        features_scaled = DecisionTree.scaler.transform(features_df)

        # Make prediction
        prediction = DecisionTree.model.predict(features_scaled)[0]

        return prediction
import pickle
from pyexpat import model
import pandas as pd
from collections import deque

from dataPreprocessing.imusignal import extract_features

class DecisionTree:

    model = None
    scaler = None

    @staticmethod
    def setup():
        # Load the trained model and scaler
        DecisionTree.model = pickle.load(open("dt/model.pkl", "rb"))
        DecisionTree.scaler = pickle.load(open("dt/scaler.pkl", "rb"))

    @staticmethod
    def preprocess(data):
        pass

    @staticmethod
    def predict(data):
        '''
        Data is already windowed.
        Return the prediction.
        '''
        #window= wnindowInput()

        input = DecisionTree.preprocess(data)

        # Extract features from the window
        features = extract_features(window)
        # Scale the features with proper column names
        columns = [f'col_{i}' for i in range(len(features))]
        features_df = pd.DataFrame([features], columns=columns)
        features_scaled = DecisionTree.scaler.transform(features_df)

        # Make prediction
        prediction = DecisionTree.model.predict(features_scaled)[0]

        return prediction
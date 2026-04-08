import os

import tensorflow as tf
from tensorflow import keras
from keras.saving import load_model
import pandas as pd
from sklearn.preprocessing import LabelEncoder

class LSTM:
    MODEL_LOCATION = os.path.join("..", "tf-lite", "model.h5")
    TRAINING_LOCATION = os.path.join("..", "data", "aggregated.csv")

    model = None

    # these are the default labels as given by model.ipynb
    labels = ['look_down', 'look_left', 'look_right', 'look_up', 'none', 'tilt_left', 'tilt_right']

    @staticmethod
    def load(model_location=MODEL_LOCATION):
        LSTM.model = load_model(model_location, compile=True)

    @staticmethod
    def set_labels_from_training():
        '''
        Call this if you want to reset the labels,
        but these should normally be the same as the hardcoded ones
        '''
        df = pd.read_csv('../data/aggregated.csv')
        y = df.iloc[:, 0].values
        le = LabelEncoder()
        y = le.fit_transform(y)
        LSTM.labels = le.classes_

    @staticmethod
    def predict(data):
        df = pd.DataFrame(data)
        df = df.reshape(-1, 100, 6)
        predictions = LSTM.model.predict(df)
        return LSTM.labels[tf.argmax(predictions)]
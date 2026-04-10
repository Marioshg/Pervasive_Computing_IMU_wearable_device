import os

import numpy as np
import tensorflow as tf
from tensorflow import keras
from keras.saving import load_model
import pandas as pd
from sklearn.preprocessing import LabelEncoder

import datetime

class LSTM:
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_LOCATION = os.path.join(CURRENT_DIR, "..", "..", "tf-lite", "model.h5")
    TRAINING_LOCATION = os.path.join(CURRENT_DIR, "..", "..", "data", "aggregated.csv")

    model = None

    # these are the default labels as given by model.ipynb
    labels = ['look_down', 'look_left', 'look_right', 'look_up', 'none', 'tilt_left', 'tilt_right']

    @staticmethod
    def load(model_location=MODEL_LOCATION):
        LSTM.model = load_model(model_location, compile=True)

    @staticmethod
    def warmup():
        dummy_data = np.random.rand(1, 100, 6)
        LSTM._infer(dummy_data)

    @staticmethod
    def set_labels_from_training():
        '''
        Call this if you want to reset the labels,
        but these should normally be the same as the hardcoded ones
        '''
        df = pd.read_csv(LSTM.TRAINING_LOCATION)
        y = df.iloc[:, 0].values
        le = LabelEncoder()
        y = le.fit_transform(y)
        LSTM.labels = le.classes_

    @tf.function
    def _infer(x):
        return LSTM.model(x, training=False)

    @staticmethod
    def predict(data):
        df = pd.DataFrame(data).to_numpy(dtype=np.float32)
        df = df.reshape(-1, 100, 6)
        predictions = LSTM._infer(df)
        idx = int(tf.argmax(predictions, axis=-1).numpy()[0])
        return LSTM.labels[idx]
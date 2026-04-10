import pandas as pd
import os
from inference_factory import InferenceFactory

class InferenceTest:

    X = None
    index = 0

    @staticmethod
    def load_data():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(os.path.join(current_dir, "..", "..", "data", "aggregated.csv"))
        X_flat = df.iloc[:, 1:].values
        InferenceTest.X = X_flat.reshape(-1, 100, 6)

    @staticmethod
    def data_provider():
        data = InferenceTest.X[InferenceTest.index]
        InferenceTest.index += 1
        return data

    @staticmethod
    def test():
        InferenceTest.load_data()
        inference = InferenceFactory.decision_tree(data_provider=InferenceTest.data_provider)
        inference.start()
        idx = 0
        while True:
            prediction = inference.getGesture()
            if prediction is not None:
                print(f"{idx} : {prediction}")
            idx += 1

if __name__ == "__main__":
    InferenceTest.test()
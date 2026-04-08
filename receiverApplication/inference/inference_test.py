import pandas as pd
from inference_factory import InferenceFactory

class InferenceTest:

    X = None
    index = 0

    @staticmethod
    def load_data():
        df = pd.read_csv("../data/aggregated.csv")
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
        inference = InferenceFactory.lstm(data_provider=InferenceTest.data_provider)
        inference.start()
        while True:
            print(inference.getGesture())

if __name__ == "__main__":
    InferenceTest.test()
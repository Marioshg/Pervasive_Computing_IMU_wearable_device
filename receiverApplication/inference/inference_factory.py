from lstm_model import LSTM
from inference import Inference

class InferenceFactory:

    @staticmethod
    def lstm(data_provider=None, queue_size=1):
        LSTM.load()
        return Inference(
            data_provider=data_provider,
            model_function=LSTM.predict,
            queue_size=queue_size
        )

    
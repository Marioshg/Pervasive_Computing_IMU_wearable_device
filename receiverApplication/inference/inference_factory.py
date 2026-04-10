from receiverApplication.inference.lstm_model import LSTM
# from decision_tree_model import DecisionTree
from receiverApplication.inference.inference import Inference

class InferenceFactory:

    @staticmethod
    def lstm(data_provider=None, queue_size=1):
        LSTM.load()
        print("Loaded LSTM model")
        LSTM.warmup()
        print("LSTM warmup complete")
        return Inference(
            data_provider=data_provider,
            model_function=LSTM.predict,
            queue_size=queue_size
        )

    # @staticmethod
    # def decision_tree(data_provider=None, queue_size=1):
    #     DecisionTree.setup()
    #     return Inference(
    #         data_provider=data_provider,
    #         model_function=DecisionTree.predict,
    #         queue_size=queue_size
    #     )
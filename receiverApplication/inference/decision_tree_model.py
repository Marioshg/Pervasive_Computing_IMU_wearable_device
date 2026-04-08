class DecisionTree:
    '''
    Store variables here
    '''
    model = None

    @staticmethod
    def setup():
        pass

    @staticmethod
    def preprocess(data):
        pass

    @staticmethod
    def predict(data):
        '''
        Data is already windowed.
        Return the prediction.
        '''
        input = DecisionTree.preprocess(data)
        pass
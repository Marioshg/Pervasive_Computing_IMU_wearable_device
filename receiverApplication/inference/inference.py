import asyncio
import queue
import threading
import copy

class Inference:
    MIN_DELAY = 0.001
    TIMEOUT = 2

    def __init__(self, data_provider=None, model_function=None, queue_size=1):
        self._data_provider = data_provider
        self._model_function = model_function
        self._data = None

        if queue_size is not None and queue_size > 0:
            self._queue = queue.Queue(maxsize=queue_size)
        else:
            self._queue = queue.SimpleQueue()

        self._lock = threading.Lock()

        self._thread = None
        self._loop = None
        self._running = False

    def _thread_main(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._runner)
        finally:
            self._loop.close()
            self._loop = None

    async def _runner(self):
        try:
            await self.inference_loop()
        finally:
            print(f"Inference runner has finished execution")

    def start(self):
        if self._running:
            return
        
        if self._model_function is None:
            print(f"Cannot start inference thread without a model function")
            return
        
        if self._data_provider is None:
            print(f"Cannot start inference thread without a data provider")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._thread_main, daemon=True)
        self._thread.start()

    def stop(self):
        if not self._running:
            return
        
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=Inference.TIMEOUT)
            self._thread = None

    def set_model(self, model_function):
        '''
        Model function has to receive as input either a pandas
        data frame that is (100, 6) or an array-like of 600
        elements and return a string representing the class infered
        '''
        self._model_function = model_function

    def set_data_provider(self, data_provider):
        '''
        Data provider must be a function that returns
        either a pandas data frame that is (100, 6) or 
        an array-like of 600 elements
        '''
        self._data_provider = data_provider

    def getGesture(self):
        '''
        This will return the latest unread inference result.
        Will return None if no inference has been made since
        the last call to get_latest_output
        '''
        acquired = self._lock.acquire(timeout=Inference.TIMEOUT)
        if not acquired:
            return None
        
        if self._queue.empty():
            output = None
        else:
            output = self._queue.get()
        self._lock.release()
        return output

    def get_data(self):
        '''
        Read data from the data provider and store it
        '''
        acquired = self._lock.acquire(timeout=Inference.TIMEOUT)
        if not acquired:
            return
        
        # get a copy of the data to avoid data races
        self._data = copy.deepcopy(self._data_provider())
        self._lock.release()

    def infer(self):
        '''
        Make an inference based on stored data.
        if an inference has been made, the result is 
        stored in the output queue
        '''
        if self._data is None:
            return
        
        output = self._model_function(self._data)

        acquired = self._lock.acquire(timeout=Inference.TIMEOUT)
        if not acquired:
            # we can't write the output, so just return
            return
        if self._queue.full():
            # lose first item in the queue if not enough space
            self._queue.get()
        self._queue.put(output)
        self._lock.release()

    async def inference_loop(self):
        while self._running:
            self.get_data()
            self.infer()
            await asyncio.sleep(Inference.MIN_DELAY)

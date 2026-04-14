import asyncio
from bleak import BleakClient, BleakScanner
# from ble_simulator import SimBleakClient as BleakClient
# from ble_simulator import SimBleakScanner as BleakScanner
import threading
import time
import pandas as pd

import queue

from dataPreprocessing.imusignal import diff

class IMUWindower:
    _current_reader = None

    def __init__(self, device_uuid, device_name, window_size, window_overlap):
        self.columns = ["timestamp", "x_accel", "y_accel", "z_accel", "x_gyro", "y_gyro", "z_gyro"]

        self.device_uuid = device_uuid
        self.device_name = device_name

        # Queue for raw incoming samples
        self._raw_q = queue.Queue()

        # Queue for the last completed window
        self._window_q = queue.Queue(maxsize=1)

        self.window_size = window_size
        self.window_step = window_size - window_overlap

        # Internal buffer used to accumulate samples for windowing
        self._buffer = pd.DataFrame(columns=self.columns)
        self._current_step = 0

        self.client = None
        self._ble_thread = None
        self._accumulator_thread = None
        self._loop = None
        self._running = False
        self._connected_event = threading.Event()
        self._failed_event = threading.Event()
        IMUWindower._current_reader = self
        
    @staticmethod
    async def _notification_handler(sender, data: bytearray):
        reader = IMUWindower._current_reader
        if not reader._running:
            return
        try:
            values = list(map(float, data.decode("utf-8").strip().split(",")))
            row = dict(zip(reader.columns, values))
            
            reader._raw_q.put(row)
        except Exception as e:
            print("Parse error:", e)

    async def _connect(self):
        devices = await BleakScanner.discover()
        target = None
        for d in devices:
            if d.name == self.device_name:
                target = d
                break

        if target is None:
            raise RuntimeError(f"Device '{self.device_name}' not found")

        self.client = BleakClient(target.address)
        await self.client.connect()

        if not self.client.is_connected:
            raise RuntimeError("Failed to connect")

        self._connected_event.set()
        print(f"Connected to {target.name} ({target.address})")

        print("Set notification handler for BLE characteristic")
        await self.client.start_notify(self.device_uuid, IMUWindower._notification_handler)

    async def _ble_runner(self):
        try:
            await self._connect()
            while self._running:
                await asyncio.sleep(0.01)
        finally:
            self._failed_event.set()
            if self.client and self.client.is_connected:
                await self.client.disconnect()
                print("BLE disconnected")

    def _ble_thread_main(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._ble_runner())
        finally:
            loop.close()

    def _accumulator_thread_main(self):
        """
        Drains _raw_q, builds windows, pushes completed windows to _window_q.
        Runs entirely on its own thread — _buffer is never touched elsewhere.
        """
        while self._running or not self._raw_q.empty():
            # Block briefly so we don't busy-spin; collect all available rows
            batch = []
            try:
                # Wait up to 50 ms for the first item
                batch.append(self._raw_q.get(timeout=0.05))
            except queue.Empty:
                continue

            # Drain everything else that arrived in the meantime
            while True:
                try:
                    batch.append(self._raw_q.get_nowait())
                except queue.Empty:
                    break

            new_data = pd.DataFrame(batch, columns=self.columns)
            new_data = new_data.drop(columns='timestamp')
            self._roll_process_window(new_data)


    def _roll_process_window(self, new_data: pd.DataFrame):
        """Appends the data to the internal buffer. If the buffer contains enough data 
        for the next window, the window is emitted (added to the output queue). ti
        If the buffer contains multiple windows after appending new data, it emits all of them."""
        self._buffer = pd.concat([self._buffer, new_data], ignore_index=True)
        self._current_step += len(new_data)

        if self._current_step >= self.window_size:
            window = self._buffer.iloc[:self.window_size].copy() # 

            try:
                # remove the previous window, if it hasnt been accessed yet
                self._window_q.get_nowait()
            except queue.Empty:
                pass
            
            self._window_q.put_nowait(window)

            self._buffer = self._buffer.iloc[self.window_step:].reset_index(drop=True) # trim the buffer
            self._current_step -= self.window_step # reset the index

    def get_window(self, differentiate=False) -> pd.DataFrame | None:
        """
        Returns the next window or None if
        no new window is ready yet. Never blocks.
        """
        try:
            data: pd.DataFrame = self._window_q.get_nowait()
            if differentiate:
                data = diff(data, columns=['x_gyro', 'y_gyro', 'z_gyro'])
            data = data.drop(columns='timestamp')
            return data
        except queue.Empty:
            return None
    
    def start(self):
        if self._running:
            return
        self._running = True
        self._failed_event.clear()
        self._connected_event.clear()

        self._ble_thread = threading.Thread(target=self._ble_thread_main, daemon=True, name="ble")
        self._accumulator_thread = threading.Thread(target=self._accumulator_thread_main, daemon=True, name="accumulator")

        self._ble_thread.start()
        self._accumulator_thread.start()


    def stop(self):
        self._running = False
        if self._ble_thread:
            self._ble_thread.join(timeout=3.0)
        if self._accumulator_thread:
            self._accumulator_thread.join(timeout=3.0)

    def wait_until_connected(self, timeout=5.0):
        while True:
            if self._connected_event.wait(timeout=timeout):
                return True
            if self._failed_event.is_set():
                raise RuntimeError(f"BLE connection failed")
            if timeout is not None:
                timeout -= 0.05
                if timeout <= 0:
                    return False
    

if __name__ == "__main__":
    device_uuid = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
    device_name = "BLE Server Example"
    
    imu = IMUWindower(device_uuid, device_name, window_size=100, window_overlap=99)
    imu.start()

    if not imu.wait_until_connected(timeout=10.0):
        print("Could not connect")
        imu.stop()
        exit(1)

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("Shutting down")
        imu.stop()
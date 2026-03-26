import asyncio
from bleak import BleakClient, BleakScanner
import threading
import time
import pandas as pd

CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"  # Your characteristic UUID
DEVICE_NAME = "BLE Server Example"

class IMUReader:
    _current_reader = None

    def __init__(self):

        self.columns = ["timestamp", "x_accel", "y_accel", "z_accel", "x_gyro", "y_gyro", "z_gyro"]
        self.newData = pd.DataFrame(columns=self.columns)

        self.client = None

        self._lock = threading.Lock()

        self._thread = None
        self._loop = None
        self._running = False
        self._connected_event = threading.Event()
        self._failed_event = threading.Event()
        IMUReader._current_reader = self

    @staticmethod
    async def notification_handler(sender, data: bytearray):
        if not IMUReader._current_reader._running:
            return
        try:
            row = dict(zip(IMUReader._current_reader.columns, map(float, data.decode("utf-8").strip().split(","))))

            with IMUReader._current_reader._lock:
                IMUReader._current_reader.newData.loc[len(IMUReader._current_reader.newData)] = row

        except Exception as e:
            print("Read error:", e)

    async def connect(self):
        devices = await BleakScanner.discover()
        target = None
        for d in devices:
            if d.name == DEVICE_NAME:
                target = d
                break

        if target is None:
            raise RuntimeError(f"Device '{DEVICE_NAME}' not found")

        self.client = BleakClient(target.address)
        await self.client.connect()

        if not self.client.is_connected:
            raise RuntimeError("Failed to connect")

        self._connected_event.set()
        print(f"Connected to {target.name} ({target.address})")

        await self.client.start_notify(CHAR_UUID, IMUReader.notification_handler)
        print("Set notification handler for BLE characteristic")

    async def pollingLoop(self):
        while self._running:
            await asyncio.sleep(0.001)

    async def _runner(self):
        try:
            await self.connect()
            await self.pollingLoop()
        finally:
            self._failed_event.set()
            if self.client is not None and self.client.is_connected:
                await self.client.disconnect()
                print("Disconnected")

    def _thread_main(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._runner())
        finally:
            self._loop.close()
            self._loop = None

    def getData(self):
        """
        Return all samples collected since the last call, and clear the buffer.
        """
        with self._lock:
            data = self.newData.copy()
            self.newData = pd.DataFrame(columns=self.columns)
        return data

    def clearData(self):
        self.newData = pd.DataFrame(columns=self.columns)

    def start(self):
        if self._running:
            return

        self._failed_event.clear()
        self._connected_event.clear()
        self._running = True
        self._thread = threading.Thread(target=self._thread_main, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

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
    imu = IMUReader()
    imu.start()

    try:
        while True:
            time.sleep(1.0)
            samples = imu.getData()
            if samples:
                print(f"Got {len(samples)} new samples")
                print("Latest sample:", samples[-1])
            else:
                print("No new samples")
    finally:
        imu.stop()
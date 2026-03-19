import asyncio
from bleak import BleakClient, BleakScanner
import threading
import time
import pandas as pd

CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"  # Your characteristic UUID
DEVICE_NAME = "BLE Server Example"

class IMUReader:
    def __init__(self, poll_interval=0.1):
        self.newData = []
        self.client = None
        self.interval = poll_interval

        self._lock = threading.Lock()

        self._thread = None
        self._loop = None
        self._running = False

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

        print(f"Connected to {target.name} ({target.address})")

    async def pollingLoop(self):
        while self._running:
            try:
                data = await self.client.read_gatt_char(CHAR_UUID)
                # convert bytes to string if your STM32 sends ASCII CSV
                # line = data.decode('utf-8').strip()
                # values = [float(x) for x in line.split(',')]

                columns = ["timestamp", "x_accel", "y_accel", "z_accel", "x_gyro", "y_gyro", "z_gyro"]
                df = pd.DataFrame([dict(zip(columns, map(float, data.decode("utf-8").strip().split(","))))])
                print(df)

                with self._lock:
                    self.newData.append(df)

            except Exception as e:
                print("Read error:", e)

            # await asyncio.sleep(self.poll_interval)

    async def _runner(self):
        try:
            await self.connect()
            await self.pollingLoop()
        finally:
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

    def get_new_data(self):
        """
        Return all samples collected since the last call, and clear the buffer.
        """
        with self._lock:
            data = self.newData[:]
            self.newData.clear()
        return data

    def start(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._thread_main, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    # Blocking wrapper so you can just call it
    def startBlocking(self):
        asyncio.run(self.connect())
        # asyncio.run(self.readIMU())

if __name__ == "__main__":
    imu = IMUReader(poll_interval=0.01)
    imu.start()

    try:
        while True:
            time.sleep(1.0)
            samples = imu.get_new_data()
            if samples:
                print(f"Got {len(samples)} new samples")
                print("Latest sample:", samples[-1])
            else:
                print("No new samples")
    finally:
        imu.stop()
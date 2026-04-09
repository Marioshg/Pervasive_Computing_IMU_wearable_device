import asyncio
import math
import time
import random
import pandas as pd

DEVICE_NAME = "BLE Server Example"
CHAR_UUID   = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

# to use, simply replace
# from bleak import BleakClient, BleakScanner
# with
# from ble_simulator import SimBleakClient as BleakClient
# from ble_simulator import SimBleakScanner as BleakScanner

class _SimDevice:
    """Fake discovery result — same attributes BleakScanner returns."""
    def __init__(self, name: str, address: str):
        self.name    = name
        self.address = address


class SimBleakScanner:
    """Drop-in for bleak.BleakScanner.  Returns one fake device."""

    @staticmethod
    async def discover(timeout: float = 2.0) -> list[_SimDevice]:
        await asyncio.sleep(0.05)           # simulate scan latency
        return [_SimDevice(DEVICE_NAME, "AA:BB:CC:DD:EE:FF")]


class IMUSimulator:
    """
    Generates synthetic IMU data and calls the BLE notification handler
    at a configurable rate.

    Signal model
    ────────────
    Accelerometer : slow sine waves on each axis  +  small Gaussian noise
    Gyroscope     : slower sine waves             +  small Gaussian noise
    Timestamp     : real wall-clock time (seconds)

    You can subclass and override `_next_sample()` to inject your own
    waveforms (step responses, recorded replays, fault injections …).
    """

    def __init__(
        self,
        sample_rate_hz: float = 100.0,
        accel_amplitude: float = 1.0,
        gyro_amplitude: float  = 50.0,
        noise_std: float       = 0.02,
    ):
        self._rate     = sample_rate_hz
        self._a_amp    = accel_amplitude
        self._g_amp    = gyro_amplitude
        self._noise    = noise_std
        self._handler  = None
        self._running  = False
        self._task     = None
        self._t0       = time.time()

    # ── internal waveform ──────────────────────────────────────────────

    def _next_sample(self, t: float) -> dict:
        """Override to replace with recorded data or custom patterns."""
        n = lambda: random.gauss(0, self._noise)
        return {
            "timestamp": t,
            "x_accel":   self._a_amp * math.sin(2 * math.pi * 0.5  * t) + n(),
            "y_accel":   self._a_amp * math.sin(2 * math.pi * 0.75 * t + 1.0) + n(),
            "z_accel":   self._a_amp * math.cos(2 * math.pi * 0.3  * t) + n() + 9.81,
            "x_gyro":    self._g_amp * math.sin(2 * math.pi * 0.2  * t + 0.5) + n(),
            "y_gyro":    self._g_amp * math.cos(2 * math.pi * 0.15 * t) + n(),
            "z_gyro":    self._g_amp * math.sin(2 * math.pi * 0.1  * t + 2.0) + n(),
        }

    # ── background loop ────────────────────────────────────────────────

    async def _emit_loop(self):
        interval = 1.0 / self._rate
        while self._running:
            if self._handler is not None:
                t       = time.time() - self._t0
                sample  = self._next_sample(t)
                payload = ",".join(f"{sample[k]:.6f}" for k in [
                    "timestamp",
                    "x_accel", "y_accel", "z_accel",
                    "x_gyro",  "y_gyro",  "z_gyro",
                ])
                await self._handler(CHAR_UUID, bytearray(payload.encode()))
            await asyncio.sleep(interval)

    def start(self, loop: asyncio.AbstractEventLoop):
        self._running = True
        self._task    = loop.create_task(self._emit_loop())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()


class SimBleakClient:
    """
    Drop-in for bleak.BleakClient.

    Identical public interface:
        await client.connect()
        client.is_connected          → bool
        await client.start_notify(uuid, handler)
        await client.disconnect()
    """

    def __init__(self, address: str, sample_rate_hz: float = 100.0, **kwargs):
        self.address      = address
        self.is_connected = False
        self._simulator   = IMUSimulator(sample_rate_hz=sample_rate_hz)
        self._loop        = None

    async def connect(self):
        await asyncio.sleep(0.1)            # simulate connection latency
        self.is_connected = True
        self._loop        = asyncio.get_event_loop()
        print(f"[SIM] Connected to simulated device ({self.address})")

    async def start_notify(self, char_uuid: str, handler):
        if not self.is_connected:
            raise RuntimeError("[SIM] Not connected")
        self._simulator._handler = handler
        self._simulator.start(self._loop)
        print(f"[SIM] Notifications started on {char_uuid}")

    async def stop_notify(self, char_uuid: str):
        self._simulator.stop()

    async def disconnect(self):
        self._simulator.stop()
        self.is_connected = False
        print("[SIM] Disconnected")
        

# Replay a CSV recording
class ReplaySimulator(IMUSimulator):
    def __init__(self, csv_path, **kw):
        super().__init__(**kw)
        self._df = pd.read_csv(csv_path)
        self._i  = 0

    def _next_sample(self, t):
        row = self._df.iloc[self._i % len(self._df)].to_dict()
        self._i += 1
        return row

import asyncio
from bleak import BleakClient, BleakScanner
import time

CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"  # Your characteristic UUID

async def read_imu():
    devices = await BleakScanner.discover()
    target = None
    for d in devices:
        if "BLE Server Example" == d.name:
            target = d
            break
    if not target:
        print("Device not found")
        return

    async with BleakClient(target.address) as client:
        print(f"Connected to {target.name} ({target.address})")
        while True:
            try:
                data = await client.read_gatt_char(CHAR_UUID)
                # convert bytes to string if your STM32 sends ASCII CSV
                line = data.decode('utf-8').strip()
                print("Raw data:", line)
                values = [float(x) for x in line.split(',')]
                ax, ay, az, gx, gy, gz = values
                print(f"Accel: {ax:.2f}, {ay:.2f}, {az:.2f} | Gyro: {gx:.2f}, {gy:.2f}, {gz:.2f}")
            except Exception as e:
                print("Read error:", e)
            time.sleep(0.1)  # adjust polling rate

# Blocking wrapper so you can just call it
def read_imu_blocking():
    asyncio.run(read_imu())

if __name__ == "__main__":
    read_imu_blocking()
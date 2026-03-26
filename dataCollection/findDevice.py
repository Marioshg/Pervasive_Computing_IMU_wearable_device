import asyncio
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "BLE Server Example"

async def find_uuids():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=5.0)
    target = None
    for d in devices:
        print(f"Found: {d.name}, {d.address}")
        if d.name == DEVICE_NAME:
            target = d
            break

    if not target:
        print("Device not found!")
        return

    async with BleakClient(target.address) as client:
        if not client.is_connected:
            print("Failed to connect!")
            return

        print(f"Connected to {target.name} ({target.address})")
        
        # Access services after connection
        for service in client.services:
            print(f"Service: {service.uuid}")
            for char in service.characteristics:
                print(f"  Characteristic: {char.uuid} | properties: {char.properties}")

asyncio.run(find_uuids())
#include "FastIMU.h"
#include "EEPROM.h"
#include <Wire.h>

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define IMU_ADDRESS 0x68
MPU6500 IMU;

calData calib = { 0 };
AccelData accelData;
GyroData gyroData;

BLECharacteristic *pCharacteristic;

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

void setup() {

  Serial.begin(115200);

  // IMU setup
  Wire.begin();
  Wire.setClock(400000);

  int err = IMU.init(calib, IMU_ADDRESS);
  if (err != 0) {
    Serial.println("IMU init failed");
    while(true);
  }

  Serial.println("IMU ready");

  // BLE setup
  BLEDevice::init("BLE Server Example");

  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);

  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ |
                      BLECharacteristic::PROPERTY_NOTIFY
                    );

  pCharacteristic->addDescriptor(new BLE2902());

  pService->start();

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();

  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);  // helps with iPhone compatibility
  pAdvertising->setMinPreferred(0x12);

BLEDevice::startAdvertising();

  Serial.println("BLE ready and Advertising...");
}

void loop() {

  IMU.update();

  IMU.getAccel(&accelData);
  IMU.getGyro(&gyroData);

  char buffer[120];
  unsigned long t = millis();

  sprintf(buffer,"%lu,%f,%f,%f,%f,%f,%f",
      t,
      accelData.accelX,
      accelData.accelY,
      accelData.accelZ,
      gyroData.gyroX,
      gyroData.gyroY,
      gyroData.gyroZ);

  Serial.println(buffer);   // still print locally

  pCharacteristic->setValue(buffer);
  pCharacteristic->notify();

  delay(50);
}
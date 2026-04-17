# Pervasive_Computing_IMU_wearable_device
This is a Repository created for the Course of Pervasive Computing. The goal is to program an STM32 with an IMU sensor device to perfomr head movement classification using Machine Learning Technics

The BLE server for IMU data collection can be found in `arduino/esp32_IMU/esp32_IMU.ino`. This server simply collects raw IMU data and transmits it over Bluetooth.

The data collection tool can be found in `dataCollection/main.py`. When run, it connects to the bluetooth server, reads which gestures it needs to record from the `gestures.json` file, and stores the raw IMU data as a `.csv` file.

The GUI application can be started by running `receiverApplication/gestureHandler.py`. This file connects to the bluetooth server, starts processing incoming data, feeds the data into the model, and inserts inputs into the given application.

The code for training the Decision Tree can be found in the `dt/` folder and the LSTM training code can be found in the `tf-lite/` folder.

The anonymised IMU sensor data can be found in the `data\` folder. 
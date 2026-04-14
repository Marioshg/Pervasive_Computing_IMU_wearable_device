# TODO: Code
import json
import time

import pygetwindow as gw
import pyautogui
import tkinter as tk

import sys

from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from imu_window import IMUWindower

from receiverApplication.inference.inference_factory import InferenceFactory
from dataCollection.IMUReadings import IMUReader


class DummyConnection:
	def __init__(self):
		return

class DummyModel:
	def __init__(self, connection):

		self.connection = connection
		self.helloWorld = ["look_left", "look_right", "look_up", "look_up", "look_down", "tilt_left", "look_down",
		                   "tilt_right", "look_up", "extra_value_to_complete_hello_world"]
		self.cnt = 0

	def getGesture(self):
		time.sleep(0.2)

		try:
			gesture = self.helloWorld[self.cnt]
			self.cnt += 1
			return gesture
		except:
			return None


class GestureMapping:
	def __init__(self, mappingName):
		mappingFile = json.load(open(mappingName))
		self.mapping = mappingFile["gestures"]
		self.target = mappingFile["application"]

	def executeGesture(self, gesture):
		"""
		The function responsible for executing gestures
		"""
		if (gesture is not None and gesture != 'none') and gw.getWindowsWithTitle(self.target) != []:
			newInput = self.mapping[gesture]
			gw.getWindowsWithTitle(self.target)[0].activate()
			pyautogui.press(newInput)

class Manager:
	def __init__(self, mapping, model):
		self.model = model
		self.mapping = mapping

	def getGesture(self):
		newGesture = self.model.getGesture()
		self.mapping.executeGesture(newGesture)
		return newGesture

	def isTargetRunning(self):
		return True if (gw.getWindowsWithTitle(self.mapping.target) != []) else False

	def isConnected(self):
		# Assume that we are connected if this is not None
		return self.model is not None

class AppGui:
	def __init__(self, manager):

		self.manager = manager

		self.root = tk.Tk()
		self.root.title("GestureMapper")

		# Set up event loop until application is closed
		self.root.done = False
		self.root.protocol("WM_DELETE_WINDOW", lambda: setattr(self.root, 'done', True))

		# applicationList = list(set(gw.getAllTitles()))
		# self.opt = tk.StringVar(value=applicationList[0])
		# tk.OptionMenu(self.root, self.opt, *applicationList).pack()

		# # Have a button to connect to the BLE device
		# def connectBle():
		# 	if self.manager.setConnection(DummyConnection()):
		# 		self.eventList.insert(tk.END, f"Connected to 'Dummy Connection'")
		# 		self.hasBle = True
		# 		self.bleTextVar.set(self.bleText[0])
		# 	else:
		# 		self.eventList.insert(tk.END, f"Failed to connect to 'Dummy Connection'")
		# 		self.hasBle = False
		# 		self.bleTextVar.set(self.bleText[1])
		# 	self.eventList.yview(tk.END)

		def connectTarget():
			running = self.manager.isTargetRunning()
			if running:
				self.eventList.insert(tk.END, f"Connected with '{self.manager.mapping.target}' application!")
				self.hasTarget = True
				self.targetTextVar.set(self.targetText[0])
			else:
				self.eventList.insert(tk.END, f"Target application '{self.manager.mapping.target}' not running")
				self.hasTarget = False
				self.targetTextVar.set(self.targetText[1])
			self.eventList.yview(tk.END)


		# def addBleButton():
		# 	# Buttons+text for connecting bluetooth
		# 	frame = tk.Frame(self.root)
		# 	frame.pack(side=tk.TOP, anchor="w")
		#
		# 	bleConnect = tk.Button(frame, text="Connect Bluetooth", command=connectBle)
		# 	bleConnect.pack(side=tk.LEFT, anchor="w")
		#
		# 	textVar = tk.StringVar()
		# 	statusText = tk.Label(frame, textvariable=textVar)
		# 	statusText.pack(side=tk.LEFT, padx=5)
		# 	return textVar

		def addTargetButton():
			frame = tk.Frame(self.root)
			frame.pack(side=tk.TOP, anchor="w")

			appConnect = tk.Button(frame, text="Connect Application", command=connectTarget)
			appConnect.pack(side=tk.LEFT, anchor="w")

			textVar = tk.StringVar()
			statusText = tk.Label(frame, textvariable=textVar)
			statusText.pack(side=tk.LEFT, padx=5)
			return textVar

		# self.bleTextVar = addBleButton()
		# self.hasBle = False
		# self.bleText = ["🟢 Bluetooth connected", "🔴 Bluetooth not connected"]
		# self.bleTextVar.set(self.bleText[1])

		self.targetTextVar = addTargetButton()
		self.hasTarget = False
		self.targetText = ["🟢 Target application running", "🔴 Target application not running"]
		self.targetTextVar.set(self.targetText[1])

		self.scrollbar = tk.Scrollbar(self.root)
		self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

		self.eventList = tk.Listbox(self.root, width=50, height=20, yscrollcommand=self.scrollbar.set)
		self.eventList.pack(side=tk.LEFT, fill=tk.BOTH)

		self.scrollbar.config(command=self.eventList.yview)

	def applicationLoop(self):
		while not self.root.done:
			# if self.hasTarget and self.hasBle:
			if self.hasTarget:
				gesture = self.manager.getGesture()

				if gesture is not None:
					self.eventList.insert(tk.END, f"Received [{gesture}] gesture")
					self.eventList.yview(tk.END)

			self.root.update()

WINDOW_LENGTH = 1000 # ms
WINDOW_LATENCY = 100 # ms

WINDOW_SIZE = int(WINDOW_LENGTH / 10)
WINDOW_OVERLAP = WINDOW_SIZE - int(WINDOW_LATENCY / 10)

def startImuWindower(window_size=WINDOW_SIZE, window_overlap=WINDOW_OVERLAP):
	device_uuid = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
	device_name = "BLE Server Example"

	imu = IMUWindower(device_uuid, device_name, window_size=window_size, window_overlap=window_overlap)
	imu.start()

	if not imu.wait_until_connected(timeout=30.0):
		print("Could not connect")
		imu.stop()
		exit(1)

	# try:
	# 	while True:
	# 		time.sleep(1.0)
	# except KeyboardInterrupt:
	# 	print("Shutting down")
	# 	imu.stop()

	return imu

def startInference(dataProvider):
	inference = InferenceFactory.lstm(data_provider=dataProvider)
	inference.start()
	return inference

if __name__ == "__main__":

	# Dummy test classes
	# imu = DummyConnection()
	#

	imu = startImuWindower()
	# model = DummyModel(imu)
	model = startInference(dataProvider=imu.get_window)


	mapping = GestureMapping(mappingName="Thonny_mapping.json")
	app = Manager(mapping=mapping, model=model)

	g = AppGui(app)
	g.applicationLoop()

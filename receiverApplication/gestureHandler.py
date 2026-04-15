# TODO: Code
import json
import time

import pygetwindow as gw
import pyautogui
import tkinter as tk
from collections import deque, Counter
import time
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

class GestureSmoother:
    def __init__(
        self,
        min_count=3,
        timeframe_s=0.7,
        cooldown_s=0.8,
        require_neutral_between_opposites=True,
        ignore_classes=None,
        opposites=None,
    ):
        self.min_count = min_count
        self.timeframe_s = timeframe_s
        self.cooldown_s = cooldown_s
        self.require_neutral_between_opposites = require_neutral_between_opposites
        self.ignore_classes = set(ignore_classes or ["none"])

        self.opposites = opposites or {
            "look_up": "look_down",
            "look_down": "look_up",
            "look_left": "look_right",
            "look_right": "look_left",
            "tilt_left": "tilt_right",
            "tilt_right": "tilt_left",
        }

        self.events = deque()
        self.last_emitted_gesture = None
        self.last_emit_time = 0.0
        self.neutral_seen_since_last_event = True

    def update(self, gesture):
        now = time.monotonic()

        if gesture is None:
            return None

        self.events.append((now, gesture))

        cutoff = now - self.timeframe_s
        while self.events and self.events[0][0] < cutoff:
            self.events.popleft()

        if gesture in self.ignore_classes:
            self.neutral_seen_since_last_event = True
            return None

        counts = Counter(g for _, g in self.events if g not in self.ignore_classes)

        if counts[gesture] < self.min_count:
            return None

        if (
            self.last_emitted_gesture == gesture
            and (now - self.last_emit_time) < self.cooldown_s
        ):
            return None

        if self.require_neutral_between_opposites:
            opposite_of_last = self.opposites.get(self.last_emitted_gesture)
            if (
                gesture == opposite_of_last
                and not self.neutral_seen_since_last_event
            ):
                return None

        self.last_emitted_gesture = gesture
        self.last_emit_time = now
        self.neutral_seen_since_last_event = False
        self.events.clear()
        return gesture

class Manager:
	def __init__(self, mapping, model, smoother=None):
		self.model = model
		self.mapping = mapping
		self.smoother = smoother

	def getGesture(self):
		raw_gesture = self.model.getGesture()

		if self.smoother is not None:
			detected_gesture = self.smoother.update(raw_gesture)
		else:
			detected_gesture = raw_gesture

		self.mapping.executeGesture(detected_gesture)
		return detected_gesture

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
WINDOW_LATENCY = 50 # ms

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

	smoother = GestureSmoother(
		min_count=8,
		timeframe_s=0.7,
		cooldown_s=1.2,
		ignore_classes=["none"],
	)

	app = Manager(mapping=mapping, model=model, smoother=smoother)

	g = AppGui(app)
	g.applicationLoop()

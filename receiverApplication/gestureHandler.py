# TODO: Code
import json
import time

import pygetwindow as gw
import pyautogui
import tkinter as tk

class DummyConnection:
	def __init__(self):
		self.helloWorld = ["look_left", "look_right", "look_up", "look_up", "look_down", "tilt_left", "look_down",
		                   "tilt_right", "look_up", "extra_value_to_complete_hello_world"]
		self.cnt = 0

	def checkReceive(self):
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
		if gesture is not None and gw.getWindowsWithTitle(self.target) != []:
			newInput = self.mapping[gesture]
			gw.getWindowsWithTitle(self.target)[0].activate()
			pyautogui.press(newInput)

		# currentActive = gw.getActiveWindow()
		# currentActive.activate()

class Manager:
	def __init__(self, mapping):
		self.connection = None
		self.mapping = mapping

	def setConnection(self, connection):
		# TODO: actual connecting logic for the real thing
		self.connection = connection
		return True

	def receive(self):
		newGesture = self.connection.checkReceive()
		self.mapping.executeGesture(newGesture)
		return newGesture

	def isTargetRunning(self):
		return True if (gw.getWindowsWithTitle(self.mapping.target) != []) else False


class AppGui:
	def __init__(self, manager):

		self.manager = manager

		self.root = tk.Tk()
		self.root.title("GestureMapper")

		# Set up event loop until application is closed
		self.root.done = False
		self.root.protocol("WM_DELETE_WINDOW", lambda: setattr(self.root, 'done', True))

		# Have a button to connect to the BLE device
		def connectBle():
			if self.manager.setConnection(DummyConnection()):
				self.eventList.insert(tk.END, f"Connected to 'Dummy Connection'")
				self.eventList.yview(tk.END)
				self.hasBle = True
				self.bleTextVar.set(self.bleText[0])
			else:
				self.eventList.insert(tk.END, f"Failed to connect to 'Dummy Connection'")
				self.eventList.yview(tk.END)
				self.hasBle = False
				self.bleTextVar.set(self.bleText[1])

		def connectTarget():
			running = self.manager.isTargetRunning()
			if running:
				self.eventList.insert(tk.END, f"Connected with '{self.manager.mapping.target}' application!")
				self.eventList.yview(tk.END)
				self.hasTarget = True
				self.targetTextVar.set(self.targetText[0])
			else:
				self.eventList.insert(tk.END, f"Target application '{self.manager.mapping.target}' not running")
				self.eventList.yview(tk.END)
				self.hasTarget = False
				self.targetTextVar.set(self.targetText[1])

		def addBleButton():
			# Buttons+text for connecting bluetooth
			frame = tk.Frame(self.root)
			frame.pack(side=tk.TOP, anchor="w")

			bleConnect = tk.Button(frame, text="Connect Bluetooth", command=connectBle)
			bleConnect.pack(side=tk.LEFT, anchor="w")

			textVar = tk.StringVar()
			statusText = tk.Label(frame, textvariable=textVar)
			statusText.pack(side=tk.LEFT, padx=5)
			return textVar

		def addTargetButton():
			frame = tk.Frame(self.root)
			frame.pack(side=tk.TOP, anchor="w")

			appConnect = tk.Button(frame, text="Connect Application", command=connectTarget)
			appConnect.pack(side=tk.LEFT, anchor="w")

			textVar = tk.StringVar()
			statusText = tk.Label(frame, textvariable=textVar)
			statusText.pack(side=tk.LEFT, padx=5)
			return textVar

		self.bleTextVar = addBleButton()
		self.hasBle = False
		self.bleText = ["🟢 Bluetooth connected", "🔴 Bluetooth not connected"]
		self.bleTextVar.set(self.bleText[1])

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
			if self.hasTarget and self.hasBle:
				gesture = self.manager.receive()

				if gesture is not None:
					self.eventList.insert(tk.END, f"Received [{gesture}] gesture")
					self.eventList.yview(tk.END)

			self.root.update()


if __name__ == "__main__":
	mapping = GestureMapping(mappingName="Thonny_mapping.json")
	app = Manager(mapping=mapping)

	g = AppGui(app)
	g.applicationLoop()

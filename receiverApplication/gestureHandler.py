# TODO: Code
import time

import pygetwindow as gw
import pyautogui


class DummyConnection:
	def __init__(self):
		self.helloWorld = ["look_left", "look_right", "look_up", "look_up", "look_down", "tilt_left", "look_down",
		                   "tilt_right", "look_up", "extra_value_to_complete_hello_world"]
		self.cnt = 0

	def checkReceive(self):
		time.sleep(0.1)

		try:
			gesture = self.helloWorld[self.cnt]
			self.cnt += 1
			return gesture
		except:
			return None


class GestureMapping:
	def __init__(self):
		pass

	def loadMapping(self, mappingName):
		pass

	def executeGesture(self):
		pass

class Manager:
	def __init__(self, target,  mapping, connection, mode=None):
		self.connection = connection
		self.targetApplication = target
		self.mapping = mapping
		self.mode = mode

	def receiveLoop(self):
		while True:
			newGesture = self.connection.checkReceive()

			if newGesture is not None:
				print(f"received [{newGesture}] gesture")
				self._inputFromGesture(newGesture)

	def _inputFromGesture(self, gesture):
		newInput = self.mapping[gesture]
		currentActive = gw.getActiveWindow()
		gw.getWindowsWithTitle(self.targetApplication)[0].activate()
		pyautogui.press(newInput)
		# currentActive.activate()


if __name__ == "__main__":
	targetApplication = "Thonny"
	gestureMapping = {
		"look_left": "H",
		"look_right": "E",
		"look_up": "L",
		"look_down": "O",
		"tilt_left": "W",
		"tilt_right": "R",
		"extra_value_to_complete_hello_world": "D"
	}
	connection = DummyConnection()

	app = Manager(target=targetApplication, mapping=gestureMapping, connection=connection)

	app.receiveLoop()

	# # time.sleep(1)
	# active = gw.getActiveWindow()
	# print(active)
	#
	# win = gw.getWindowsWithTitle("Thonny")[0]
	# win.activate()  # bring to foreground
	#
	# pyautogui.press("H")
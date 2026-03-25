import time
import os
import pandas as pd
import numpy as np
from pathlib import Path
import json

from IMUReadings import IMUReader
from imusignal import IMUSignal

def get_highest_run(folder, gesture):
	"""
	Looks through existing files and returns the highest run number of a specific gesture
	"""
	folder = Path(folder)
	if not folder.exists():
		return 0

	return max(
		(
			int(f.stem.rsplit("_", 1)[1])
			for f in folder.iterdir()
			if f.is_file() and f.stem.startswith(f"{gesture}_")
		),
		default=0,
	)

def getColour(colour, text):
	colourDict = {
		"RED": '\033[91m',
		"GREEN": '\033[92m',
		"BLUE": '\033[94m',
		"WHITE": '\033[0m',
	}
	return f"{colourDict[colour]}{text}{colourDict['WHITE']}"

class DummyData:
	def __init__(self):
		self.n = 0
		self.valuesPerCall = 10
		self.columnLabels = ["timestamp", "x_accel", "y_accel", "z_accel", "x_gyro", "y_gyro", "z_gyro"]

	def getData(self):
		dummyData = {}

		# Fill all columns with random values
		for i in self.columnLabels:
			dummyData[i] = np.random.uniform(-1,1,self.valuesPerCall)

		# Overwrite timestamp because lazy
		dummyData["timestamp"] = np.arange(self.n, self.n + self.valuesPerCall)
		self.n += self.valuesPerCall

		time.sleep(0.05)

		return pd.DataFrame(dummyData)


class Recorder:
	def __init__(self, user, gestures, dataSource):
		"""
		:param user: String or number indicating a specific user
		:param gestures: List of gestures to execute
		:param dataSource: Function to get data from
		"""

		self.user = user
		self.gestures = gestures
		self.dataSource = dataSource

		# Create directory if it doesn't exist yet
		os.makedirs(f"data/{self.user}", exist_ok=True)

		print(f"Configured recorder for {getColour('GREEN', self.user)}")
		print(f"Recording {len(self.gestures)} different gestures")

	def run(self):
		"""
		Main loop that runs through all gestures the given amount of times.
		"""

		# Repeat for all gestures gives
		for gesture, gestureData in self.gestures.items():
			instruction = gestureData["instructions"]
			duration = gestureData["duration"]
			repeats = gestureData["repeats"]
			pauseTime = gestureData["pause"]

			print(f"\r\n{getColour('GREEN', gesture)} gesture")
			print(f"\t{instruction}")
			print(f"\trepeats={repeats}, duration={duration}, pause={pauseTime}")
			input("\tPress Enter to start")
			print()

			# If we already have data, get the highest number
			startingRun = get_highest_run(f"data/{self.user}", gesture)

			# Repeat self.repeats times
			for repeat in range(1, repeats + 1):
				print(f"{getColour('GREEN', '🟢')} {gesture} - {repeat}/{repeats}")

				signal = self._gesture(duration)

				# TODO do enrichment in the IMUSignal class
				enriched = self._processData(signal)
				self._saveData(gesture, startingRun + repeat, enriched)

				# Optional pause between recordings
				if pauseTime > 0:
					print(f"\tPausing for {pauseTime} seconds, return to the starting position")
					time.sleep(pauseTime)


	def _printProgressBar(self, current, duration):
		totalBars = 10

		# Draw the progress bar
		nBars = int((totalBars * current) / duration) + 1
		nEmpty = totalBars - nBars
		barStr = f"[{nBars * '█'}{nEmpty * ' ' }]"

		# Draw the timer
		timerStr = f"{current if current <= duration else duration:.2f}s/{duration:.2f}s"

		print(f"\r\t{barStr} - {timerStr} ", end='', flush=True)

	def _gesture(self, duration):
		startTime = time.time()
		self.dataSource.clearData()

		signal = IMUSignal()
  
		# Loop for self.duration seconds
		while time.time() <= startTime + duration:
			newData = self.dataSource.getData()
			if not newData.empty:
				signal.append(newData)
			# imu_df = pd.concat([imu_df, newData], ignore_index=True)
			self._printProgressBar(time.time() - startTime, duration)

		print(f"\n\tCollected {signal.length()} samples")
		return signal


	def _processData(self, data):
		# TODO: Enrich data (Add extra fields as desired e.g total, average
		return data

	def _saveData(self, gesture, number, data):
		fileName = f"data/{self.user}/{gesture}_{number}.csv"

		print(f"\tSaving {fileName}")
		data.to_csv(fileName, index=False, float_format="%.4f")


if __name__ == "__main__":
	# Connect with the BLE server and start polling for data
	imu = IMUReader()
	imu.start()
	imu.wait_until_connected()

	# Open the gestures
	gestureDict = json.load(open("gestures.json"))

	# configure and run the recorder
	r = Recorder(user="User", gestures=gestureDict, dataSource=imu)
	r.run()

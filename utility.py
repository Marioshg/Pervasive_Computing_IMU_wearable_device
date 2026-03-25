from os import listdir
from os.path import isfile, join, basename
from os import walk
import re


def getUsers(path="data"):
	""""
	Dataset is sorted by user using folder names. This function returns a list of folders
	"""
	f = []
	for (dirpath, dirnames, filenames) in walk(path):
		f.extend(dirnames)
		break
	
    # remove original sample data since it is not properly recorded
	if 'sample_test' in f:
		f.remove('sample_test')

	return f

def sortByGesture(recordings):
	"""
	Creates a dictionary of recordings, sorted by gesture
	"""
	gestureDict = {}
	for recording in recordings:
		noNumber = re.sub(r'_\d+(?:\.[^.]+)?$', '', basename(recording))
		gestureDict.setdefault(noNumber, []).append(recording)

	return gestureDict


class DataOrganiser:
	def __init__(self, baseFolder="data"):
		self.baseFolder = baseFolder

		self.users = getUsers(path=baseFolder)
		self.recordingList = []
		self.recordingDictByUser = {}
		self._loadRecordings()
		self.recordingDictByGesture = sortByGesture(self.recordingList)

	def _loadRecordings(self):
		"""
		Creates a list of all recordings and creates a dict of recordings, sorted by user
		"""
		for user in self.users:
			folder = f"{self.baseFolder}/{user}"

			recordings = [f"{folder}/{f}" for f in listdir(folder) if isfile(join(folder, f))]

			self.recordingList += recordings
			self.recordingDictByUser[user] = recordings

	def printInfo(self):
		print(f"Got a total of {len(self.recordingList)} recordings "
		      f"of {len(self.recordingDictByGesture)} different gestures "
		      f"by {len(self.recordingDictByUser)} different users")

		print(f"Breakdown per user:")
		for user in self.recordingDictByUser:
			print(f"\t{user} has: {len(self.recordingDictByUser[user])} recordings of {len(sortByGesture(self.recordingDictByUser[user]))} unique gestures")
		print()
		# print(f"Breakdown per gesture")
		# for gesture in self.recordingDictByGesture:
		# 	print(f"\t{gesture} has been recorded {len(self.recordingDictByGesture[gesture])} times")


def combineClasses(dictByGesture):
	newDict = {}
	baseGestures = [
		"look_left",
		"look_right",
		"look_up",
		"look_down",
		"tilt_left",
		"tilt_right",
		"shake_leftright",
		"shake_rightleft",
		"behind_left",
		"behind_right",
		"nod",
		"music_beat",
		"look_around",
		"look_direction",
		"idle",
		"walk",
		"jump",
		"sit_down",
		"get_up",
	]
	for i in dictByGesture:
		pass


if __name__ == "__main__":
	d = DataOrganiser("data")
	# print(f"List of recordings: {d.recordingList}")
	# print(f"Dict of recordings by user: {d.recordingDictByUser}")
	# print(f"Dict of recordings by gesture: {d.recordingDictByGesture}")

	d.printInfo()

	# Get just the recordings by Marios
	print(f"Recordings by Marios: {d.recordingDictByUser['Marios']}")

	# Get all the 'look_left' recordings
	print(f"look_left recordings: {d.recordingDictByGesture['look_left']}")



from os import listdir
from os.path import isfile, join
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
	return f

def getUserRecordings(folder="sample_test"):
	"""
	Returns a list of recorded files found in the given userfolder
	"""
	return [f for f in listdir(folder) if isfile(join(folder, f))]

def examineRecordings(recordingList):
	"""
	Returns a dict of unique gestures and the amount of recordings for that gesture
	"""
	gestureDict = {}

	# Count how much of each gesture there is
	for i in recordingList:
		new_name = re.sub(r'_\d+(?:\.[^.]+)?$', '', i)
		gestureDict[new_name] = gestureDict.get(new_name, 0) + 1

	return gestureDict

class DataOrganiser:
	def __init__(self, baseFolder="data"):
		self.baseFolder = baseFolder

		self.users = getUsers(path=baseFolder)

		self.recordingList = []
		self.recordingDictByUser = {}
		self.recordingDictByGesture = {}

		print(f"Found {len(self.users)} user folders: {self.users}")

	def getRecordings(self):
		for user in self.users:
			folder = f"{self.baseFolder}/{user}"
			[self.recordingList.append(f"{folder}/{f}") for f in listdir(folder) if isfile(join(folder, f))]


if __name__ == "__main__":
	d = DataOrganiser("data")
	d.getRecordings()
	print(d.recordingList)
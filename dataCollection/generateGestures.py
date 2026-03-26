import json

def generateGestures():
	defaultDuration = 3
	fastDuration = 2
	defaultRepeats = 10
	noPause = 0
	defaultPause = 1

	baseGestures = {
		"look_left": "Rotate your head left in a {speed} movement{ret}",
		"look_right": "Rotate your head right in a {speed} movement{ret}",
		"look_up": "Rotate your head up in a {speed} movement{ret}",
		"look_down": "Rotate your head down in a {speed} movement{ret}",
		"tilt_left": "Tilt your head left in a {speed} movement{ret}",
		"tilt_right": "Tilt your head right in a {speed} movement{ret}",

		"shake_leftright": "look left, then right in a {speed} movement{ret}",
		"shake_rightleft": "look right, then left in a {speed} movement{ret}",
		"behind_left": "Look behind you in a {speed} leftwards motion{ret}",
		"behind_right": "Look behind you in a {speed} rightwards motion{ret}",
	}

	speed_mod = ["", "fast"]
	return_mod = ["", "return"]

	gestureDict = {}

	# Generate base gestures with speed and return modifiers
	for name, template in baseGestures.items():
		for speed in speed_mod:
			for ret in return_mod:
				key = "_".join(filter(None, [name, speed, ret]))
				instructions = template.format(
					speed=speed or "smooth",
					ret=", then return to a neutral position" if ret else ""
				)
				duration = fastDuration if speed == "fast" else defaultDuration
				pause = noPause if ret else defaultPause
				gestureDict[key] = {
					"instructions": instructions,
					"duration": duration,
					"repeats": defaultRepeats,
					"pause": pause
				}

	otherGestures = {
		"nod": "repeatedly nod your head for 1-2 seconds",
		"music_beat": "Repeatedly nod to the beat",
		"look_around": "Move your head in random directions",
		"look_direction": "Move your head to a random direction and stay still",
		"idle": "Don't really move at all",
		"walk": "Walk around",
		"jump": "Jump once per recording",
		"sit_down": "Start standing up, sit down on a chair",
		"get_up": "Start sitting down, get out of a chair",
	}
	for name, instr in otherGestures.items():
		gestureDict[name] = {
			"instructions": instr,
			"duration": defaultDuration,
			"repeats": defaultRepeats * 2,
			# Note: If we have more with custom values, add them manually maybe?
			"pause": defaultPause if name not in ["sit_down", "get_up"] else 2
		}

	# Save to JSON
	with open("./dataCollection/gestures.json", "w") as f:
		json.dump(gestureDict, f, indent=4)


if __name__ == "__main__":
	generateGestures()

	f = open("./dataCollection/gestures.json")
	data =  json.load(f)

	for i in data:
		print(f"{i}: {data[i]},")
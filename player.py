# player.py


class Player(object):
	"""Class for the player. Includes stats and actions."""

	def __init__(self, race="human"):
		"""Setting stats and variables"""

		#self.race = race
		self.loc = [int((DUN_W - 1) / 2), int((DUN_H - 1) / 2)]
		self.floor = None
		self.max_health = DEFAULT_MAX_HEALTH
		self.health = self.max_health
		self.damage = DEFAULT_DAMAGE
		self.defence = 0
		self.experiance = 0
		self.lvl = 1
		self.inven = {"gold": Gold(amount=STARTING_GOLD)}
		self.equipment = {}

	def move(self, dir):
		"""Player movement on map function"""

		# this is mostly redundent except for the starting room
		dun[self.loc[0]][self.loc[1]].visited = True

		if dir == "north" and self.loc[1] > 0:   # up
			self.loc[1] -= 1
			disp.move("player", 0, -1 * SMH)
		elif dir == "south" and self.loc[1] < DUN_H-1:  # down
			self.loc[1] += 1
			disp.move("player", 0, SMH)
		elif dir == "west" and self.loc[0] > 0:  # left
			self.loc[0] -= 1
			disp.move("player", -1 * SMW, 0)
		elif dir == "east" and self.loc[0] < DUN_W-1:  # right
			self.loc[0] += 1
			disp.move("player", SMW, 0)

		dun[self.loc[0]][self.loc[1]].enter()

		dun[self.loc[0]][self.loc[1]].visited = True
		
		
		disp.itemconfig(
			str(self.loc[0]) + "," + str(self.loc[1]),
			fill="yellow")
		disp.itemconfig(
			str(self.loc[0]) + "," + str(self.loc[1]),
			fill="yellow")

	def disp_in(self):
		"""Display the player's inventory"""

		hold = ""
		for key, val in self.inven.items():
			hold += "\n" + str(key).title() + ": " + str(val.amount)
		out.config(text=hold[1:])

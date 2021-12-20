
def def_Floor():
	class Floor(object):
		"""Whole floor of the dungeon"""

		def __init__(self, floor: int, upstairs=None) -> None:
			"""Create a floor and populate it"""

			x = 9

			self.stairs = False

			self.floor_num: int = floor
			self.dun: list[list["Room"]] = []
			if x:
				print("test")
			if isinstance(x, int):
				for i in range(DUN_W):  # map generation
					column: list["Room"] = []
					for k in range(DUN_H):
						column.append(
							Room(
								int(
									(
										abs(i - (DUN_W - 1) // 2)
										+ abs(k - (DUN_H - 1) // 2)
									)
									* 1.5
									* DISTANCE_DIFF
									+ 150 * self.floor_num
								),
								{"x": i, "y": k, "floor": self.floor_num},
							)
						)

	return Floor

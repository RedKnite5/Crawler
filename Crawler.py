"""The main Crawler game"""

from __future__ import annotations

import random
from functools import total_ordering
from math import atan, pi, exp
import os
from typing import (TYPE_CHECKING,
					Callable,
					Sequence,
					ClassVar,
					TypeVar,
					Iterator,
					Type)

from PIL import Image  # type: ignore
from PIL import ImageOps  # type: ignore
from PIL import ImageTk  # type: ignore

from GUI import GUI
from inven import Inventory
from errors import *
from config import *


#   python Crawler.py

# ToDo: Unequip stuff
# ToDo: store equipment differently
# TODo: tests

if TYPE_CHECKING:
	Space = tuple[str, int]


class Dungeon(object):
	"""Contains the Rooms in a structured way"""

	def __init__(self) -> None:
		self.floors: list['Floor'] = [Floor(0)]
		self.floor_num: int = 0

	@property
	def current_floor(self) -> Floor:
		return self.floors[self.floor_num]

	def __getitem__(self, index: int) -> 'Floor':
		return self.floors[index]

	def gen_floor(self, up_stair_location: dict[str, int], level: str ="+1") -> None:
		"""Create the next single floor of the dungeon"""

		if level[0] == "+" and level[1:].isdigit():
			new_floor_num = self.floor_num + int(level[1:])
		else:
			new_floor_num = int(level)

		self.floors.append(Floor(new_floor_num, up_stair_location))

	def check_all_rooms(self) -> bool:
		"""Check if all rooms have been visited"""

		for row in self.current_floor:
			for room in row:
				if not room.visited:
					return False
		return True


class Floor(object):
	"""Whole floor of the dungeon"""

	def __init__(self, floor: int, upstairs: dict[str, int] | None = None) -> None:
		"""Create a floor and populate it"""
		
		if floor < 0:
			return
		
		self.stairs = False

		self.floor_num: int = floor
		self.dun: list[list['Room']] = []
		for i in range(DUN_W):  # map generation
			column: list['Room'] = []
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
			self.dun.append(column)

		center_room: 'Room' = self.dun[(DUN_W - 1) // 2][(DUN_H - 1) // 2]

		if self.floor_num == 0:
			center_room.type = STARTING_ROOM_TYPE
			center_room.init2()
		else:
			center_room.type = UP_STAIRS_TYPE
			center_room.init2(dest=upstairs)

	def __getitem__(self, key: int) -> list['Room']:
		"""Index the floor"""

		return self.dun[key]

	def __iter__(self) -> Iterator[list['Room']]:
		return iter(self.dun)


class Room(object):
	"""Class for individual cells with encounters in them."""

	def __init__(self, difficulty: int, location: dict[str, int]) -> None:
		self.type: int
		self.info: str
		self.en: Encounter
		self.location: dict[str, int] = location
		self.visited: bool = False

		weights: tuple[float, float, float] = (
			normpdf(difficulty, 600, 200),  # goblin
			normpdf(difficulty, 1050, 200),  # slime
			normpdf(difficulty, 1500, 200)  # drider
		)

		# Goblin, Slime, Drider
		enemy_types = [101, 102, 103]

		if ENEMIES:
			self.type = random.choices(enemy_types, weights=weights)[0]
		else:
			self.type = 100
		self.init2()

	# This function allows variable to be reset without doing them all
	# manually, used for stairs and some other stuff
	def init2(self, **kwargs) -> None:
		"""Set various variables that may need to be updated all together"""

		# enemy generation
		if self.type == 103:
			self.en = Drider()
		elif self.type == 102:
			self.en = Slime()
		elif self.type == 101:
			self.en = Goblin()
		elif self.type == 100:
			self.info = "This is an empty room"
			self.en = Empty()

		if self.type > 100:
			self.info = f"This is a room with a {self.en.name}"

		if self.type == STARTING_ROOM_TYPE:
			self.visited = True
			self.info = (
				"This is the starting room. There is nothing of "
				"significance here."
			)
			self.en = Empty()

		elif self.type == DOWN_STAIRS_TYPE:
			self.info = "Here are the stairs to the next floor"
			self.floor.stairs = True
			self.en = Stairs(self.location)
		elif self.type == UP_STAIRS_TYPE:
			self.info = "Here are the stairs to the previous floor"
			self.en = Stairs(
				self.location,
				dist=-1,
				to=kwargs["dest"]
			)

	@property
	def floor(self) -> Floor:
		"""Return the floor that this room is on"""
		return dungeon[self.location["floor"]]

	def enter(self) -> None:
		"""Set up to enter a room"""

		self.visited = True
		floor_finished: bool = dungeon.check_all_rooms()

		if floor_finished and not self.floor.stairs:
			# make this room stairs down to the next floor
			self.type = DOWN_STAIRS_TYPE
			self.init2()

		gui.write_out(self.info)
		if getattr(self.en, "alive", False):
			self.en.meet()
		# this isn't good practice
		elif not isinstance(self.en, Enemy):
			self.en.meet()


# used primarily for sorting items by amount
@total_ordering
class CollectableItem(object):
	"""Class for any item that can be gained by the player."""

	image: ClassVar[ImageTk.PhotoImage]

	def __init__(
			self,
			amount: int = 1,
			filename: str = "ImageNotFound.png") -> None:
		self.amount: int = amount
		self.plural: bool = False
		self.name: str = "undefined_collectable_item"

		# if a refereance is not kept to ImageTk.PhotoImage(image) it
		# is garbage collected and will not display
		if not hasattr(type(self), "image"):
			# item icon stuff
			image = Image.open(file_path(filename))
			image = image.resize((IBW - 5, IBH - 5))
			type(self).image = ImageTk.PhotoImage(image)

	def __str__(self) -> str:
		# return self.name
		return f"{self.amount} {self.name}"

	# math ops are here to allow manipulation of the
	# amounts without too much extra work
	def __add__(self, other: 'CollectableItem | int') -> 'CollectableItem':
		if isinstance(other, type(self)):
			return type(self)(self.amount + other.amount)
		elif isinstance(other, int):
			return type(self)(self.amount + other)
		else:
			raise TypeError

	def __iadd__(self, other: 'CollectableItem | int') -> 'CollectableItem':
		if isinstance(other, type(self)):
			self.amount += other.amount
		elif isinstance(other, int):
			self.amount += other
		else:
			raise TypeError
		return self

	def __sub__(self, other: 'CollectableItem | int') -> 'CollectableItem':
		if isinstance(other, type(self)):
			return type(self)(self.amount - other.amount)
		elif isinstance(other, int):
			return type(self)(self.amount - other)
		else:
			raise TypeError

	def __isub__(self, other: 'CollectableItem | int') -> 'CollectableItem':
		if isinstance(other, type(self)):
			self.amount -= other.amount
		elif isinstance(other, int):
			self.amount -= other
		else:
			raise TypeError
		return self

	def __lt__(self, other: int) -> bool:
		return self.amount < other

	def __bool__(self) -> bool:
		return bool(self.amount)

	def __neg__(self) -> 'CollectableItem':
		return type(self)(amount=-self.amount)


class Gold(CollectableItem):
	"""Collectable currency"""

	def __init__(self, amount: int = 0) -> None:
		super().__init__(amount, filename="gold.png")
		self.name: str = "gold"


class Player(object):
	"""Class for the player. Includes stats and actions."""

	def __init__(self, inven: Inventory, race: str = "human") -> None:
		"""Setting stats and variables"""

		self.race: str = race
		self.loc: list[int] = [(DUN_W - 1) // 2, (DUN_H - 1) // 2]
		self.floor: Floor = Floor(-1)
		self.max_health: int = DEFAULT_MAX_HEALTH
		self.health: int = self.max_health
		self.damage: int = DEFAULT_DAMAGE
		self.defence: int = DEFAULT_DEFENCE
		self.experiance: int = 0
		self.lvl: int = 1
		self.inven: Inventory = inven
		self.equipment: dict[str, list[Space, int, 'EquipableItem']] = {}
		self.status = None

	def occupied_equipment(self) -> list[str]:
		"""Figure out what equipment spaces are used"""

		vals: tuple[list[Space, int, 'EquipableItem']] = tuple(self.equipment.values())
		total: list[str] = []
		for i in vals:
			total += [i[0][0]] * i[1]
		return total


class Encounter(object):
	"""A base class for enemies and non combat things"""

	image: ClassVar[ImageTk.PhotoImage]
	icon: ClassVar[ImageTk.PhotoImage]

	def __init__(self, filename: str = "ImageNotFound.png") -> None:
		"""Create the image variable

		image is a class variable to reduce variable initialization
		(the repeated defining of self.image), copying of large
		variables, and keep related data together. It is being
		defined here so that PhotoImage does not get called before
		tk has been initialised.
		"""

		self.name: str = "Encounter"

		if not hasattr(type(self), "image"):
			image: ImageTk.PhotoImage = Image.open(file_path(filename))
			image = image.resize((180, 180))
			type(self).image = ImageTk.PhotoImage(image)

	@classmethod
	# Class method to give access to class variables for the class.
	# This method belongs to not just this base class
	def show_ico(cls, place: str = "center") -> None:
		"""Display the image of the enemy"""

		gui.show_image(cls.image, False, place)

	def meet(self, disp: str = "center") -> None:
		"""Start the encounter"""

		gui.screen = "encounter"
		self.show_ico(place=disp)

	def interact(self) -> None:
		pass


class Empty(Encounter):
	"""An empty room"""

	image = None

	def __init__(self) -> None:
		pass

	def meet(self, disp: str = "") -> None:
		"""Dont do anything because the room is empty"""

		pass


class Stairs(Encounter):
	"""Stairs to another Floor"""

	image: ClassVar[ImageTk.PhotoImage]
	icon: ClassVar[ImageTk.PhotoImage]

	def __init__(
			self,
			location: dict[str, int],
			dist: int = +1,
			to: dict[str, int] | None = None) -> None:

		if not hasattr(type(self), "image"):
			image = Image.open(file_path("dungeon_stairs.png"))
			image = image.resize((180, 240))
			type(self).image = ImageTk.PhotoImage(image)

			# icon of stairs
			icon = Image.open(file_path("stairs_icon.png"))
			icon = ImageOps.mirror(
				icon.resize((SMW // 2, SMH // 2))
			)
			type(self).icon = ImageTk.PhotoImage(icon)

		self.location: dict[str, int] = location
		self.dist: int = dist
		if to:
			self.to: dict[str, int] = to
			self.dist = self.to["floor"] - self.location["floor"]
		else:
			self.to = {
				"floor": self.location["floor"] + self.dist,
				"x": (DUN_W - 1) // 2,
				"y": (DUN_H - 1) // 2
			}

	def interact(self) -> None:
		"""Go up or down the stairs"""

		dungeon.gen_floor(self.location)

		dungeon.floor_num += self.dist
		p.floor = dungeon.current_floor
		p.loc[:] = (self.to["x"], self.to["y"])

		# gui.navigation_widgets[0] = dungeon.current_floor.disp
		gui.enc.remove()
		gui.nav.show()
		gui.screen = "navigation"

		dungeon.current_floor.disp.coords(
			"player",
			(
				SMW * p.loc[0],
				SMH * p.loc[1],
				SMW * p.loc[0] + SMW,
				SMH * p.loc[1] + SMH
			)
		)

	def meet(self, disp: str = "center") -> None:
		"""Dislpay the stairs image"""

		super().meet(disp)

		gui.nav.draw_encounter(self.icon, p.loc[0], p.loc[1])

		gui.screen = "stairs"
		gui.clear_screen()
		gui.enc.show()

		gui.enc.inter_btn.config(text="Decend" if self.dist > 0 else "Ascend")
		gui.enc.inter_btn.config(command=self.interact)


class Enemy(Encounter):
	"""General enemy class. Includes set up for fights, attacking, being
	attacked, and returning loot"""

	def __init__(self, filename: str = "ImageNotFound.png") -> None:

		super().__init__(filename)
		self.name: str = "enemy"
		self.alive: bool = True
		self.max_health: int = 1
		self.health: int = 1
		self.damage: int = 1
		# must be done again after stats are finalized
		self.loot: dict[str, CollectableItem] = {
			"undefined_collectable_item": CollectableItem()
		}

	def gold_gen(self) -> Gold:
		"""Determine how much gold the enemy will drop"""

		return Gold(amount=self.max_health // 3 + self.damage // 2 + 2)

	@classmethod
	# Class method to give access to class variables for the class.
	# This method belongs to not just this base class
	def show_ico(cls, place: str = "NW") -> None:
		"""Display the image of the enemy"""

		gui.show_image(cls.image, True, place)

	def meet(self, disp: str = "NW") -> None:
		"""Format screen for a fight"""

		# fight comes first because it clears the screen
		gui.bat.fight(self.health, self.max_health, p.health, p.max_health)

		super().meet(disp)

		gui.screen = "battle"
		gui.nav.remove()
		gui.bat.show()

	def attack(self) -> None:
		"""Attack the player"""

		# defence function ↓↓↓
		damage_delt = round(
			self.damage * (1 - 2 * atan(p.defence / 20) / pi)
		)
		p.health -= damage_delt
		if p.health <= 0:
			gui.lose()
		gui.update_healthbar(p.health, p.max_health)
		gui.write_out(f"The enemy did {damage_delt} damage!")

	def be_attacked(self) -> None:
		"""The player attacks. The enemy is damaged"""

		self.health -= p.damage
		if self.health <= 0:
			self.die()
			return

		gui.bat.update_en_healthbar(self.health, self.max_health)

		self.attack()

	def die(self) -> None:
		"""The enemy dies"""

		global monsters_killed

		self.alive = False
		monsters_killed += 1
		hold = "You got: \n"
		# display loot
		for key, val in self.loot.items():
			hold += f"{str(key).title()}: {val.amount}\n"
		gui.write_out(hold[:-1])

		gui.nav.remove_enemy_marker(p.loc[0], p.loc[1])
		cur_room().info = "This is an empty room."

		# take loot
		get_loot(self.loot)

		gui.bat.remove()
		gui.nav.show()
		gui.screen = "navigation"


class Goblin(Enemy):
	"""Common weak enemy"""

	def __init__(self) -> None:
		"""Set stats and loot"""

		super().__init__(filename="TypicalGoblin.png")
		self.name: str = "goblin"
		self.max_health = random.randint(30, 40) + monsters_killed // 2
		self.health = self.max_health
		self.damage = random.randint(3, 6) + monsters_killed // 5
		self.loot = {
			"gold": self.gold_gen()
		}

		if not random.randint(0, 2):
			self.loot["health potion"] = HealthPot()


class Slime(Enemy):
	"""Higher level enemy"""

	def __init__(self) -> None:
		"""Set stats and loot"""

		super().__init__(filename="SlimeMonster.png")
		self.name: str = "slime"
		self.max_health = random.randint(50, 70) + (3 * monsters_killed) // 2
		self.health = self.max_health
		self.damage = random.randint(10, 15) + monsters_killed // 4
		self.loot = {
			"gold": self.gold_gen()
		}
		if not random.randint(0, 15):
			self.loot["slime heart"] = SlimeHeart()


class Drider(Enemy):
	"""A enemy with medium health, but high attack and it can poison you"""

	def __init__(self) -> None:
		super().__init__(filename="Drider.png")

		self.name: str = "drider"
		self.max_health = random.randint(40, 60) + monsters_killed
		self.health = self.max_health
		self.damage = random.randint(20, 30) + monsters_killed // 2
		self.loot = {
			"gold": self.gold_gen() + 10
		}


class UsableItem(CollectableItem):
	"""An item that can be used and consumed on use"""

	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)

		self.name: str = "undefined_usable_item"

	def use(self) -> bool:
		"""Use the item for what ever purpose it has"""

		if p.inven[self.name].amount <= 0:
			return False
			# raise UseItemWithZeroError(f"You have 0 {self.name}s")

		# should later change how consumable things work
		# make not everything consumable? or add durability

		gui.write_out("Used " + self.name.title())
		return True


class EquipableItem(UsableItem):
	"""An item that can be equiped and unequiped"""

	def __init__(self, *args, **kwargs) -> None:
		# *args and **kwargs allow other agruments to be passed
		super().__init__(*args, **kwargs)
		self.name: str = "undefined_equipable_item"
		self.space: tuple = ("", -1)
		# would prefer for this to be a temp variable
		self.equiped: bool = False

	def use(self) -> bool:
		"""Using an equipable item equips it"""

		success = super().use()
		if success:
			success = self.equip()
		return success

	def equip(self) -> bool:
		"""Equip the item"""

		if (
			p.occupied_equipment().count(self.space[0])
			>= self.space[1]
		):

			gui.write_out(
				f"You can not equip more than {self.space[1]} of this"
			)
			return False
		else:
			self.equiped = True
			gui.write_out(f"You equip the {self.name}")

			if self.space[0] not in p.occupied_equipment():
				p.equipment[self.name] = [self.space, 1, self]
			else:
				p.equipment[self.name][1] += 1
			return True

	def unequip(self) -> None:
		"""Unequip the item"""

		if self.name in p.equipment:
			# would prefer for this to be a temporary variable
			self.unequiped = True
			p.inven[self.name] += 1
			p.equipment[self.name][1] -= 1
			if p.equipment[self.name][1] <= 0:
				p.equipment.pop(self.name)
			gui.write_out(f"You unequip the {self.name}")
		else:
			gui.write_out(f"{self.name} is not equiped")


class BuyableItem(CollectableItem):
	"""An item that is sold in the shop"""

	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.cost: int = 0
		self.name: str = "buyable_item"

	def __str__(self) -> str:
		return self.name

	def effect(self) -> None:
		"""The passive effect the item has just my having it"""

		pass


T_Tiered = TypeVar("T_Tiered", bound="TieredItem")
class TieredItem(BuyableItem):
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.name: str = "tiered_item"
		self.tier: int = 0

	# needed to create different tiers dynamically
	@classmethod
	def factory(cls: Type[T_Tiered], tier: int) -> Callable[[], T_Tiered]:
		"""Create function that returns class with the desired tier"""

		def proxy() -> T_Tiered:
			"""Return an instance with the correct tier"""

			return cls(tier)

		proxy.factory = cls.factory

		return proxy  # return func that returns the class

class HealthPot(UsableItem, BuyableItem):
	"""An item that heals the player"""

	def __init__(self, *args, **kwargs) -> None:
		super().__init__(filename="healthpotion.png", *args, **kwargs)
		self.cost: int = int(100 * COST_MUL)
		self.name: str = "health potion"

	def use(self) -> bool:
		"""Restore health"""

		success = super().use()
		p.health += HEAL_POT_VAL
		if p.health > p.max_health:
			p.health = p.max_health

		gui.update_healthbar(p.health, p.max_health)
		return success


class SlimeHeart(UsableItem):
	"""An item that increases the player's max HP"""

	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)

		self.name: str = "slime heart"

	def use(self) -> bool:
		"""Increase max health"""

		success = super().use()
		p.max_health += SLIME_HEART_VAL
		p.health += SLIME_HEART_VAL

		gui.update_healthbar(p.health, p.max_health)
		return success


class Sword(BuyableItem, EquipableItem):
	"""A basic weapon"""

	def __init__(self, *args, **kwargs) -> None:
		super().__init__(filename="sword.png", *args, **kwargs)
		self.name: str = "sword"
		self.cost = int(50 * COST_MUL)
		self.space = ("1 hand", 2)

	def equip(self) -> bool:
		"""Equip the sword"""

		success = super().equip()
		if self.equiped:
			p.damage += 5
			# reset this variable
			self.equiped = False
			gui.update_stats(p.damage, p.defence)
		return success

	def unequip(self) -> None:
		"""Remove the sword"""

		super().unequip()
		if self.unequiped:
			p.damage -= 5
			# reset this variable
			self.unequiped = False
			gui.update_stats(p.damage, p.defence)


class Armor(TieredItem, EquipableItem):
	"""Armor class that gives defence"""

	# what if kwargs contains "tier=1.2"? I don't know what to
	# do about that
	def __init__(self, tier: int, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.name: str = f"tier {tier} armor"
		self.tier: int = tier
		self.cost = int(COST_MUL * 100 * self.tier)
		self.space = ("body", 1)
		self.plural = True

	def equip(self) -> bool:
		"""Wear the armor"""

		success = super().equip()
		if self.equiped:
			p.defence += 5 + 5 * self.tier
			self.equiped = False  # reset this variable
			gui.update_stats(p.damage, p.defence)
		return success

	def unequip(self) -> None:
		"""Take off the armor"""

		super().unequip()
		if self.unequiped:
			p.defence -= 5 + 5 * self.tier
			self.unequiped = False  # reset this variable
			gui.update_stats(p.damage, p.defence)


equipment = {
	"sword": ("1 hand", 2),
	"armor": ("body", 1),
	"undefined_equipable_item": (None, float("inf")),
}

max_use_body_part = {
	"1 hand": 2,
	"body": 1,
}


def cur_room(xy: Sequence[int] | None = None) -> Room:
	"""Return the Room object that they player is currently in"""

	if xy is None:
		x = p.loc[0]
		y = p.loc[1]
	else:
		x, y = xy

	room = dungeon.current_floor[x][y]
	return room


'''
def restart() -> None:
	"""Reset all the values of the game and prepare to start over"""

	global dungeon, p, monsters_killed, gui, inventory

	del inventory
	del gui
	del p
	del dungeon

	monsters_killed = 0

	inventory = Inventory()

	p = Player(inventory)
	gui = GUI(inventory, p.damage, p.defence, p.max_health, p.loc, cur_room)

	buyable_items = (Sword, HealthPot, armor_factory(1))
	gui.misc_config(buyable_items, restart)

	get_loot({"gold": Gold(amount=STARTING_GOLD)})

	dungeon = Dungeon()
	gui.dungeon_config(dungeon)

	p.floor = dungeon.current_floor

	gui.master.mainloop()
'''


def get_loot(loot: dict[str, CollectableItem]) -> None:
	"""Add all loot items to inventroy"""

	for key, item in loot.items():
		gui.inv.add_to_inv(item)


def file_path(file: str) -> str:
	"""Find files in the Crawler home directory"""

	dirname = os.path.dirname(__file__)
	return os.path.join(dirname, file)


def normpdf(x: float, mean: float, sd: float) -> float:
	"""Calculate points on a normal curve"""

	var = float(sd) ** 2
	denom = (2 * pi * var) ** .5
	num = exp(-(float(x) - float(mean)) ** 2 / (2 * var))
	return num / denom


if __name__ == "__main__":
	print("\n" * 3)

	monsters_killed = 0

	inventory = Inventory()

	buyable: tuple[Callable[[], BuyableItem] | type[BuyableItem], ...] = (
		Sword, HealthPot, Armor.factory(1)
	)

	p = Player(inventory)
	gui = GUI(
		inventory,
		buyable,
		p.damage,
		p.defence,
		p.max_health,
		p.loc,
		cur_room
	)

	get_loot({"gold": Gold(amount=STARTING_GOLD)})

	# gui.player_config(p)

	dungeon = Dungeon()
	gui.dungeon_config(dungeon)

	p.floor = dungeon.current_floor

	gui.master.mainloop()


# END

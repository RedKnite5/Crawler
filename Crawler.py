#!/cygdrive/c/Users/RedKnite/Appdata/local/programs/Python/Python38/python.exe

"""The main Crawler game"""

import random as rand
import tkinter as tk
from re import match
from functools import total_ordering
from math import atan, pi, exp
import os

from PIL import Image     # type: ignore
from PIL import ImageOps  # type: ignore
from PIL import ImageTk   # type: ignore

from GUI import GUI
from inven import Inventory
from errors import *
from config import *

#   python Crawler.py

# ToDo: If you equip and unequip a sword, further attempts to unequip will
#       not produce any message.
# ToDo: Change how equiping stuff works so that it doesn't remove it from
#       the inventory, just puts a marker by it.
# ToDo: Get Gold icon to work

# fix all issues labeled: 'BUG:'


class Dungeon(object):
	def __init__(self) -> None:
		self.floors: list['Floor'] = [Floor(0)]
		self.floor_num: int = 0

	def __getattr__(self, attr: str):
		if attr == "current_floor":
			return self.floors[self.floor_num]

	def __getitem__(self, index: int) -> 'Floor':
		return self.floors[index]

	def gen_floor(self, up_stair_location: dict[str, int], level="+1") -> None:
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

	def __init__(self, floor: int, upstairs=None) -> None:
		"""Create a floor and populate it"""

		self.stairs = False

		self.floor_num: int = floor
		self.dun: list[list['Room']] = []
		for i in range(DUN_W):  # map generation
			column: list['Room'] = []
			for k in range(DUN_H):
				column.append(Room(int(
					(abs(i - (DUN_W - 1) // 2)
					 + abs(k - (DUN_H - 1) // 2)) * 1.5
					* DISTANCE_DIFF + 150 * self.floor_num),
					{"x": i, "y": k, "floor": self.floor_num}))
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


class Room(object):
	"""Class for individual cells with encounters in them."""

	def __init__(self, difficulty: int, location: dict[str, int]) -> None:
		"""Room creation"""

		self.type: int
		self.info: str
		self.en: Encounter
		self.location: dict[str, int] = location
		self.visited: bool = False
		
		weights: list[float] = []
		
		#goblin
		weights.append(normpdf(difficulty, 600, 200))
		
		#slime
		weights.append(normpdf(difficulty, 1050, 200))
		
		#drider
		weights.append(normpdf(difficulty, 1500, 200))
		
		# Goblin, Slime, Drider
		enemy_types = [101, 102, 103]
		
		if ENEMIES:
			self.type = rand.choices(enemy_types, weights=weights)[0]
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

		gui.out.config(text=self.info)
		if getattr(self.en, "alive", False):
			self.en.meet()
		# this isn't good practice
		elif not isinstance(self.en, Enemy):
			self.en.meet()


# used primarily for sorting items by amount
@total_ordering
class CollectableItem(object):
	"""Class for any item that can be gained by the player."""
	
	image: ImageTk.PhotoImage

	def __init__(self, amount: int = 1, filename: str = "ImageNotFound.png") -> None:
		self.amount: int = amount
		self.plurale: bool = False
		self.name: str = "undefined_collectable_item"
		
		# if a refereance is not kept to ImageTk.PhotoImage(image) it
		# is garbage collected and will not display
		if not hasattr(type(self), "image"):
			# item icon stuff
			image = Image.open(file_path(filename))
			image = image.resize((IBW - 5, IBH - 5))
			type(self).image = ImageTk.PhotoImage(image)

	def __str__(self) -> str:
		#return self.name
		return f"{self.amount} {self.name}"

	# math ops are here to allow manipulation of the
	# amounts without too much extra work
	def __add__(self, other) -> 'CollectableItem':
		if isinstance(other, type(self)):
			return type(self)(self.amount + other.amount)
		else:
			return type(self)(self.amount + other)

	def __iadd__(self, other) -> 'CollectableItem':
		if isinstance(other, type(self)):
			self.amount += other.amount
		else:
			self.amount += other
		return self

	def __sub__(self, other) -> 'CollectableItem':
		if isinstance(other, type(self)):
			return type(self)(self.amount - other.amount)
		else:
			return type(self)(self.amount - other)

	def __isub__(self, other) -> 'CollectableItem':
		if isinstance(other, type(self)):
			self.amount -= other.amount
		else:
			self.amount -= other
		return self

	def __lt__(self, other) -> bool:
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

	def __init__(self, inventory: Inventory, race: str = "human") -> None:
		"""Setting stats and variables"""

		self.race: str = race
		self.loc: list[int] = [(DUN_W - 1) // 2, (DUN_H - 1) // 2]
		self.floor = None
		self.max_health: int = DEFAULT_MAX_HEALTH
		self.health: int = self.max_health
		self.damage: int = DEFAULT_DAMAGE
		self.defence: int = DEFAULT_DEFENCE
		self.experiance: int = 0
		self.lvl: int = 1
		self.inven: Inventory = inventory
		self.equipment: dict = {}
		self.status = None

	'''
	def search_inventory(self, item, searching: str = "inventory"):
		"""Find the name of the item in the player's inventory or equipment"""

		if searching == "inventory":
			search = self.inven
		elif searching == "equipment":
			search = self.equipment
		else:
			raise ItemNotFoundError

		# if the item is just in the inventory
		if item in search.keys():
			return [item]

		items = []
		for i in search.keys():
			# check if the item is tiered
			if m := match(f"tier ([0-9]+) {item}", i):
				items.append(f"tier {m.group(1)} {item}")
		return items
	'''

	def occupied_equipment(self):
		"""Figure out what equipment spaces are used"""

		vals = tuple(self.equipment.values())
		total = []
		for i in vals:
			total += [i[0][0]] * i[1]
		return total


class Encounter(object):
	"""A base class for enemies and non combat things"""
	
	image: ImageTk.PhotoImage

	def __init__(self, filename: str = "ImageNotFound.png") -> None:
		"""Create the image variable
		
		image is a class variable to reduce variable initialization
		(the repeated defining of self.image), copying of large
		variables, reduce amount of global variables, and keep
		related data together. It is being defined here so that
		PhotoImage does not get called before tk has been initialised.
		"""
		
		self.name: str = "Encounter"
		
		if not hasattr(type(self), "image"):
			image = Image.open(file_path(filename))
			image = image.resize((180, 180))
			type(self).image = ImageTk.PhotoImage(image)

	@classmethod
	# Class method to give access to class variables for the class.
	# This method belongs to not just this base class
	def show_ico(cls, place: str = "NW") -> None:
		"""Display the image of the enemy"""

		if cls.image:
			# encounter icon
			if place == "NW":
				# encounter icon
				gui.cbt_scr.create_image(
					210,
					40,  # 40 is different from 130
					image=cls.image,
					anchor="nw"
				)
			elif place == "center":
				# encounter icon
				gui.cbt_scr.create_image(
					210,
					130,  # 130 is different from 40
					image=cls.image,
					anchor="center"
				)

	def meet(self, disp: str = "NW") -> None:
		"""Start the encounter"""

		gui.screen = "encounter"
		gui.cbt_scr.delete("all")
		self.show_ico(place=disp)

	@staticmethod
	def leave() -> None:
		gui.navigation_mode()

	@classmethod
	def reset(cls) -> None:
		if hasattr(cls, "image"):
			del cls.image


class Empty(Encounter):
	"""An empty room"""

	image = None

	# noinspection PyMissingConstructor
	def __init__(self) -> None:
		pass

	# noinspection PyMethodOverriding
	def meet(self, disp: str = "") -> None:
		super().meet()
		self.leave()


class Stairs(Encounter):
	"""Stairs to another Floor"""
	
	image: ImageTk.PhotoImage
	icon: ImageTk.PhotoImage

	def __init__(self, location: dict[str, int], dist: int = +1, to=None) -> None:

		if not hasattr(type(self), "image"):
			image = Image.open(file_path("dungeon_stairs.png"))
			image = image.resize((180, 240))
			type(self).image = ImageTk.PhotoImage(image)

			# icon of stairs
			icon: ImageTk.PhotoImage = Image.open(file_path("stairs_icon.png"))
			icon = ImageOps.mirror(
				icon.resize((SMW // 2, SMH // 2))
			)
			type(self).icon = ImageTk.PhotoImage(icon)

		self.location: dict[str, int] = location
		self.dist: int = dist
		if to:
			self.to = to
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

		#gui.navigation_widgets[0] = dungeon.current_floor.disp
		gui.navigation_mode()

		dungeon.current_floor.disp.coords("player",
			(SMW * p.loc[0],
			 SMH * p.loc[1],
			 SMW * p.loc[0] + SMW,
			 SMH * p.loc[1] + SMH)
		)

	def meet(self, disp: str = "center") -> None:
		"""Dislpay the stairs image"""

		super().meet(disp)
		
		gui.nav.draw_encounter(self.icon, p.loc[0], p.loc[1])

		gui.screen = "stairs"
		gui.clear_screen()
		gui.cbt_scr.grid(row=0, column=0, columnspan=4)

		gui.inter_btn.grid(row=1, column=1)
		gui.inter_btn.config(text="Decend" if self.dist > 0 else "Ascend")
		gui.inter_btn.config(command=self.interact)

		gui.leave_btn.grid(row=1, column=2)
		# Having a button labeled "Leave" also sounds like going down
		# the stairs
		gui.leave_btn.config(text="Leave")
		gui.leave_btn.config(command=self.leave)


class Enemy(Encounter):
	"""General enemy class. Includes set up for fights, attacking, being
	attacked, and returning loot"""

	def __init__(self, filename="ImageNotFound.png") -> None:

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

	def meet(self, disp: str = "NW") -> None:
		"""Format screen for a fight"""

		super().meet(disp)

		gui.screen = "fight"
		gui.nav.remove()
		gui.bat_frame.grid(row=0, column=0)

		self.fight()

	def fight(self) -> None:
		"""Set up fight screen"""

		# enemy health bar
		gui.cbt_scr.create_rectangle(W + 90, 10, W - 10, 30)

		# enemy health
		gui.cbt_scr.create_rectangle(
			W + 90,
			10,
			W + 90 - (100 * self.health / self.max_health),
			30,
			fill="red",
			tags="en_bar"
		)

		# player healthbar
		gui.cbt_scr.create_rectangle(
			10,
			H - 30,
			110,
			H - 10
		)
		gui.cbt_scr.create_rectangle(
			10,
			H - 30,
			10 + (100 * p.health / p.max_health), H - 10,
			fill="green",
			tags="fight_healthbar"
		)
		gui.cbt_scr.create_text(
			60,
			H - 20,
			text=f"{p.health}/{p.max_health}",
			tags="fight_healthbar_text"
		)

	def attack(self) -> None:
		"""Attack the player"""

		damage_delt = 0  # defence function ↓↓↓
		damage_delt = round(
			self.damage * (1 - 2 * atan(p.defence / 20) / pi)
		)
		p.health -= damage_delt
		if p.health <= 0:
			gui.lose()
		gui.update_healthbar(p.health, p.max_health)
		gui.out.config(text=f"The enemy did {str(damage_delt)} damage!")

	def be_attacked(self) -> None:
		"""The player attacks. The enemy is damaged"""

		self.health -= p.damage
		if self.health <= 0:
			self.die()
		gui.cbt_scr.coords(
			"en_bar",
			W + 90, 10, W + 90 - (100 * self.health / self.max_health), 30)
		if self.alive:
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
		gui.out.config(text=hold[:-1])

		gui.nav.remove_enemy_marker(p.loc[0], p.loc[1])
		cur_room().info = "This is an empty room."

		# take loot
		get_loot(self.loot)

		self.leave()


class Goblin(Enemy):
	"""Common weak enemy"""

	def __init__(self) -> None:
		"""Set stats and loot"""

		super().__init__(filename="TypicalGoblin.png")
		self.name: str = "goblin"
		self.max_health = rand.randint(30, 40) + monsters_killed // 2
		self.health = self.max_health
		self.damage = rand.randint(3, 6) + monsters_killed // 5
		self.loot = {
			"gold": self.gold_gen()
		}

		if not rand.randint(0, 2):
			self.loot["health potion"] = HealthPot()


class Slime(Enemy):
	"""Higher level enemy"""

	def __init__(self) -> None:
		"""Set stats and loot"""

		super().__init__(filename="SlimeMonster.png")
		self.name: str = "slime"
		self.max_health = rand.randint(50, 70) + (3 * monsters_killed) // 2
		self.health = self.max_health
		self.damage = rand.randint(10, 15) + monsters_killed // 4
		self.loot = {
			"gold": self.gold_gen()
		}
		if not rand.randint(0, 15):
			self.loot["slime heart"] = SlimeHeart()


class Drider(Enemy):
	"""A enemy with medium health, but high attack and it can poison you"""

	def __init__(self) -> None:
		super().__init__(filename="Drider.png")
		
		self.name: str = "drider"
		self.max_health = rand.randint(40, 60) + monsters_killed
		self.health = self.max_health
		self.damage = rand.randint(20, 30) + monsters_killed // 2
		self.loot = {
			"gold": self.gold_gen() + 10
		}


class UsableItem(CollectableItem):
	"""An item that can be used and consumed on use"""

	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		
		self.name: str = "undefined_usable_item"

	def use(self) -> None:
		"""Use the item for what ever purpose it has"""

		if p.inven[self.name].amount <= 0:
			raise UseItemWithZeroError(f"You have 0 {self.name}s")

		# should later change how consumable things work
		# make not everything consumable? or add durability
		#p.inven[self.name] -= 1

		gui.out.config(text="Used " + self.name.title())


class EquipableItem(UsableItem):
	"""An item that can be equiped and unequiped"""

	def __init__(self, *args, **kwargs) -> None:
		# *args and **kwargs allow other agruments to be passed
		super().__init__(*args, **kwargs)
		self.name: str = "undefined_equipable_item"
		self.space: tuple = (None, float("inf"))
		# would prefer for this to be a temp variable
		self.equiped: bool = False
	
	def use(self) -> None:
		super().use()
		self.equip()

	def equip(self) -> None:
		"""Equip the item"""

		if (
				p.occupied_equipment().count(self.space[0])
				>= self.space[1]
		):

			gui.out.config(
				text=f"You can not equip more than {self.space[1]} of this"
			)
			raise EquipmentFullError(f"You can not equip more than {self.space[1]} of this")
		else:
			self.equiped = True
			gui.out.config(text=f"You equip the {self.name}")
			# should rework how inventory interacts with equipment
			p.inven[self.name] -= 1

			if self.space[0] not in p.occupied_equipment():
				p.equipment[self.name] = [self.space, 1, self]
			else:
				p.equipment[self.name][1] += 1

	def unequip(self) -> None:
		"""Unequip the item"""

		if self.name in p.equipment:
			# would prefer for this to be a temporary variable
			self.unequiped = True
			p.inven[self.name] += 1
			p.equipment[self.name][1] -= 1
			if p.equipment[self.name][1] <= 0:
				p.equipment.pop(self.name)
			gui.out.config(text=f"You unequip the {self.name}")
		else:
			raise NotEquipedError(f"{self.name} is not equiped")


class BuyableItem(CollectableItem):
	"""An item that is sold in the shop"""

	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.cost: int = 0
		self.tiered: bool = False
		self.name: str = "undefined_buyable_item"

	def __str__(self) -> str:
		return self.name

	def effect(self):
		"""The passive effect the item has just my having it"""

		pass


class HealthPot(UsableItem, BuyableItem):
	"""An item that heals the player"""

	def __init__(self, *args, **kwargs) -> None:
		super().__init__(filename="healthpotion.png", *args, **kwargs)
		self.cost: int = int(100 * COST_MUL)
		self.name: str = "health potion"

	def use(self) -> None:
		"""Restore health"""

		super().use()
		p.health += HEAL_POT_VAL
		if p.health > p.max_health:
			p.health = p.max_health

		gui.update_healthbar(p.health, p.max_health)


class SlimeHeart(UsableItem):
	"""An item that increases the player's max HP"""

	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		
		self.name: str = "slime heart"

	def use(self) -> None:
		"""Increase max health"""

		super().use()
		p.max_health += SLIME_HEART_VAL
		p.health += SLIME_HEART_VAL

		gui.update_healthbar(p.health, p.max_health)


# sword in shop
class Sword(BuyableItem, EquipableItem):
	"""A basic weapon"""

	def __init__(self, *args, **kwargs) -> None:
		super().__init__(filename="sword.png", *args, **kwargs)
		self.name: str = "sword"
		self.cost = int(50 * COST_MUL)
		self.space = ("1 hand", 2)

	def equip(self) -> None:
		"""Equip the sword"""

		super().equip()
		if self.equiped:
			p.damage += 5
			# reset this variable
			self.equiped = False
			gui.update_stats(p.damage, p.defence)

	def unequip(self) -> None:
		"""Remove the sword"""

		super().unequip()
		if self.unequiped:
			p.damage -= 5
			# reset this variable
			self.unequiped = False
			gui.update_stats(p.damage, p.defence)


# needed to create different tiers of armor dynamically
def armor_factory(tier: int) -> type[CollectableItem]:
	"""Create armor class with the desired tier"""

	class Armor(BuyableItem, EquipableItem):
		"""Armor class that gives defence"""
		
		# here so that a higher tier class can be generated from this one
		factory = staticmethod(armor_factory)

		# what if kwargs contains "tier=1.2"? I don't know what to
		# do about that
		def __init__(self, *args, **kwargs) -> None:
			super().__init__(*args, **kwargs)
			self.name: str = f"tier {tier} armor"
			self.tier: int = tier
			self.cost = int(COST_MUL * 100 * self.tier)
			self.space = ("body", 1)
			self.plurale = True

		def equip(self) -> None:
			"""Wear the armor"""

			super().equip()
			if self.equiped:
				p.defence += 5 + 5 * self.tier
				self.equiped = False  # reset this variable
				gui.update_stats(p.damage, p.defence)

		def unequip(self) -> None:
			"""Take off the armor"""

			super().unequip()
			if self.unequiped:
				p.defence -= 5 + 5 * self.tier
				self.unequiped = False  # reset this variable
				gui.update_stats(p.damage, p.defence)


	return Armor  # return the class from the factory


equipment = {
	"sword": ("1 hand", 2),
	"armor": ("body", 1),
	"undefined_equipable_item": (None, float("inf")),
}

max_use_body_part = {
	"1 hand": 2,
	"body": 1,
}


def cur_room(xy=None) -> Room:
	"""Return the Room object that they player is currently in"""
	
	if xy is None:
		x = p.loc[0]
		y = p.loc[1]
	else:
		x, y = xy

	room = dungeon.current_floor[x][y]
	return room


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


def get_loot(loot: dict) -> None:
	for key, item in loot.items():
		#if key in p.inven:
		#	p.inven[key] += item
		#else:
		#	p.inven[key] = item
		gui.add_to_inv(item)


def file_path(file: str) -> str:
	dirname = os.path.dirname(__file__)
	return os.path.join(dirname, file)

def normpdf(x: float, mean: float, sd: float) -> float:
    var = float(sd)**2
    denom = (2*pi*var)**.5
    num = exp(-(float(x)-float(mean))**2/(2*var))
    return num/denom


if __name__ == "__main__":
	print("\n" * 3)
	
	monsters_killed = 0
	
	inventory = Inventory()

	p = Player(inventory)
	gui = GUI(inventory, p.damage, p.defence, p.max_health, p.loc, cur_room)

	buyable_items = (Sword, HealthPot, armor_factory(1))
	gui.misc_config(buyable_items, restart)

	get_loot({"gold": Gold(amount=STARTING_GOLD)})

	#gui.player_config(p)

	dungeon = Dungeon()
	gui.dungeon_config(dungeon)

	p.floor = dungeon.current_floor

	gui.master.mainloop()










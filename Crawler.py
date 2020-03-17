#!/cygdrive/c/Users/RedKnite/Appdata/local/programs/Python/Python38/python.exe

import random as rand
import tkinter as tk
from re import match
from functools import total_ordering
from math import atan, pi
from math import fabs as abs

from PIL import Image
from PIL import ImageOps
from PIL import ImageTk

from GUI import GUI
from config import *

#   python Crawler.py

# ToDo:
	# 1) If you equip and unequip a sword, further attempts to unequip will
	#    not produce any message.
	# 2) Rewrite the enter method of GUI
	# 3) Change how equiping stuff works so that it doesn't remove it from
	#    the inventory, just puts a marker by it.


monsters_killed = 0


class ItemNotFoundError(ValueError):
	pass


class NotEquipedError(RuntimeError):
	pass


class Dungeon(object):
	def __init__(self):
		self.floors = [Floor(0)]
		self.floor_num = 0

	def __getattr__(self, attr):
		if attr == "current_floor":
			return self.floors[self.floor_num]

	def __getitem__(self, index):
		return self.floors[index]

	def gen_floor(self, up_stair_location, level="+1"):
		if level[0] == "+" and level[1:].isdigit():
			new_floor_num = self.floor_num + int(level[1:])
		else:
			new_floor_num = int(level)

		self.floors.append(Floor(new_floor_num, up_stair_location))

	def check_all_rooms(self):
		"""Check if all rooms have been visited"""

		for row in self.current_floor:
			for room in row:
				if not room.visited:
					return False
		return True


class Floor(object):
	"""Whole floor of the dungeon"""

	def __init__(self, floor, upstairs=None):
		"""Create a floor and populate it"""

		self.stairs = False

		self.floor_num = floor
		self.dun = []
		for i in range(DUN_W): # map generation
			column = []
			for k in range(DUN_H):
				column.append(Room(int(
					(abs(i - int((DUN_W - 1) / 2))
					+ abs(k - int((DUN_H - 1) / 2))) * 1.5
					* DISTANCE_DIFF + 150 * self.floor_num),
					{"x": i, "y": k, "floor": self.floor_num}))
			self.dun.append(column)

		center_room = self.dun[int((DUN_W - 1) / 2)][int((DUN_H - 1) / 2)]

		if self.floor_num == 0:
			center_room.type = STARTING_ROOM_TYPE
			center_room.init2()
		else:
			center_room.type = UP_STAIRS_TYPE
			center_room.init2(dest=upstairs)

		self.disp = tk.Canvas(gui.master, width=W, height=H)
		self.create_display()


	def __getitem__(self, key):
		"""Index the floor"""

		return self.dun[key]

	def create_display(self):
		"""Create the map for the player to see"""

		# display creation
		for i in range(DUN_W):
			for k in range(DUN_H):
				# if there is a space in the tags tkinter will split it up
				# do not add one
				self.disp.create_rectangle(
					SMW * i,
					SMH * k,
					SMW * i + SMW,
					SMH * k + SMH,
					fill="grey",
					tags=f"{str(i)},{str(k)}"
				)

		# player icon creation
		self.disp.create_oval(
			SMW * p.loc[0],
			SMH * p.loc[1],
			SMW * p.loc[0] + SMW,
			SMH * p.loc[1] + SMH,
			fill = "green",
			tags = "player"
		)


class Room(object):
	"""Class for individual cells with encounters in them."""

	def __init__(self, difficulty, location):
		"""Room creation"""

		self.location = location
		self.visited = False
		if ENEMIES:
			self.type = int(rand.gauss(difficulty + 400, 140))
			if self.type < 1:
				self.type = 1
		else:
			self.type = NON_VIOLENT_ENC_CUTOFF
		self.init2()

	# This function allows variable to be reset without doing them all
	# manually
	def init2(self, **kwargs):
		"""Set various variables that may need to be updated all together"""

		# enemy generation
		if DRIDER_CUTOFF <= self.type:
			self.en = Drider()
		elif SLIME_CUTOFF <= self.type:
			self.en = Slime()
		elif GOB_CUTOFF <= self.type:
			self.en = Goblin()
		else:
			self.info = "This is an empty room"
			self.en = Empty()

		if self.type > NON_VIOLENT_ENC_CUTOFF:
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
	def floor(self):
		"""Return the floor that this room is on"""
		return dungeon[self.location["floor"]]

	def enter(self):
		"""Set up to enter a room"""

		self.visited = True
		floor_finished = dungeon.check_all_rooms()

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

	def __init__(self, amount=1, *args):
		self.amount = amount
		self.name = "undefined_collectable_item"
		self.plurale = False

	def __str__(self):
		return self.name

	 # math ops are here to allow manipulation of the
	 # amounts without too much extra work
	def __add__(self, other):
		if isinstance(other, type(self)):
			return type(self)(self.amount + other.amount)
		else:
			return type(self)(self.amount + other)

	def __iadd__(self, other):
		if isinstance(other, type(self)):
			self.amount += other.amount
		else:
			self.amount += other
		return self

	def __sub__(self, other):
		if isinstance(other, type(self)):
			return type(self)(self.amount - other.amount)
		else:
			return type(self)(self.amount - other)

	def __isub__(self, other):
		if isinstance(other, type(self)):
			self.amount -= other.amount
		else:
			self.amount -= other
		return self

	def __lt__(self, other):
		return self.amount < other

	def __bool__(self):
		return bool(self.amount)

	def __neg__(self):
		return type(self)(amount=-self.amount)


class Gold(CollectableItem):
	"""Collectable currency"""

	def __init__(self, *args, amount=0,  **kwargs):
		super().__init__(amount, *args, **kwargs)
		self.name = "gold"


class Player(object):
	"""Class for the player. Includes stats and actions."""

	def __init__(self, race="human"):
		"""Setting stats and variables"""

		self.race = race
		self.loc = [int((DUN_W - 1) / 2), int((DUN_H - 1) / 2)]
		self.floor = None
		self.max_health = DEFAULT_MAX_HEALTH
		self.health = self.max_health
		self.damage = DEFAULT_DAMAGE
		self.defence = DEFAULT_DEFENCE
		self.experiance = 0
		self.lvl = 1
		self.inven = {"gold": Gold(amount=STARTING_GOLD)}
		self.equipment = {}
		self.status = None

	def move(self, dir):
		"""Player movement on map function"""

		# this is mostly redundent except for the starting room
		dungeon.current_floor[self.loc[0]][self.loc[1]].visited = True
		# if there is a space in the tags tkinter will split it up
		# do not add one
		dungeon.current_floor.disp.itemconfig(
			f"{str(self.loc[0])},{str(self.loc[1])}",
			fill="yellow")

		if dir == "north" and self.loc[1] > 0:   # up
			self.loc[1] -= 1
			dungeon.current_floor.disp.move("player", 0, -1 * SMH)
		elif dir == "south" and self.loc[1] < DUN_H-1:  # down
			self.loc[1] += 1
			dungeon.current_floor.disp.move("player", 0, SMH)
		elif dir == "west" and self.loc[0] > 0:  # left
			self.loc[0] -= 1
			dungeon.current_floor.disp.move("player", -1 * SMW, 0)
		elif dir == "east" and self.loc[0] < DUN_W-1:  # right
			self.loc[0] += 1
			dungeon.current_floor.disp.move("player", SMW, 0)

		dungeon.current_floor[self.loc[0]][self.loc[1]].enter()

		dungeon.current_floor[self.loc[0]][self.loc[1]].visited = True
		# if there is a space in the tags tkinter will split it up
		dungeon.current_floor.disp.itemconfig(
			f"{str(self.loc[0])},{str(self.loc[1])}",
			fill="yellow")

	def disp_in(self):
		"""Display the player's inventory"""

		hold = ""
		for key, val in self.inven.items():
			hold += f"\n{str(key).title()}: {str(val.amount)}"
		gui.out.config(text=hold[1:])

	def search_inventory(self, item, searching="inventory"):
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
			m = match(f"tier ([0-9]+) {item}", i)
			if m:
				items.append(f"tier {m.group(1)} {item}")
		return items

	def occupied_equipment(self):
		"""Figure out what equipment spaces are used"""

		vals = tuple(self.equipment.values())
		total = []
		for i in vals:
			total += [i[0][0]] * i[1]
		return total


class Encounter(object):
	"""A base class for enemies and non combat things"""

	def __init__(self, filename="ImageNotFound.png"):
		"""Create the image variable
		
		image is a class variable to reduce variable initialization
		(the repeated defining of self.image), copying of large
		variables, reduce amount of global variables, and keep
		related data together. It is being defined here so that
		PhotoImage does not get called before tk has been inititialized.
		"""
		
		if not hasattr(type(self), "image"):
			image = Image.open(filename)
			image = image.resize((180, 180))
			type(self).image = ImageTk.PhotoImage(image)

	@classmethod
	# Class method to give access to class variables for the class.
	# This method belongs to not just this base class
	def show_ico(cls, place="NW"):
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


	def meet(self, disp="NW"):
		"""Start the encounter"""

		if isinstance(self, Stairs):
			dungeon.current_floor.disp.create_image(
				int(SMW * (p.loc[0] + .5)),
				int(SMH * (p.loc[1] + .5)),
				image=cur_room().en.icon,
				anchor="center"
			)

		gui.screen = "encounter"
		gui.cbt_scr.delete("all")
		self.show_ico(place=disp)

	def leave(self):
		gui.navigation_mode()

	@classmethod
	def reset(cls):
		if hasattr(cls, "image"):
			del cls.image


class Empty(Encounter):
	"""An empty room"""

	image = None

	def __init__(self):
		pass

	def meet(self):
		super().meet()
		self.leave()


class Stairs(Encounter):
	"""Stairs to another Floor"""

	def __init__(self, location, dist=+1, to=None):

		if not hasattr(type(self), "image"):
			image = Image.open("dungeon_stairs.png")
			image = image.resize((180, 240))
			type(self).image = ImageTk.PhotoImage(image)

			# icon of stairs
			icon = Image.open("stairs_icon.png")
			icon = ImageOps.mirror(
				icon.resize((int(SMW / 2), int(SMH / 2)))
			)
			type(self).icon = ImageTk.PhotoImage(icon)

		self.location = location
		self.dist = dist
		if to:
			self.to = to
			self.dist = self.to["floor"] - self.location["floor"]
		else:
			self.to = {
				"floor": self.location["floor"] + self.dist,
				"x": int((DUN_W - 1) / 2),
				"y": int((DUN_H - 1) / 2)
			}

	def interact(self):
		"""Go up or down the stairs"""

		dungeon.gen_floor(self.location)

		dungeon.floor_num += self.dist
		p.floor = dungeon.current_floor
		p.loc = [self.to["x"], self.to["y"]]

		gui.navigation_widgets[0] = dungeon.current_floor.disp
		gui.navigation_mode()

		dungeon.current_floor.disp.coords("player",
			(SMW * p.loc[0],
			SMH * p.loc[1],
			SMW * p.loc[0] + SMW,
			SMH * p.loc[1] +SMH)
		)


	def meet(self, disp="center"):
		"""Dislpay the stairs image"""
		
		super().meet(disp)

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

	def __init__(self, filename="ImageNotFound.png"):

		super().__init__(filename)

		self.alive = True
		self.max_health = 1
		self.health = 1
		self.damage = 1
		self.name = "enemy"
		# must be done again after stats are finalized
		self.loot = {
			"undefined_collectable_item": CollectableItem()
		}


	def gold_gen(self):
		"""Determine how much gold the enemy will drop"""
		
		return Gold(amount=self.max_health // 3 + self.damage // 2 + 2)


	def meet(self):
		"""Format screen for a fight"""

		super().meet()

		gui.screen = "fight"
		gui.clear_screen()
		gui.cbt_scr.grid(row=0, column=0, columnspan=3)
		gui.att_b.grid(row=1, column=0)
		gui.b[4].grid(row=1, column=1)
		gui.stats.grid(row=1, column=3)
		gui.run_b.grid(row=1, column=2)
		gui.out.grid(row=2, column=0, columnspan=3)
		gui.entry.grid(row=3, column=0, columnspan=3)

		self.fight()

	def fight(self):
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

	def attack(self):
		"""Attack the player"""

		damage_delt = 0     # defence function ↓↓↓
		damage_delt = round(
			self.damage * (1 - 2 * atan(p.defence / 20) / pi)
		)
		p.health -= damage_delt
		if p.health <= 0:
			gui.lose()
		gui.update_healthbar()
		gui.out.config(text=f"The enemy did {str(damage_delt)} damage!")

	def be_attacked(self):
		"""The player attacks. The enemy is damaged"""

		self.health -= p.damage
		if self.health <= 0:
			self.die()
		gui.cbt_scr.coords(
			"en_bar",
			W + 90, 10, W + 90 - (100 * self.health / self.max_health), 30)
		if self.alive:
			self.attack()

	def die(self):
		"""The enemy dies"""

		global monsters_killed

		self.alive = False
		monsters_killed += 1
		hold = "You got: \n"
		# display loot
		for key, val in self.loot.items():
			hold += f"{str(key).title()}: {str(val.amount)}\n"
		gui.out.config(text=hold[:-1])

		# remove enemy icon on map
		# if there is a space in the tags tkinter will split it up
		dungeon.current_floor.disp.delete(
			f"enemy{str(p.loc[0])},{str(p.loc[1])}"
		)
		cur_room().info = "This is an empty room."

		# take loot
		for i in self.loot:
			if i in p.inven:
				p.inven[i] += self.loot[i]
			else:
				p.inven[i] = self.loot[i]

		self.leave()


class Goblin(Enemy):
	"""Common weak enemy"""

	def __init__(self, *args, **kwargs):
		"""Set stats and loot"""

		if not hasattr(type(self), "image"):
			# enemy icon stuff
			image = Image.open("TypicalGoblin.png")
			image = ImageOps.mirror(image.resize((180, 180)))
			type(self).image = ImageTk.PhotoImage(image)

		super().__init__(*args, **kwargs)
		self.max_health = rand.randint(30, 40) + monsters_killed // 2
		self.health = self.max_health
		self.damage = rand.randint(3, 6) + monsters_killed // 5
		self.name = "goblin"
		self.loot = {
			"gold": self.gold_gen()
		}

		if not rand.randint(0, 2):
			self.loot["health potion"] = HealthPot()


class Slime(Enemy):
	"""Higher level enemy"""

	def __init__(self, *args, **kwargs):
		"""Set stats and loot"""

		super().__init__(*args, filename="SlimeMonster.png", **kwargs)
		self.max_health = rand.randint(50, 70) + (3 * monsters_killed) // 2
		self.health = self.max_health
		self.damage = rand.randint(10, 15) + monsters_killed // 4
		self.name = "slime monster"
		self.loot = {
			"gold": self.gold_gen()
		}
		if not rand.randint(0, 15):
			self.loot["slime heart"] = SlimeHeart()


class Drider(Enemy):
	"""A enemy with medium health, but high attack and it can poison you"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, filename="Drider.png", **kwargs)

		self.max_health = rand.randint(40, 60) + monsters_killed
		self.health = self.max_health
		self.damage = rand.randint(20, 30) + monsters_killed // 2
		self.name = "drider"
		self.loot = {
			"gold": self.gold_gen() + 10
		}


class UsableItem(CollectableItem):
	"""An item that can be used and consumed on use"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.name = "undefined_usable_item"

	def use(self):
		"""Use the item for what ever purpose it has"""

		gui.out.config(text="Used " + self.name.title())

		# should later change how consumable things work
		# make not everything consumable? or add durability
		p.inven[self.name] -= 1


class EquipableItem(CollectableItem):
	"""An item that can be equiped and unequiped"""

	def __init__(self, *args, **kwargs):
		# *args and **kwargs allow other agruments to be passed
		super().__init__(*args, **kwargs)
		self.name = "undefined_equipable_item"
		self.space = (None, float("inf"))
		# would prefer for this to be a temp variable
		self.equiped = False

	def equip(self):
		"""Equip the item"""

		if (
			p.occupied_equipment().count(self.space[0])
			>= self.space[1]
		):
			gui.out.config(
				text=f"You can not equip more than {self.space[1]} of this"
			)
		else:
			self.equiped = True
			gui.out.config(text=f"You equip the {self.name}")
			# should rework how inventory interacts with equipment
			p.inven[self.name] -= 1

			if self.space[0] not in p.occupied_equipment():
				p.equipment[self.name] = [self.space, 1, self]
			else:
				p.equipment[self.name][1] += 1

	def unequip(self):
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

	tiered = False

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.cost = 0
		self.name = "undefined_buyable_item"

	def __str__(self):
		return self.name

	def effect(self):
		"""The passive effect the item has just my having it"""

		pass


class HealthPot(UsableItem, BuyableItem):
	"""An item that heals the player"""

	name = "health potion"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.cost = int(100 * COST_MUL)
		self.name = "health potion"

	def use(self):
		"""Restore health"""

		super().use()
		p.health += HEAL_POT_VAL
		if p.health > p.max_health:
			p.health = p.max_health

		gui.update_healthbar()


class SlimeHeart(UsableItem):
	"""An item that increases the player's max HP"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.name = "slime heart"

	def use(self):
		"""Increase max health"""

		super().use()
		p.max_health += SLIME_HEART_VAL
		p.health += SLIME_HEART_VAL

		gui.update_healthbar()

# sword in shop
class Sword(BuyableItem, EquipableItem):
	"""A basic weapon"""

	name = "sword"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.name = "sword"
		self.cost = int(50 * COST_MUL)
		self.space = ("1 hand", 2)

	def equip(self):
		"""Equip the sword"""

		super().equip()
		if self.equiped:
			p.damage += 5
			# reset this variable
			self.equiped = False
			gui.update_stats()

	def unequip(self):
		"""Remove the sword"""

		super().unequip()
		if self.unequiped:
			p.damage -= 5
			# reset this variable
			self.unequiped = False
			gui.update_stats()


# needed to create different tiers of armor dynamically
def armor_factory(tier):
	"""Create armor class with the desired tier"""

	class Armor(BuyableItem, EquipableItem):
		"""Armor class that gives defence"""

		name = f"tier {tier} armor"
		# here so that a higher tier class can be generated from this one
		factory = staticmethod(armor_factory)

		# what if kwargs contains "tier=1.2"? I don't know what to
		# do about that
		def __init__(self, *args, **kwargs):
			super().__init__(*args, **kwargs)
			self.tier = tier
			self.name = f"tier {tier} armor"
			self.cost = int(COST_MUL * 100 * self.tier)
			self.space = ("body", 1)
			self.plurale = True

		def equip(self):
			"""Wear the armor"""

			super().equip()
			if self.equiped:
				p.defence += 5 + 5 * self.tier
				self.equiped = False  # reset this variable
				gui.update_stats()

		def unequip(self):
			"""Take off the armor"""

			super().unequip()
			if self.unequiped:
				p.defence -= 5 + 5 * self.tier
				self.unequiped = False  # reset this variable
				gui.update_stats()

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


def cur_room():
	"""Return the Room object that they player is currently in"""

	room = dungeon.current_floor[p.loc[0]][p.loc[1]]
	return(room)


def restart():
	"""Reset all the values of the game and prepare to start over"""

	global dungeon, p, monsters_killed, gui

	gui.master.destroy()
	del gui

	# reset images for TKimage to work
	Goblin.reset()
	Slime.reset()

	gui = GUI()
	buyable_items = (Sword, HealthPot, armor_factory(1))
	gui.misc_config(buyable_items, restart)

	del p
	p = Player()
	gui.player_config(p)

	del dungeon
	dungeon = Dungeon()
	gui.dungeon_config(dungeon)

	dungeon.current_floor.disp.focus()

	monsters_killed = 0

	gui.master.mainloop()


if __name__ == "__main__":
	print("\n" * 3)

	gui = GUI()
	
	buyable_items = (Sword, HealthPot, armor_factory(1))
	gui.misc_config(buyable_items, restart)

	p = Player()  # player creation

	gui.player_config(p)

	dungeon = Dungeon()
	gui.dungeon_config(dungeon)
	
	dungeon.current_floor

	p.floor = dungeon.current_floor
	
	gui.master.mainloop()
	



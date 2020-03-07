#!/cygdrive/c/Users/RedKnite/Appdata/local/programs/Python/Python38/python.exe

import random as rand
import re
import tkinter as tk
from functools import total_ordering
from math import atan, pi
from math import fabs as abs
from tkinter import font

from PIL import Image
from PIL import ImageOps
from PIL import ImageTk

#   python Crawler.py

# ToDo:
	# 1) If you equip and unequip a sword, further attempts to unequip will
	#    not produce any message.
	# 2) Figure out why "Mys line 1" is there. "Mys line 1" is a label in a
	#    nearby comment
	# 3) Change how equiping stuff works so that it doesn't remove it from
	#    the inventory, just puts a marker by it.
	# 4) Make the next floor do something.
	# 5)

# should these be placed in a config file?
DUN_W = 4   # number of rooms wide         # constant intialization
DUN_H = 4
W = 300        # width of map screen in pixels
H = 300
SMW = W / DUN_W  # width of a room in pixels
SMH = H / DUN_H
COST_MUL = 1
STARTING_GOLD = 300
DISTANCE_DIFF = 70
DEFAULT_MAX_HEALTH = 100
DEFAULT_DAMAGE = 10
HEAL_POT_VAL = 50    # the amount of a health potion heals
SLIME_HEART_VAL = 5  # the amount of health a slime heart gives
SLIME_CUTOFF = 1700
GOB_CUTOFF = 1100
ENEMY_CUTOFF = 100
NON_VIOLENT_ENC_CUTOFF = 1
STARTING_ROOM_TYPE = 0
DOWN_STAIRS_TYPE = -1
UP_STAIRS_TYPE = -2

ENEMIES = True

screen = "navigation"
monsters_killed = 0


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
				column.append(Room(
					(abs(i - int((DUN_W - 1) / 2))
					+ abs(k - int((DUN_H - 1) / 2)))
					* DISTANCE_DIFF,
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
		create_display(self.disp)


	def __getitem__(self, key):
		"""Index the floor"""

		return self.dun[key]


class Room(object):
	"""Class for individual cells with encounters in them."""

	def __init__(self, difficulty, location):
		"""Room creation"""

		self.location = location
		self.visited = False
		if ENEMIES:
			self.type = rand.randint(
				NON_VIOLENT_ENC_CUTOFF,
				1000) + difficulty
		else:
			self.type = NON_VIOLENT_ENC_CUTOFF
		self.init2()

	# This function allows variable to be reset without doing them all
	# manually
	def init2(self, **kwargs):
		"""Set various variables that may need to be updated all together"""

		if SLIME_CUTOFF >= self.type > GOB_CUTOFF:  # enemy generation
			self.en = Slime()
		elif GOB_CUTOFF >= self.type > ENEMY_CUTOFF:
			self.en = Goblin()
		elif ENEMY_CUTOFF >= self.type >= NON_VIOLENT_ENC_CUTOFF:
			self.info = "This is an empty room"
			self.en = Empty()
		else:
			# these should be overwritten
			self.info = "UNDEFINED"
			self.en = Empty()

		if self.type > ENEMY_CUTOFF:
			self.info = f"This is a room with a {self.en.name}"

		if self.type == STARTING_ROOM_TYPE:
			self.visited = True
			self.info = ("This is the starting room. There is nothing of "
			"significance here.")
			self.en = Empty()

		elif self.type == DOWN_STAIRS_TYPE:
			self.info = "Here are the stairs to the next floor"
			self.floor.stairs = True
			self.en = Stairs(self.location)
		elif self.type == UP_STAIRS_TYPE:
			self.info = "Here are the stairs to the previous floor"
			self.en = Stairs(self.location, dist=-1, to=kwargs["dest"])


	def __getattr__(self, atter):
		if atter == "floor":
			return dungeon[self.location["floor"]]

	def enter(self):
		"""Set up to enter a room"""

		self.visited = True
		floor_finished = check_all_rooms()

		if floor_finished and not self.floor.stairs:
			# make this room stairs down to the next floor
			self.type = DOWN_STAIRS_TYPE
			self.init2()

		gui.out.config(text=self.info)
		if getattr(self.en, "alive", False):
			self.en.meet()
		elif not isinstance(self.en, Enemy): # this isn't good practice
			self.en.meet()


@total_ordering  # used primarily for sorting items by amount
class CollectableItem(object):
	"""Class for any item that can be gained by the player."""

	def __init__(self, amount=1):
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
		dungeon.current_floor[self.loc[0]][self.loc[1]].visited = True
		dungeon.current_floor.disp.itemconfig(
			str(self.loc[0]) + "," + str(self.loc[1]),
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
		dungeon.current_floor.disp.itemconfig(
			str(self.loc[0]) + "," + str(self.loc[1]),
			fill="yellow")

	def disp_in(self):
		"""Display the player's inventory"""

		hold = ""
		for key, val in self.inven.items():
			hold += "\n" + str(key).title() + ": " + str(val.amount)
		gui.out.config(text=hold[1:])


class Encounter(object):
	
	def __init__(self, filename="ImageNotFound_png.png"):
		
		
			# image is a class variable to reduce variable initialization
			# (the repeated defining of self.image), copying of large variables,
			# reduce amount of global variables, and keep related data together.
			# It is being defined here so that PhotoImage does not get called
			# before tk has been inititialized.
		if not hasattr(type(self), "image"):
			image = Image.open(filename)
			image = image.resize((180, 180))
			type(self).image = ImageTk.PhotoImage(image)

	@classmethod  # Class method to give access to class variables for the
	# class. This method belongs to not just this base class
	def show_ico(cls, place="NW"):
		"""Display the image of the enemy"""

		if cls.image:
			if place == "NW":
				gui.cbt_scr.create_image(   # encounter icon
					210, 40, image=cls.image, anchor="nw")
			elif place == "center":
				gui.cbt_scr.create_image(   # encounter icon
					210, 130, image=cls.image, anchor="center")

	def meet(self, disp="NW"):
		"""Start the encounter"""

		global screen
		
		if isinstance(self, Stairs):
			dungeon.current_floor.disp.create_image(
				int(SMW * (p.loc[0] + .5)), int(SMH * (p.loc[1] + .5)),
				image=cur_room().en.icon, anchor="center")

		screen = "encounter"
		gui.cbt_scr.delete("all")
		self.show_ico(place=disp)

	def leave(self):
		gui.navigation_mode()


class Empty(Encounter):
	image = None
	
	def __init__(self):
		pass

	def meet(self):
		super().meet()
		self.leave()


class Stairs(Encounter):

	def __init__(self, location, dist=+1, to=None):
	
		if not hasattr(type(self), "image"):
			image = Image.open("dungeon_stairs.png")
			image = image.resize((180, 240))
			type(self).image = ImageTk.PhotoImage(image)

			icon = Image.open("stairs_icon.png")  # icon of stairs
			icon = ImageOps.mirror(icon.resize((int(SMW / 2), int(SMH / 2))))
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
			SMH * p.loc[1] +SMH))


	def meet(self, disp="center"):
		super().meet(disp)
		
		global screen
		screen = "stairs"

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

	def __init__(self, filename="ImageNotFound_png.png"): #   create enemy
	
		super().__init__(filename)
		
		self.alive = True
		self.max_health = 1
		self.health = 1
		self.damage = 1
		self.name = "enemy"
		self.loot = {   # must be done again after stats are finalized
			"undefined_collectable_item": CollectableItem()
		}


	def meet(self):
		super().meet()

		global screen
		screen = "fight"
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

		gui.cbt_scr.create_rectangle(W + 90, 10, W - 10, 30) # enemy health bar

		gui.cbt_scr.create_rectangle(   # enemy health
			W + 90, 10, W + 90 - (100 * self.health / self.max_health), 30,
			fill="red", tags="en_bar")

		gui.cbt_scr.create_rectangle(
			10, H - 30, 110, H - 10) # player healthbar
		gui.cbt_scr.create_rectangle(
			10, H - 30, 10 + (100 * p.health / p.max_health), H - 10,
			fill="green", tags="fight_healthbar")
		gui.cbt_scr.create_text(
			60, H - 20,
			text=f"{p.health}/{p.max_health}",
			tags="fight_healthbar_text")

	def attack(self):
		"""Attack the player"""

		damage_delt = 0     # defence function ↓↓↓
		damage_delt = round(self.damage * (1 - 2 * atan(p.defence / 20) / pi))
		p.health -= damage_delt
		if p.health <= 0:
			lose()
		gui.update_healthbar()
		gui.out.config(text="The enemy did " + str(damage_delt) + " damage!")

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
		for key, val in self.loot.items():  # display loot
			hold += str(key).title() + ": " + str(val.amount) + "\n"
		gui.out.config(text=hold[:-1])

		# remove enemy icon on map
		dungeon.current_floor.disp.delete(
			"enemy" + str(p.loc[0]) + "," + str(p.loc[1]))
		cur_room().info = "This is an empty room."

		for i in self.loot:  # take loot
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
			image = Image.open("TypicalGoblin_png.png")  # enemy icon stuff
			image = ImageOps.mirror(image.resize((180, 180)))
			type(self).image = ImageTk.PhotoImage(image)

		super().__init__(*args, **kwargs)
		self.max_health = rand.randint(30, 40) + monsters_killed
		self.health = self.max_health
		self.damage = rand.randint(3, 6) + monsters_killed // 3
		self.name = "goblin"
		self.loot = {
			"gold": Gold(amount=self.max_health // 3 + self.damage // 2 + 2)
		}
		if not rand.randint(0, 2):
			self.loot["health potion"] = HealthPot()


class Slime(Enemy):
	"""Higher level enemy"""

	def __init__(self, *args, **kwargs):
		"""Set stats and loot"""

		super().__init__(*args, filename="SlimeMonster_png.png", **kwargs)
		self.max_health = rand.randint(50, 70) + (3 * monsters_killed) // 2
		self.health = self.max_health
		self.damage = rand.randint(10, 20) + monsters_killed // 2
		self.name = "slime monster"
		self.loot = {
			"gold": Gold(amount=self.max_health // 3 + self.damage // 2 + 2)
		}
		if not rand.randint(0, 15):
			self.loot["slime heart"] = SlimeHeart()


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
		self.equiped = False  # would prefer for this to be a temp variable

	def equip(self):
		"""Equip the item"""

		if (occupied_equipment(p.equipment).count(self.space[0]) >=
			self.space[1]):
			gui.out.config(
				text=f"You can not equip more than {self.space[1]} of this")
		else:
			self.equiped = True
			gui.out.config(text="You equip the " + self.name)
			# should rework how inventory interacts with equipment
			p.inven[self.name] -= 1

			if self.space[0] not in occupied_equipment(p.equipment):
				p.equipment[self.name] = [self.space, 1, self]
			else:
				p.equipment[self.name][1] += 1

	def unequip(self):
		"""Unequip the item"""

		if self.name in p.equipment:
			self.unequiped = True  # would prefer for this to be a
			                       # temporary variable
			p.inven[self.name] += 1
			p.equipment[self.name][1] -= 1
			if p.equipment[self.name][1] <= 0:
				p.equipment.pop(self.name)
			gui.out.config(text="You unequip the " + self.name)


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


class HealthPot(UsableItem):
	"""An item that heals the player"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
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


class Sword(BuyableItem, EquipableItem):  # sword in shop
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
			self.equiped = False  # reset this variable
			gui.update_stats()

	def unequip(self):
		"""Remove the sword"""

		super().unequip()
		if self.unequiped:
			p.damage -= 5
			self.unequiped = False  # reset this variable
			gui.update_stats()


class GUI(object):
	def __init__(self):
		self.master = tk.Tk()
		
		self.master.title(string="The Dungeon")  # window name
		self.empty_menu = tk.Menu(self.master)
		
		# movement + inventory button creation
		self.b = [tk.Button(self.master) for i in range(5)]

		# movement button configuation
		self.b[0].configure(text="North", command=movement_factory("north"))
		self.b[3].configure(text="South", command=movement_factory("south"))
		self.b[1].configure(text="West", command=movement_factory("west"))
		self.b[2].configure(text="East", command=movement_factory("east"))

		self.b[0].grid(row=2, column=1) # button placement
		self.b[1].grid(row=3, column=0)
		self.b[2].grid(row=3, column=2)
		self.b[3].grid(row=4, column=1)
		self.b[4].grid(row=1, column=0)

		# health bar creation
		self.healthbar = tk.Canvas(self.master, width=100 + 10, height=30)
		self.healthbar.grid(row=0, column=0, columnspan=3)

		self.healthbar.create_rectangle(10, 10, 10 + 100, 30)  # health bar drawing

		self.stats = tk.Message(self.master, text="")
		self.stats.grid(row=1, column=1, columnspan=2)

		# output text creation
		self.out = tk.Message(
			self.master,
			text="Welcome to The Dungeon. Come once, stay forever!",
			width=W + 100)
		self.out.grid(row=5, column=0, columnspan=4)

		self.entry = tk.Entry(self.master)
		self.entry.grid(row=6, column=1, columnspan=2)

		self.shop = tk.Menu(self.master) # top level shop menu
		self.stock = tk.Menu(self.shop, tearoff=0) # drop down menu
		for i in buyable_items:
			self.stock.add_command(   # actual things you can buy
				label=i.title() + ": " + str(buyable_items[i]().cost),
				command=buy_item_fact(i))

		self.shop.add_cascade(menu=self.stock, label="Shop")
		self.master.config(menu=self.shop) # add menu to screen

		self.restart_button = tk.Button(
			self.master,
			text="Restart",
			command=restart,
			width=10
		)

		self.game_over = tk.Canvas(self.master, width=W + 100, height=H)
		self.game_over.create_rectangle(0, 0, W + 100, H + 50, fill="black")
		self.game_over.create_text(
			W/2 + 50,
			H/2,
			text="GAME OVER",
			fill="green",
			font=font.Font(size=40)
		)
		self.game_over.create_window(W, H * 3/4, window=self.restart_button)
		self.restart_button.lift()

		#  fight screen
		self.cbt_scr = tk.Canvas(self.master, width=W + 100, height=H)

		self.att_b = tk.Button(self.master, text="Attack", command=attack)
		self.run_b = tk.Button(self.master, text="Flee", command=flee)

		self.inter_btn = tk.Button(
			self.master,
			text="",
			command=lambda event: cur_room().en.interact()
		)
		self.leave_btn = tk.Button(
			self.master, text="", command=self.leave
		)

		# collections of widgets
		self.fight_widgets = [self.cbt_scr, self.att_b, self.run_b]
		
		self.other_widgets = [
			self.b[4],
			self.entry,
			self.stats,
			self.restart_button,
			self.game_over
		]
		self.non_hostile_widgets = [self.inter_btn, self.leave_btn]


		self.master.bind("<Up>", movement_factory("north"))  # key bindings
		self.master.bind("<Down>", movement_factory("south"))
		self.master.bind("<Right>", movement_factory("east"))
		self.master.bind("<Left>", movement_factory("west"))

		self.master.bind("<Return>", self.enter_key)
		self.master.bind("<Button 1>", mouse_click)

	
	def player_config(self, p):
		
		self.p = p
		
		# inventory button configuration
		self.b[4].configure(text="Inventory", command=self.p.disp_in)
		
		self.healthbar.create_rectangle(
			10,
			10,
			10 + (100 * p.health / p.max_health),
			30,
			fill="green",
			tags="navigation_healthbar"
		)
		self.healthbar.create_text(
			60, 20,
			text=f"{p.health}/{p.max_health}",
			tags="navigation_healthbar_text"
		)
		
		self.update_stats()
	
	def dungeon_config(self, dungeon):
		self.dungeon = dungeon
		
		self.dungeon.current_floor.disp.grid(row=0, column=3, rowspan=5)

		create_display(self.dungeon.current_floor.disp)
		
		self.dungeon.current_floor.disp.bind("<Button 1>", room_info)
	
	def __getattr__(self, attr):
	
		# Need to make disp in this list always be the disp of the current floor
		# to do this disp must be in a known position, namely first
		if attr == "navigation_widgets":
			return ([
				self.dungeon.current_floor.disp,
				self.healthbar,
				self.out]
				+ self.b[:-1]
			)
	
	def update_stats(self):
		"""Update the stats for the player"""

		self.stats.config(
			text=f"Damage: {self.p.damage}\nDefence: {self.p.defence}"
		)


	def enter_key(self, event):
		"""This function triggers when you press the enter key in the
		entry box. It is to use or equip something in your inventory"""

		data = input_analysis(self.entry.get())
		item = data["subject"] # name of item
		# name of item in the player's inventory
		inv_names = search_inventory(item)

		# if you dont have any of the possible items and are trying to use or
		# equip an item
		if (not any(self.p.inven.get(name, 0) for name in inv_names) and
			data["command"] in ("equip", "use")):
			self.out.config(text="You do not have any of that")
			return

		elif not any(self.p.inven.get(name, 0) for name in inv_names):

			if len(inv_names) == 1:
				inv_name = inv_names[0]

			elif not len(inv_names): # len(inv_names) == 0
				self.out.config(text="That item is not equiped")
				return

			else: # Mys line 1
				self.out.config(text="More than one item fits that description")
				return
		elif len(inv_names) > 0:

			# If more than one value with at least one in the inventory, return
			if sum(1 for name in inv_names if self.p.inven.get(name, 0)) > 1:
				self.out.config(text="More than one item fits that description")
				return
			else:

				# set inv_name to the one that is in inventory.
				inv_name = sorted(inv_names, key=lambda n: -self.p.inven.get(n, 0))[0]

		else: # empty list default
			inv_name = item

		done = True  # development variable. Will be removed
		if data["command"] == "unequip":

			# look for the item in equipment if you are trying to unequip
			# something
			inv_names = search_inventory(item, "equipment")
			try:
				self.p.inven[inv_name].unequip()
			except:
				self.out.config(text=f"{inv_name.title()} is not equiped")

		elif data["command"] == "equip":

			# if you can equip the item
			try:
				if self.p.inven[inv_name].amount > 0:

					# if you are already wearing equipment in that slot
					if (occupied_equipment(p.equipment).count(
						self.p.inven[inv_name].space[0])
						>= self.p.inven[inv_name].space[1]):

						# if you are only wearing 1 thing in that slot
						if self.p.inven[inv_name].space[1] == 1:

							for key, val in self.p.equipment.items():

								if val[0] == self.p.inven[inv_name].space :
									val[2].unequip()
									self.p.inven[inv_name].equip()
									return

					self.p.inven[inv_name].equip()
					if screen == "fight":  # equiping items takes a turn
						cur_room().en.attack()
				else:
					self.out.config(text="You do not have any of that")
			except Exception as e:
				self.out.config(text="That item is not equipable")

		elif data["command"] == "use":
			try:   # if you can use the item
				if self.p.inven[inv_name].amount > 0:
					self.p.inven[inv_name].use()
					if screen == "fight":
						# using items during a fight uses a turn
						cur_room().en.attack()
				else:
					self.out.config(text="You do not have any of that")
			except:
				self.out.config(text="That item is not usable")

		else:
			done = False

		if done:
			return

		print("should finish")

		if inv_name in self.p.inven:
			if self.p.inven[inv_name].amount > 0:
				try:   # if you can use the item
					self.p.inven[inv_name].use()
					if screen == "fight":
						cur_room().en.attack()
				except:
					try:  # if you can equip the item
						self.p.inven[inv_name].equip()
						if screen == "fight":  # using items takes a turn
							cur_room().en.attack()
					except:
						self.out.config(text="That item is not usable")
			else:
				self.out.config(text="You do not have any of that")
		else:
			self.out.config(text="You do not have any of that")

	def update_healthbar(self):
		"""Update the appearance of the healthbar in both the fighting screen
		and the navigation screen"""

		self.cbt_scr.coords(
			"fight_healthbar",
			10, H - 30, 10 + (100 * self.p.health / self.p.max_health), H - 10)
		self.cbt_scr.itemconfig(
			"fight_healthbar_text",
			text=f"{self.p.health}/{self.p.max_health}")

		self.healthbar.coords(
			"navigation_healthbar",
			10, 10, 10 + (100 * self.p.health / self.p.max_health), 30)
		self.healthbar.itemconfig(
			"navigation_healthbar_text",
			text=f"{self.p.health}/{self.p.max_health}")			
		

	def navigation_mode(self):
		"""Switch to navigation screen"""

		global screen
		
		self.cbt_scr.delete("all")
		for i in self.fight_widgets + self.non_hostile_widgets:
			i.grid_remove()
		for i in self.navigation_widgets:
			i.grid()
		self.navigation_widgets[0].grid(row=0, column=3, rowspan=5)
		self.out.grid(row=5, column=0, columnspan=4)
		self.b[4].grid(row=1, column=0)
		self.entry.grid(row=6, column=1, columnspan=2)
		self.stats.grid(row=1, column=1, columnspan=2)
		self.master.config(menu=self.shop)
		screen = "navigation"
		self.healthbar.coords("navigation_healthbar",
			10, 10, 10 + (100 * self.p.health / self.p.max_health), 30)
			
	def leave(self):
		if screen == "fight":
			flee()
		else:
			self.navigation_mode()
			self.dungeon.current_floor.disp.create_image(
				int(SMW * (p.loc[0] + .5)), int(SMH * (p.loc[1] + .5)),
				image=cur_room().en.icon, anchor="center")

	def clear_screen(self):
		"""Remove all widgets"""

		for i in self.navigation_widgets + self.fight_widgets + self.other_widgets:
			i.grid_remove()
		self.master.config(menu=self.empty_menu)

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


def movement_factory(direction): # necessary for tkinter key binding reasons
	"""Factory for moveing the character functions"""

	def move_func(event=None):
		"""Move in a direction"""
		
		if screen == "stairs":
			gui.navigation_mode()
		
		if screen != "fight" and gui.master.focus_get() is not gui.entry:
			p.move(direction)

	return move_func


def mouse_click(event):
	"""The mouse is clicked in the master window. Used to unfocus from the
	entry widget"""

	event.widget.focus()


def input_analysis(s):
	"""Analyze the input the the text box to find out what the command is"""

	command = general_subject = tier = None
	item = s.lower().strip()

	commands = ("unequip", "equip", "use")

	for c in commands:
		if item.startswith(c):
			command = c
			subject = item[len(c):].strip()
			break
	else:
		subject = item

	m = re.match("tier ([0-9]+) ([a-z_][a-z0-9_]*)", item)
	if m:
		tier = m.group(1)
		general_subject = m.group(2)


	data = {
		"command": command,
		"subject": subject,
		"general_subject": general_subject,
		"tier": tier,
	}
	return data


def search_inventory(item, searching="inventory"):
	"""Find the name of the item in the player's inventory or equipment"""

	if searching == "inventory":
		search = p.inven
	elif searching == "equipment":
		search = p.equipment
	else:
		raise ValueError

	if item in search.keys(): # if the item is just in the inventory
		return [item]

	items = []
	for i in search.keys():
		# check if the item is tiered
		m = re.match(f"tier ([0-9]+) {item}", i)
		if m:
			items.append(f"tier {m.group(1)} {item}")
	return items


def occupied_equipment(ment):
	"""Figure out what equipment spaces are used"""

	vals = tuple(ment.values())
	total = []
	for i in vals:
		total += [i[0][0]] * i[1]
	return total


# must be a factory because tkinter does not support passing arguments
# to the functions it calls
def buy_item_fact(item_name, amount=1, *args):
	"""Factory for buying things in the shop"""

	def buy_specific_item():
		"""Function to buy an item from the shop. Can not take parameters
		because tkinter does not support that"""

		for i in range(amount):
			item = buyable_items[item_name](*args)

			if p.inven["gold"].amount >= item.cost:
				if item_name in p.inven:
					p.inven[item_name].amount += 1
				else:
					p.inven[item_name] = item
				item.effect()    #  passive effect from having it
				if item.plurale:
					gui.out.config(text="You bought " + item_name)
				else:
					gui.out.config(text="You bought a " + item_name)
				p.inven["gold"] -= item.cost
				if hasattr(item, "tier"):
					# replace item in list of buyable items
					del buyable_items[item_name]
					new_item_cls = item.factory(item.tier + 1)
					buyable_items[new_item_cls.name] = new_item_cls

					gui.stock.delete(  # replace item in the menu
						item_name.title() + ": " + str(item.cost))
					gui.stock.add_command(
						label=(new_item_cls.name.title() + ": "
						+ str(new_item_cls().cost)),
						command=buy_item_fact(new_item_cls.name))
			else:
				gui.out.config(text="You do not have enough Gold for that")
	return buy_specific_item


_bitems = [Sword, armor_factory(1)]
buyable_items = {item.name: item for item in _bitems}


equipment = {
	"sword": ("1 hand", 2),
	"armor": ("body", 1),
	"undefined_equipable_item": (None, float("inf")),
}

max_use_body_part = {
	"1 hand": 2,
	"body": 1,
}

def check_all_rooms():
	"""Check if all rooms have been visited"""
	
	for row in dungeon.current_floor:
		for room in row:
			if not room.visited:
				return False
	return True


def cur_room():
	"""Return the Room object that they player is currently in"""

	room = dungeon.current_floor[p.loc[0]][p.loc[1]]
	return(room)


def attack():
	"""Attack the enemy"""

	cur_room().en.be_attacked()


def flee():
	"""Leave a fight without winning or losing"""

	chance = rand.randint(0, 100)
	if chance > 50:
		gui.navigation_mode()
		# create an icon for an enemy the player knows about
		dungeon.current_floor.disp.create_oval(
			SMW * p.loc[0] + SMW / 4, SMH * p.loc[1] + SMH / 4,
			SMW * p.loc[0] + SMW * 3/4, SMH * p.loc[1] + SMH * 3/4,
			fill="red", tags="enemy" + str(p.loc[0]) + "," + str(p.loc[1]))
		gui.out.config(text="You got away.")
	else:
		cur_room().en.attack()
		gui.out.config(text="You couldn't get away.")



def room_info(event):
	"""Give information about rooms by clicking on them"""

	x, y = event.x, event.y
	subjects = dungeon.current_floor.disp.find_overlapping(
		x - 1,
		y - 1,
		x + 1,
		y + 1)
	sub = []
	for i in subjects:
		if dungeon.current_floor.disp.type(i) == "rectangle":
			sub.append(i)
	if len(sub) == 1:
		tag = dungeon.current_floor.disp.gettags(sub[0])[0].split(",")
		clicked_room = dungeon.current_floor[int(tag[0])][int(tag[1])]

		if int(tag[0]) == p.loc[0] and int(tag[1]) == p.loc[1]:
			out.config(text="This is your current location.")
		elif clicked_room.visited:
			out.config(text=clicked_room.info)
		else:
			out.config(text="Unknown")


def lose():
	"""Change screen to the game over screen"""

	screen = "game over"
	clear_screen()
	game_over.grid(row=0, column=0)


def restart():
	"""Reset all the values of the game and prepare to start over"""

	global dungeon, p, monsters_killed

	del dungeon
	dungeon = Dungeon()

	del p
	p = Player()

	monsters_killed = 0

	update_healthbar()
	update_stats()
	game_over.grid_remove()
	screen = "navigation"
	navigation_mode()
	dungeon.current_floor.disp.delete("all")
	create_display(dungeon.current_floor.disp)
	out.config(text="Welcome to The Dungeon!")


def create_display(disp):
	"""Create the map for the player to see"""

	for i in range(DUN_W):  # display creation
		for k in range(DUN_H):
			disp.create_rectangle(
				SMW * i, SMH * k, SMW * i + SMW, SMH * k + SMH,
				fill="grey", tags=str(i) + "," + str(k))

	disp.create_oval(
		SMW * p.loc[0], SMH * p.loc[1], # player icon creation
		SMW * p.loc[0] + SMW, SMH * p.loc[1] +SMH,
		fill = "green", tags = "player")



if __name__ == "__main__":
	print("\n" * 3)
	
	gui = GUI()

	p = Player()  # player creation

	gui.player_config(p)

	dungeon = Dungeon()
	gui.dungeon_config(dungeon)
	
	dungeon.current_floor

	p.floor = dungeon.current_floor
	
	gui.master.mainloop()
	



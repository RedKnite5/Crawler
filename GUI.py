

# GUI.py

__all__ = ["GUI"]

import tkinter as tk
from tkinter import font
from re import match
from random import randint

from errors import *
from config import *


class GUI(object):
	"""The user interface for the game"""

	def __init__(self):

		self.screen = "navigation"

		self.master = tk.Tk()

		# window name
		self.master.title(string="The Dungeon")
		self.empty_menu = tk.Menu(self.master)

		# movement & inventory button creation
		self.b = [tk.Button(self.master) for i in range(5)]

		# movement button configuation
		self.b[0].configure(
			text="North",
			command=self.movement_factory("north")
		)
		self.b[3].configure(
			text="South",
			command=self.movement_factory("south")
		)
		self.b[1].configure(
			text="West",
			command=self.movement_factory("west")
		)
		self.b[2].configure(
			text="East",
			command=self.movement_factory("east")
		)

		# button placement
		self.b[0].grid(row=2, column=1)
		self.b[1].grid(row=3, column=0)
		self.b[2].grid(row=3, column=2)
		self.b[3].grid(row=4, column=1)
		self.b[4].grid(row=1, column=0)

		# health bar creation
		self.healthbar = tk.Canvas(self.master, width=100 + 10, height=30)
		self.healthbar.grid(row=0, column=0, columnspan=3)

		# health bar drawing
		self.healthbar.create_rectangle(10, 10, 10 + 100, 30)

		self.stats = tk.Message(self.master, text="")
		self.stats.grid(row=1, column=1, columnspan=2)

		# output text creation
		self.out = tk.Message(
			self.master,
			text="Welcome to The Dungeon. Come once, stay forever!",
			width=W + 100
		)
		self.out.grid(row=5, column=0, columnspan=4)

		self.entry = tk.Entry(self.master)
		self.entry.grid(row=6, column=1, columnspan=2)

		# top level shop menu
		self.shop = tk.Menu(self.master)
		# drop down menu
		self.stock = tk.Menu(self.shop, tearoff=0)

		self.shop.add_cascade(menu=self.stock, label="Shop")
		# add menu to screen
		self.master.config(menu=self.shop)

		self.game_over = tk.Canvas(self.master, width=W + 100, height=H)
		self.game_over.create_rectangle(0, 0, W + 100, H + 50, fill="black")
		self.game_over.create_text(
			W/2 + 50,
			H/2,
			text="GAME OVER",
			fill="green",
			font=font.Font(size=40)
		)

		#  fight screen
		self.cbt_scr = tk.Canvas(self.master, width=W + 100, height=H)

		self.leave_btn = tk.Button(
			self.master, text="", command=self.leave
		)

		# key bindings
		self.master.bind("<Up>", self.movement_factory("north"))
		self.master.bind("<Down>", self.movement_factory("south"))
		self.master.bind("<Right>", self.movement_factory("east"))
		self.master.bind("<Left>", self.movement_factory("west"))

		self.master.bind("<Return>", self.enter_key)
		self.master.bind("<Button 1>", self.mouse_click)

	def player_config(self, p):
		"""Configure the settings that require the player exist"""

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
		"""Configure settings that require that the dungeon object exist"""

		self.dungeon = dungeon
		self.dungeon.current_floor.disp.grid(row=0, column=3, rowspan=5)
		self.dungeon.current_floor.create_display()
		self.dungeon.current_floor.disp.bind("<Button 1>", self.room_info)

		self.att_b = tk.Button(
			self.master,
			text="Attack",
			command=lambda: self.cur_room().en.be_attacked())
		self.run_b = tk.Button(self.master, text="Flee", command=self.flee)

		self.inter_btn = tk.Button(
			self.master,
			text="",
			command=lambda event: self.cur_room().en.interact()
		)
		
		# collections of widgets
		self.fight_widgets = [self.cbt_scr, self.att_b, self.run_b]
		self.non_hostile_widgets = [self.inter_btn, self.leave_btn]
	
	def misc_config(self, items, restart):
		"""Configure settings that require buyable_items or the restart
		function
		"""
		self.buyable_items = {item.name: item for item in items}
		
		for i in self.buyable_items:
			# actual things you can buy
			self.stock.add_command(
				label=f"{i.title()}: {str(self.buyable_items[i]().cost)}",
				command=self.buy_item_fact(i)
			)

		# collections of widgets
		self.restart_button = tk.Button(
			self.master,
			text="Restart",
			command=restart,
			width=10
		)
		
		self.game_over.create_window(W, H * 3/4, window=self.restart_button)
		self.restart_button.lift()
		
		self.other_widgets = [
			self.b[4],
			self.entry,
			self.stats,
			self.restart_button,
			self.game_over
		]

	@property
	def navigation_widgets(self):

		# Need to make disp in this list always be the disp of the current
		# floor
		return ([
			self.dungeon.current_floor.disp,
			self.healthbar,
			self.out
			]
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

		data = self.input_analysis(self.entry.get())
		# name of item
		item = data["subject"]
		# name of item in the player's inventory
		inv_names = self.p.search_inventory(item)


		if data["command"] is None:
			# Trying to equip or use
			if any(self.p.inven.get(name, 0) for name in inv_names):
				if hasattr(item, "use"):
					data["command"] = "use"
				elif hasattr(item, "equip"):
					data["command"] = "equip"
			elif any(self.p.search_inventory(item, "equipment")):
				if (self.p.occupied_equipment().count(item.space[0])
					>= item.space[1]):
					data["command"] = "unequip"

		if data["command"] == "use":
			try:   # if you can use the item
				self.p.inven[inv_name].use()
				if self.screen == "fight":
					# using items during a fight uses a turn
					self.cur_room().en.attack()
			except AttributeError:
				self.out.config(text="That item is not usable")
			except UseItemWithZeroError as e:
				self.out.config(text=e.args[0])

			return

		if data["command"] == "equip":
			# if you can equip the item
			try:
				self.p.inven[inv_name].equip()
			except AttributeError:
				self.out.config(text="That item is not equipable")
			
			return



		# if you dont have any of the possible items and are trying to use or
		# equip an item
		if (
			not any(self.p.inven.get(name, 0) for name in inv_names)
			and data["command"] in ("equip", "use")
		):
			self.out.config(text="You do not have any of that")
			return
		# you are either unequiping the item or have not specified a command
		if not any(self.p.inven.get(name, 0) for name in inv_names):

			if len(inv_names) == 1:
				inv_name = inv_names[0]
			# the item was not found in your inventory
			elif not inv_names:
				self.out.config(
					text="That item is not in your inventory and "
					"is not equiped"
				)
				return
			else:
				self.out.config(
					text="More than one item fits that description"
				)
				return
		elif len(inv_names) > 0:

			# If more than one value with at least one in the
			# inventory, return
			if sum(1 for name in inv_names if self.p.inven.get(name, 0)) > 1:
				self.out.config(
					text="More than one item fits that description"
				)
				return
			else:

				# set inv_name to the one that is in inventory.
				inv_name = sorted(
					inv_names, key=lambda n: -self.p.inven.get(n, 0)
				)[0]

		else:  # empty list default
			inv_name = item

		# development variable. Will be removed... at some point
		done = True
		if data["command"] == "unequip":

			# look for the item in equipment if you are trying to unequip
			# something
			inv_names = self.p.search_inventory(item, "equipment")
			try:
				self.p.inven[inv_name].unequip()
			except NotEquipedError:
				self.out.config(text=f"{inv_name.title()} is not equiped")

		elif data["command"] == "equip":

			# if you can equip the item
			try:
				if self.p.inven[inv_name].amount > 0:

					# if you are already wearing equipment in that slot
					if (self.p.occupied_equipment().count(
						self.p.inven[inv_name].space[0])
						>= self.p.inven[inv_name].space[1]):

						# if you are only wearing 1 thing in that slot
						if self.p.inven[inv_name].space[1] == 1:

							for key, val in self.p.equipment.items():

								if val[0] == self.p.inven[inv_name].space:
									val[2].unequip()
									self.p.inven[inv_name].equip()
									return

					self.p.inven[inv_name].equip()
					# equiping items takes a turn
					if self.screen == "fight":
						self.cur_room().en.attack()
				else:
					self.out.config(text="You do not have any of that")
			except AttributeError:
				self.out.config(text="That item is not equipable")

		elif data["command"] == "use":
			try:   # if you can use the item
				if self.p.inven[inv_name].amount > 0:
					self.p.inven[inv_name].use()
					if self.screen == "fight":
						# using items during a fight uses a turn
						self.cur_room().en.attack()
				else:
					self.out.config(text="You do not have any of that")
			except AttributeError:
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
					if self.screen == "fight":
						self.cur_room().en.attack()
				except AttributeError:
					try:  # if you can equip the item
						self.p.inven[inv_name].equip()
						if self.screen == "fight":  # using items takes a turn
							self.cur_room().en.attack()
					except AttributeError:
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
			10,
			H - 30,
			10 + (100 * self.p.health / self.p.max_health),
			H - 10
		)
		self.cbt_scr.itemconfig(
			"fight_healthbar_text",
			text=f"{self.p.health}/{self.p.max_health}"
		)

		self.healthbar.coords(
			"navigation_healthbar",
			10,
			10,
			10 + (100 * self.p.health / self.p.max_health),
			30
		)
		self.healthbar.itemconfig(
			"navigation_healthbar_text",
			text=f"{self.p.health}/{self.p.max_health}"
		)

	def navigation_mode(self):
		"""Switch to navigation screen"""

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
		self.screen = "navigation"
		self.healthbar.coords(
			"navigation_healthbar",
			10,
			10,
			10 + (100 * self.p.health / self.p.max_health),
			30
		)

	def leave(self):
		if self.screen == "fight":
			self.flee()
		else:
			self.navigation_mode()
			self.dungeon.current_floor.disp.create_image(
				int(SMW * (p.loc[0] + .5)),
				int(SMH * (p.loc[1] + .5)),
				image=self.cur_room().en.icon,
				anchor="center"
			)

	def clear_screen(self):
		"""Remove all widgets"""

		for i in (
			self.navigation_widgets
			+ self.fight_widgets
			+ self.other_widgets
		):
			i.grid_remove()
		self.master.config(menu=self.empty_menu)

	def lose(self):
		"""Change screen to the game over screen"""

		self.screen = "game over"
		self.clear_screen()
		self.game_over.grid(row=0, column=0)

	@staticmethod
	def mouse_click(event):
		"""The mouse is clicked in the master window. Used to unfocus from the
		entry widget"""

		event.widget.focus()

	# factory necessary for tkinter key binding reasons
	# noinspection PyMethodParameters
	def movement_factory(_self, direction):
		"""Factory for moveing the character functions"""

		def move_func(self, event=None):
			"""Move in a direction"""

			if self.screen == "stairs":
				self.navigation_mode()

			if (
				self.screen != "fight"
				and self.master.focus_get() is not self.entry
			):
				self.p.move(direction)

		if not hasattr(type(_self), f"move_{direction}"):
			setattr(type(_self), "move_{direction}", move_func)
		return getattr(_self, "move_{direction}")

	# must be a factory because tkinter does not support passing arguments
	# to the functions it calls
	def buy_item_fact(self, item_name, amount=1, *args):
		"""Factory for buying things in the shop"""

		def buy_specific_item():
			"""Function to buy an item from the shop. Can not take parameters
			because tkinter does not support that"""

			for i in range(amount):
				item = self.buyable_items[item_name](*args)

				if self.p.inven["gold"].amount >= item.cost:
					if item_name in self.p.inven:
						self.p.inven[item_name].amount += 1
					else:
						self.p.inven[item_name] = item
					# passive effect from having it
					item.effect()
					if item.plurale:
						self.out.config(text=f"You bought {item_name}")
					else:
						self.out.config(text=f"You bought a {item_name}")
					self.p.inven["gold"] -= item.cost
					if hasattr(item, "tier"):
						# replace item in list of buyable items
						del self.buyable_items[item_name]
						new_item_cls = item.factory(item.tier + 1)
						self.buyable_items[new_item_cls.name] = new_item_cls

						# replace item in the menu
						self.stock.delete(
							item_name.title()
							+ ": "
							+ str(item.cost)
						)
						self.stock.add_command(
							label=(
								new_item_cls.name.title()
								+ ": "
								+ str(new_item_cls().cost)
							),
							command=self.buy_item_fact(new_item_cls.name)
						)
				else:
					self.out.config(
						text="You do not have enough Gold for that"
					)
		return buy_specific_item

	def cur_room(self):
		"""Return the Room object that they player is currently in"""

		room = self.dungeon.current_floor[self.p.loc[0]][self.p.loc[1]]
		return room
		
	def room_info(self, event):
		"""Give information about rooms by clicking on them"""

		x, y = event.x, event.y
		subjects = self.dungeon.current_floor.disp.find_overlapping(
			x - 1,
			y - 1,
			x + 1,
			y + 1
		)
		sub = []
		for i in subjects:
			if self.dungeon.current_floor.disp.type(i) == "rectangle":
				sub.append(i)
		if len(sub) == 1:
			tag = (
				self.
				dungeon.
				current_floor.
				disp.
				gettags(sub[0])[0].
				split(",")
			)
			clicked_room = (
				self.
				dungeon.
				current_floor[int(tag[0])][int(tag[1])]
			)

			if int(tag[0]) == p.loc[0] and int(tag[1]) == self.p.loc[1]:
				self.out.config(text="This is your current location.")
			elif clicked_room.visited:
				self.out.config(text=clicked_room.info)
			else:
				self.out.config(text="Unknown")

	def flee(self):
		"""Leave a fight without winning or losing"""

		chance = randint(0, 100)
		if chance > 50:
			self.navigation_mode()
			# create an icon for an enemy the player knows about
			# if there is a space in the tags tkinter will split it up so
			# don't add one
			self.dungeon.current_floor.disp.create_oval(
				SMW * self.p.loc[0] + SMW / 4,
				SMH * self.p.loc[1] + SMH / 4,
				SMW * self.p.loc[0] + SMW * 3/4,
				SMH * self.p.loc[1] + SMH * 3/4,
				fill="red",
				tags=f"enemy{str(self.p.loc[0])},{str(self.p.loc[1])}"
			)
			self.out.config(text="You got away.")
		else:
			self.cur_room().en.attack()
			self.out.config(text="You couldn't get away.")

	@staticmethod
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

		#m = match("tier ([0-9]+) ([a-z_][a-z0-9_]*)", subject)
		if m := match("tier ([0-9]+) ([a-z_][a-z0-9_]*)", subject):
			tier = m.group(1)
			general_subject = m.group(2)
		else:
			general_subject = subject


		data = {
			"command": command,
			"subject": subject,
			"general_subject": general_subject,
			"tier": tier,
		}
		return data
# END








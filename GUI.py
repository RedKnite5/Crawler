

# GUI.py

__all__ = ["GUI"]

import tkinter as tk
from tkinter import font
from re import match
from random import randint

from PIL import Image
from PIL import ImageOps
from PIL import ImageTk


from errors import *
from config import *


class MultiframeWidget(object):
	def __init__(self, frames, widget, *args, **kwargs):
		self.widgets = {}
		for name, frame in frames.items():
			self.widgets[name] = widget(frame, *args, **kwargs)

	def __getattr__(self, name):
		def f(*args, **kwargs):
			ret = []
			for widget in self.widgets.values():
				ret.append(getattr(widget, name)(*args, **kwargs))
			return ret
		return f
		

class GUI(object):
	"""The user interface for the game"""

	def __init__(self, inven):

		self.screen = "navigation"
		self.inven = inven

		self.master = tk.Tk()

		# window name
		self.master.title(string="The Dungeon")
		self.empty_menu = tk.Menu(self.master)
		
		self.init_nav_scr()
		self.init_inv_scr()
		self.init_bat_scr()
		self.init_gmo_scr()
		
		self.stats = MultiframeWidget(
			{"nav": self.nav_frame, "bat": self.bat_frame},
			tk.Message,
			text=""
		)
		self.stats.widgets["nav"].grid(row=1, column=1, columnspan=2)
		self.stats.widgets["bat"].grid(row=1, column=3)
		
		self.out = MultiframeWidget(
			{"nav": self.nav_frame, "bat": self.bat_frame},
			tk.Message,
			text="Welcome to The Dungeon. Come once, stay forever!",
			width=W + 100
		)
		self.out.widgets["nav"].grid(row=5, column=0, columnspan=4)
		self.out.widgets["bat"].grid(row=2, column=0, columnspan=3)

		# top level shop menu
		self.shop = tk.Menu(self.master)
		# drop down menu
		self.stock = tk.Menu(self.shop, tearoff=0)

		self.shop.add_cascade(menu=self.stock, label="Shop")
		# add menu to screen
		self.master.config(menu=self.shop)
		
		self.navigation_mode()
		

	def init_nav_scr(self):
	
		self.nav_frame = tk.Frame(self.master)
		
		# movement & inventory button creation
		self.b = [tk.Button(self.nav_frame) for i in range(5)]
		
		button_shape = {"width": 8, "height": 4}

		# movement button configuation
		self.b[0].configure(
			text="North",
			command=self.movement_factory("north"),
			**button_shape
		)
		self.b[3].configure(
			text="South",
			command=self.movement_factory("south"),
			**button_shape
		)
		self.b[1].configure(
			text="West",
			command=self.movement_factory("west"),
			**button_shape
		)
		self.b[2].configure(
			text="East",
			command=self.movement_factory("east"),
			**button_shape
		)

		# button placement
		self.b[0].grid(row=2, column=1)
		self.b[1].grid(row=3, column=0)
		self.b[2].grid(row=3, column=2)
		self.b[3].grid(row=4, column=1)
		self.b[4].grid(row=1, column=0)

		# health bar creation
		self.healthbar = tk.Canvas(self.nav_frame, width=100 + 10, height=30)
		self.healthbar.grid(row=0, column=0, columnspan=3)
		# health bar drawing
		self.healthbar.create_rectangle(10, 10, 10 + 100, 30)
		
		self.nav_bindings()

	def init_inv_scr(self):
		
		self.inv_frame = tk.Frame(self.master)
		
		self.back_btn = tk.Button(self.inv_frame, text="leave", command=self.leave_inv)
		self.back_btn.grid(row=0, column=1)
		
		self.inv_scr = tk.Canvas(self.inv_frame, width=W, height=H)
		self.inv_scr.grid(row=0, column=0)
		
		self.inv_scr.bind("<Button 1>", self.inv_click)
		
		self.inv_images = {}
		
		for w in range(INV_WIDTH):
			for h in range(INV_HEIGHT):
				self.inv_scr.create_rectangle(
					IBW * w + 2,
					IBH * h + 2,
					IBW * (w + 1) - 2,
					IBH * (h + 1) - 2,
					fill="grey",
					tags=f"{str(w)},{str(h)}"
				)
			
	def init_bat_scr(self):
		
		self.bat_frame = tk.Frame(self.master)
		
		#  fight screen
		self.cbt_scr = tk.Canvas(self.bat_frame, width=W + 100, height=H)
		self.cbt_scr.grid(row=0, column=0, columnspan=3)

		# for non-hostile encounters
		self.leave_btn = tk.Button(
			self.bat_frame, text="", command=self.leave
		)
		self.leave_btn
		
	def init_gmo_scr(self):
		
		self.game_over_frame = tk.Frame(self.master)
		
		self.game_over = tk.Canvas(self.game_over_frame, width=W + 100, height=H)
		self.game_over.create_rectangle(0, 0, W + 100, H + 50, fill="black")
		self.game_over.create_text(
			W/2 + 50,
			H/2,
			text="GAME OVER",
			fill="green",
			font=font.Font(size=40)
		)
		self.game_over.grid()
		
	def player_config(self, p):
		"""Configure the settings that require the player exist"""

		self.p = p

		# inventory button configuration
		self.b[4].configure(text="Inventory", command=self.disp_in)

		self.create_healthbar(p.health, p.max_health)

		self.update_stats(p.damage, p.defence)

	def nav_bindings(self):
		# key bindings
		
		self.nav_frame.bind("<Up>", self.movement_factory("north"))
		self.nav_frame.bind("<Down>", self.movement_factory("south"))
		self.nav_frame.bind("<Right>", self.movement_factory("east"))
		self.nav_frame.bind("<Left>", self.movement_factory("west"))

		self.nav_frame.bind("<Button 1>", self.mouse_click)
		
		
	def disp_in(self):
		"""Display the player's inventory"""

		self.nav_frame.grid_remove()
		self.bat_frame.grid_remove()
		
		self.inv_frame.grid(row=0, column=0)
		
		self.inv_frame.focus_set()

	def create_healthbar(self, health, max_health):
		self.healthbar.create_rectangle(
			10,
			10,
			10 + (100 * health / max_health),
			30,
			fill="green",
			tags="navigation_healthbar"
		)
		self.healthbar.create_text(
			60, 20,
			text=f"{health}/{max_health}",
			tags="navigation_healthbar_text"
		)

	def dungeon_config(self, dungeon, player_loc):
		"""Configure settings that require that the dungeon object exist
		
		Also and the player location"""
		
		self.player_loc = player_loc

		self.dungeon = dungeon
		self.dungeon.current_floor.disp.grid(row=0, column=3, rowspan=5)
		#self.dungeon.current_floor.create_display()
		# may need to do current_floor.disp.focus_set()
		self.dungeon.current_floor.disp.bind("<Button 1>", self.room_info)

		self.att_b = tk.Button(
			self.bat_frame,
			text="Attack",
			command=lambda: self.cur_room().en.be_attacked())
		self.att_b.grid(row=1, column=0)
		
		
		self.run_b = tk.Button(self.bat_frame, text="Flee", command=self.flee)
		self.run_b.grid(row=1, column=2)

		# ISSUE: what frame should this be on?
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
			self.game_over_frame,
			text="Restart",
			command=restart,
			width=10
		)
		
		self.game_over.create_window(W, H * 3/4, window=self.restart_button)
		self.restart_button.lift()

	def add_to_inv(self, item):
		index = self.inven.add(item.name, item)
		total = self.inven[index].amount
		new_text = str(total) if total > 1 else ""
		
		if index not in self.inv_images:
			x  = index % INV_WIDTH
			y = (index % (INV_WIDTH * INV_HEIGHT)) // INV_WIDTH
			icon_id = self.inv_scr.create_image(
				IBW * x + 3,
				IBH * y + 3,
				image=item.image,
				anchor="nw"
			)
			
			text_id = self.inv_scr.create_text(
				IBW * (x + 1) - 3,
				IBH * (y + 1) - 1,
				text=new_text,
				anchor="se"
			)
			
			self.inv_images[item.name] = [icon_id, text_id]
		else:
			self.inv_scr.itemconfig(self.inv_images[item.name][1], text=new_text)
	
	def sub_from_inv(self, item_name, amount):
		total = self.inven.sub(item_name, amount)
		
		if total <= 0:
			self.inv_scr.delete(self.inv_images[item_name][0])
			self.inv_scr.delete(self.inv_images[item_name][1])
			del self.inv_images[item_name]
		else:
			new_text = str(total) if total > 1 else ""
			self.inv_scr.itemconfig(self.inv_images[item_name][1], text=new_text)
		
	def leave_inv(self):
		self.inv_frame.grid_remove()
		if self.screen == "navigation":
			self.navigation_mode()
		elif self.screen == "battle":
			self.nav_frame.grid(row=0, column=0)


	def update_stats(self, damage, defence):
		"""Update the stats for the player"""

		self.stats.config(
			text=f"Damage: {damage}\nDefence: {defence}"
		)


	def update_healthbar(self, health, max_health):
		"""Update the appearance of the healthbar in both the fighting screen
		and the navigation screen"""

		self.cbt_scr.coords(
			"fight_healthbar",
			10,
			H - 30,
			10 + (100 * health / max_health),
			H - 10
		)
		self.cbt_scr.itemconfig(
			"fight_healthbar_text",
			text=f"{health}/{max_health}"
		)

		self.healthbar.coords(
			"navigation_healthbar",
			10,
			10,
			10 + (100 * health / max_health),
			30
		)
		self.healthbar.itemconfig(
			"navigation_healthbar_text",
			text=f"{health}/{max_health}"
		)

	def navigation_mode(self):
		"""Switch to navigation screen"""

		self.bat_frame.grid_remove()
		self.nav_frame.grid(row=0, column=0)
		
		self.nav_frame.focus_set()
		
		self.screen = "navigation"

	def leave(self):
		if self.screen == "fight":
			self.flee()
		else:
			self.navigation_mode()
			self.dungeon.current_floor.disp.create_image(
				int(SMW * (self.player_loc[0] + .5)),
				int(SMH * (self.player_loc[1] + .5)),
				image=self.cur_room().en.icon,
				anchor="center"
			)

	def clear_screen(self):
		"""Remove all widgets"""

		self.nav_frame.grid_remove()
		self.bat_frame.grid_remove()
		self.inv_frame.grid_remove()
		self.master.config(menu=self.empty_menu)

	def lose(self):
		"""Change screen to the game over screen"""

		self.screen = "game over"
		self.clear_screen()
		self.game_over_frame.grid(row=0, column=0)

	@staticmethod
	def mouse_click(event):
		"""The mouse is clicked in the master window. Used to unfocus from the
		entry widget"""

		event.widget.focus()
	
	def inv_click(self, event):
		
		x = event.x * INV_WIDTH // W
		y = event.y * INV_HEIGHT // H
		
		index = y * INV_WIDTH + x
		
		if index in self.inven:
			self.inven[index].use()
			self.sub_from_inv(self.inven[index].name, 1)


	# factory necessary for tkinter key binding reasons
	def movement_factory(_self, direction):
		"""Factory for moveing the character functions"""

		def move_func(self, event=None):
			"""Move in a direction"""

			if self.screen == "stairs":
				self.navigation_mode()

			if self.screen != "fight":
				self.p.move(direction)

		if not hasattr(type(_self), f"move_{direction}"):
			setattr(type(_self), "move_{direction}", move_func)
		return getattr(_self, "move_{direction}")

	# must be a factory because tkinter does not support passing arguments
	# to the functions it calls
	def buy_item_fact(self, item_name, amount=1, *args):
		"""Factory for buying things in the shop"""
		
		# Can not take parameters because tkinter does not support that
		def buy_specific_item():
			"""Function to buy an item from the shop."""

			for i in range(amount):
				item = self.buyable_items[item_name](*args)

				if self.inven["gold"].amount >= item.cost:
					self.add_to_inv(item)
					# passive effect from having it
					item.effect()
					if item.plurale:
						self.out.config(text=f"You bought {item_name}")
					else:
						self.out.config(text=f"You bought a {item_name}")
					
					#self.inven["gold"] -= item.cost
					self.sub_from_inv("gold", item.cost)
					
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

		room = self.dungeon.current_floor[self.player_loc[0]][self.player_loc[1]]
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

			if int(tag[0]) == self.player_loc[0] and int(tag[1]) == self.player_loc[1]:
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
				SMW * self.player_loc[0] + SMW / 4,
				SMH * self.player_loc[1] + SMH / 4,
				SMW * self.player_loc[0] + SMW * 3/4,
				SMH * self.player_loc[1] + SMH * 3/4,
				fill="red",
				tags=f"enemy{str(self.player_loc[0])},{str(self.player_loc[1])}"
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





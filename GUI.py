"""Module for graphical elements of Crawler"""

# GUI.py

__all__ = ["GUI"]

import tkinter as tk
from tkinter import font
from random import randint

from PIL import Image     # type: ignore
from PIL import ImageOps  # type: ignore
from PIL import ImageTk   # type: ignore


from errors import *
from config import *


class MultiframeWidget(object):
	"""Widgets which belong on more than one screen. Create multiple instances
	of the widget and delegate calls to them in a loop"""

	def __init__(
			self,
			frames: dict[str, tk.Frame],
			widget: type[tk.Widget],
			*args,
			**kwargs) -> None:

		self.widgets: dict[str, tk.Widget] = {}
		for name, frame in frames.items():
			self.widgets[name] = widget(frame, *args, **kwargs)

	def __getattr__(self, name: str):
		def f(*args, **kwargs) -> list:
			"""Run the method on all the widgets and return a list of their
			return values"""

			ret = []
			for widget in self.widgets.values():
				ret.append(getattr(widget, name)(*args, **kwargs))
			return ret
		return f


class Navigation(object):
	"""The navigation screen with the map of the current floor"""

	def __init__(
			self,
			master,
			p_max_health: int,
			p_loc,
			inv_mode,
			cur_room,
			write_out) -> None:
	
		self.frame: tk.Frame = tk.Frame(master)
		
		self.player_loc = p_loc
		self.cur_room = cur_room
		self.write_out = write_out
		
		# movement & inventory button creation
		self.b = [tk.Button(self.frame) for _ in range(5)]
		
		directions = ["north", "west", "east", "south"]
		for index, dire in enumerate(directions):
			self.b[index].configure(
				text=dire.capitalize(),
				command=self.movement_factory(dire),
				width=8, height=4
			)

		# button placement
		self.b[0].grid(row=2, column=1)
		self.b[1].grid(row=3, column=0)
		self.b[2].grid(row=3, column=2)
		self.b[3].grid(row=4, column=1)
		self.b[4].grid(row=1, column=0)
		
		# inventory button configuration
		self.b[4].configure(text="Inventory", command=inv_mode)

		# health bar creation
		self.healthbar = tk.Canvas(self.frame, width=100 + 10, height=30)
		self.healthbar.grid(row=0, column=0, columnspan=3)
		# health bar drawing
		self.healthbar.create_rectangle(10, 10, 10 + 100, 30)
		
		self.create_healthbar(p_max_health)
		
		self.map = tk.Canvas(self.frame, width=W, height=H)
		self.map.grid(row=0, column=3, rowspan=5)
		
		self.create_display()
		# may need to do current_floor.disp.focus_set()
		self.map.bind("<Button 1>", self.room_info)
		
		self.nav_bindings()
		
	def create_display(self) -> None:
		"""Create the map for the player to see"""

		# display creation
		for i in range(DUN_W):
			for k in range(DUN_H):
				# if there is a space in the tags tkinter will split it up
				# do not add one
				self.map.create_rectangle(
					SMW * i,
					SMH * k,
					SMW * (i + 1),
					SMH * (k + 1),
					fill="grey",
					tags=f"{i},{k}"
				)

		# player icon creation
		self.map.create_oval(
			SMW * self.player_loc[0],
			SMH * self.player_loc[1],
			SMW * self.player_loc[0] + SMW,
			SMH * self.player_loc[1] + SMH,
			fill="green",
			tags="player"
		)
		
	def create_healthbar(self, max_health: int) -> None:
		"""Create rectangles on the navigation screen health Canvas"""

		self.healthbar.create_rectangle(
			10,
			10,
			10 + 100,
			30,
			fill="green",
			tags="navigation_healthbar"
		)
		self.healthbar.create_text(
			60, 20,
			text=f"{max_health}/{max_health}",  # assume full health at creation
			tags="navigation_healthbar_text"
		)
		
	def update_healthbar(self, health: int, max_health: int) -> None:
		"""Update the display of the health on the navigation screen"""

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
		
	def nav_bindings(self) -> None:
		"""Bind all the relevant inputs for the nav frame"""
		
		directions = {
			"north": "Up",
			"south": "Down",
			"east": "Right",
			"west": "Left"
		}
		for cardinal, relative in directions.items():
			self.frame.bind(f"<{relative}>", self.movement_factory(cardinal))

		self.frame.bind("<Button 1>", self.mouse_click)
		
	@staticmethod
	def mouse_click(event) -> None:
		"""The mouse is clicked in the master window. Used to unfocus from the
		entry widget"""

		event.widget.focus()
		
	# factory necessary for tkinter key binding reasons
	def movement_factory(_self, direction: str):
		"""Factory for moving the character functions"""

		def move_func(self, event=None) -> None:
			"""Move in a direction"""

			"""
			if self.screen == "stairs":
			#	self.navigation_mode()

			#if self.screen != "fight":
			"""
			self.p_move(direction)

		if not hasattr(type(_self), f"move_{direction}"):
			setattr(type(_self), f"move_{direction}", move_func)
		return getattr(_self, f"move_{direction}")

	def mark_visited(self, x: int, y: int) -> None:
		"""Color the square on the map yellow and set the visited attribute of
		the room to True"""

		# if there is a space in the tags tkinter will split it up
		# do not add one
		self.map.itemconfig(
			f"{x},{y}",
			fill="yellow"
		)
		self.cur_room().visited = True
		
	def p_move(self, direction: str) -> None:
		"""Change the player's location and enter the correct room according
		to the direction"""
	
		self.mark_visited(self.player_loc[0], self.player_loc[1])

		# up
		if direction == "north" and self.player_loc[1] > 0:
			self.player_loc[1] -= 1
			self.map.move("player", 0, -1 * SMH)
		# down
		elif direction == "south" and self.player_loc[1] < DUN_H - 1:
			self.player_loc[1] += 1
			self.map.move("player", 0, SMH)
		# left
		elif direction == "west" and self.player_loc[0] > 0:
			self.player_loc[0] -= 1
			self.map.move("player", -1 * SMW, 0)
		# right
		elif direction == "east" and self.player_loc[0] < DUN_W - 1:
			self.player_loc[0] += 1
			self.map.move("player", SMW, 0)
			
		self.mark_visited(self.player_loc[0], self.player_loc[1])
		self.cur_room().enter()

	def room_info(self, event) -> None:
		"""Give information about rooms by clicking on them"""

		x, y = event.x, event.y
		subjects = self.map.find_overlapping(
			x - 1,
			y - 1,
			x + 1,
			y + 1
		)
		sub = []
		for i in subjects:
			if self.map.type(i) == "rectangle":
				sub.append(i)
		if len(sub) == 1:
			tag = self.map.gettags(sub[0])[0].split(",")
			clicked_room = self.cur_room((int(tag[0]), int(tag[1])))

			if int(tag[0]) == self.player_loc[0] and int(tag[1]) == self.player_loc[1]:
				self.write_out("This is your current location.")
			elif clicked_room.visited:
				self.write_out(clicked_room.info)
			else:
				self.write_out("Unknown")

	def remove_enemy_marker(self, x: int, y: int) -> None:
		"""Remove enemy icon on map"""

		# if there is a space in the tags tkinter will split it up
		self.map.delete(
			f"enemy{x},{y}"
		)

	def draw_enemy_marker(self, x: int, y: int) -> None:
		"""Draw a red circle to indicate there is a known enemy in a room"""

		# if there is a space in the tags tkinter will split it up so
		# don't add one
		self.map.create_oval(
			SMW * x + SMW / 4,
			SMH * y + SMH / 4,
			SMW * x + SMW * 3/4,
			SMH * y + SMH * 3/4,
			fill="red",
			tags=f"enemy{x},{y}"
		)

	def draw_encounter(self, icon, x: int, y: int) -> None:
		"""Draw a known non-hostile encounter on the map"""

		self.map.create_image(
			int(SMW * (x + .5)),
			int(SMH * (y + .5)),
			image=icon,
			anchor="center"
		)

	def remove(self) -> None:
		"""Remove the navigation frame from the master window"""

		self.frame.grid_remove()

	def show(self) -> None:
		"""Put the navigation frame on the master window and give it focus so
		bindings work correctly"""

		self.frame.grid(row=0, column=0)
		self.frame.focus_set()


class GUI(object):
	"""The user interface for the game"""

	def __init__(
			self,
			inven,
			p_damage: int,
			p_defence: int,
			p_max_health: int,
			player_loc,
			cur_room) -> None:

		self.screen: str = "navigation"
		self.inven = inven

		self.master = tk.Tk()
		
		self.player_loc = player_loc

		# window name
		self.master.title(string="The Dungeon")
		self.empty_menu = tk.Menu(self.master)
		
		self.nav = Navigation(
			self.master,
			p_max_health,
			self.player_loc,
			self.inventory_mode,
			cur_room,
			self.write_out
		)
		
		self.init_inv_scr()
		self.init_bat_scr()
		self.init_gmo_scr()
		
		self.stats = MultiframeWidget(
			{"nav": self.nav.frame, "bat": self.bat_frame},
			tk.Message,
			text=""
		)
		self.stats.widgets["nav"].grid(row=1, column=1, columnspan=2)
		self.stats.widgets["bat"].grid(row=1, column=3)
		
		self.update_stats(p_damage, p_defence)
		
		self.out = MultiframeWidget(
			{"nav": self.nav.frame, "bat": self.bat_frame},
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

	def init_inv_scr(self) -> None:
		"""Create the inventory screen"""
		
		self.inv_frame: tk.Frame = tk.Frame(self.master)
		
		self.back_btn: tk.Button = tk.Button(
			self.inv_frame,
			text="leave",
			command=self.leave_inv
		)
		self.back_btn.grid(row=0, column=1)
		
		self.inv_scr: tk.Canvas = tk.Canvas(self.inv_frame, width=W, height=H)
		self.inv_scr.grid(row=0, column=0)
		
		self.inv_scr.bind("<Button 1>", self.inv_click)
		
		self.inv_images: dict[str, list[int]] = {}
		
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
			
	def init_bat_scr(self) -> None:
		"""Create battle screen"""
		
		self.bat_frame: tk.Frame = tk.Frame(self.master)
		
		#  fight screen
		self.cbt_scr: tk.Canvas = tk.Canvas(self.bat_frame, width=W + 100, height=H)
		self.cbt_scr.grid(row=0, column=0, columnspan=3)

		# for non-hostile encounters
		self.leave_btn = tk.Button(
			self.bat_frame, text="", command=self.leave
		)
		
	def init_gmo_scr(self) -> None:
		"""Create game over screen"""
		
		self.game_over_frame: tk.Frame = tk.Frame(self.master)
		
		self.game_over: tk.Canvas = tk.Canvas(
			self.game_over_frame,
			width=W + 100,
			height=H
		)
		self.game_over.create_rectangle(0, 0, W + 100, H + 50, fill="black")
		self.game_over.create_text(
			W/2 + 50,
			H/2,
			text="GAME OVER",
			fill="green",
			font=font.Font(size=40)
		)
		self.game_over.grid()

	def inventory_mode(self) -> None:
		"""Display the player's inventory"""

		self.nav.remove()
		self.bat_frame.grid_remove()
		
		self.inv_frame.grid(row=0, column=0)
		
		self.inv_frame.focus_set()

	def dungeon_config(self, dungeon) -> None:
		"""Configure settings that require that the dungeon object exist
		
		Also and the player location"""

		self.dungeon = dungeon

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
		self.non_hostile_widgets: list[tk.Widget] = [self.inter_btn, self.leave_btn]
	
	def misc_config(self, items: tuple, restart) -> None:
		"""Configure settings that require buyable_items or the restart
		function
		"""

		self.buyable_items: dict = {item().name: item for item in items}
		
		for i in self.buyable_items:
			# actual things you can buy
			self.stock.add_command(
				label=f"{i.title()}: {str(self.buyable_items[i]().cost)}",
				command=self.buy_item_fact(i)
			)

		# collections of widgets
		self.restart_button: tk.Button = tk.Button(
			self.game_over_frame,
			text="Restart",
			command=restart,
			width=10
		)
		
		self.game_over.create_window(W, H * 3/4, window=self.restart_button)
		self.restart_button.lift()

	def add_to_inv(self, item) -> None:
		"""Add an item to the inventory data structure and draw it on the
		inventory screen"""

		index: int = self.inven.add(item.name, item)
		total: int = self.inven[index].amount
		new_text = str(total) if total > 1 else ""
		
		if item.name not in self.inv_images:
			x: int = index % INV_WIDTH
			y: int = (index % (INV_WIDTH * INV_HEIGHT)) // INV_WIDTH
			icon_id: int = self.inv_scr.create_image(
				IBW * x + 3,
				IBH * y + 3,
				image=item.image,
				anchor="nw"
			)
			
			text_id: int = self.inv_scr.create_text(
				IBW * (x + 1) - 3,
				IBH * (y + 1) - 1,
				text=new_text,
				anchor="se"
			)
			
			self.inv_images[item.name] = [icon_id, text_id]
		else:
			self.inv_scr.itemconfig(self.inv_images[item.name][1], text=new_text)
	
	def sub_from_inv(self, item_name: str, amount: int) -> None:
		"""Remove some amount of an item from the player's inventory"""

		total = self.inven.sub(item_name, amount)
		
		if total <= 0:
			self.inv_scr.delete(self.inv_images[item_name][0])
			self.inv_scr.delete(self.inv_images[item_name][1])
			del self.inv_images[item_name]
		else:
			new_text = str(total) if total > 1 else ""
			self.inv_scr.itemconfig(self.inv_images[item_name][1], text=new_text)
		
	def leave_inv(self) -> None:
		"""Switch from the inventory screen to the previous screen"""

		self.inv_frame.grid_remove()
		if self.screen == "navigation":
			self.navigation_mode()
		elif self.screen == "battle":
			self.bat_frame.grid(row=0, column=0)

	def update_stats(self, damage: int, defence: int) -> None:
		"""Update the stats for the player"""

		self.stats.config(
			text=f"Damage: {damage}\nDefence: {defence}"
		)

	def write_out(self, new_text: str) -> None:
		"""Set the content of the out widget to display messages to the
		player"""

		self.out.config(text=new_text)

	def update_healthbar(self, health: int, max_health: int) -> None:
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

		self.nav.update_healthbar(health, max_health)

	def navigation_mode(self) -> None:
		"""Switch to navigation screen"""

		self.bat_frame.grid_remove()
		self.nav.show()
		
		self.screen = "navigation"

	def leave(self) -> None:
		"""Flee a fight or leave a room"""

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

	def clear_screen(self) -> None:
		"""Remove all widgets"""

		self.nav.remove()
		self.bat_frame.grid_remove()
		self.inv_frame.grid_remove()
		self.master.config(menu=self.empty_menu)

	def lose(self) -> None:
		"""Change screen to the game over screen"""

		self.screen = "game over"
		self.clear_screen()
		self.game_over_frame.grid(row=0, column=0)
	
	def inv_click(self, event) -> None:
		"""Use an item when you click on it in the inventory"""
		
		x: int = event.x * INV_WIDTH // W
		y: int = event.y * INV_HEIGHT // H
		
		index: int = y * INV_WIDTH + x
		
		if index in self.inven:
			self.inven[index].use()
			self.sub_from_inv(self.inven[index].name, 1)

	def buy_item_fact(self, item_name: str, amount: int = 1, *args):
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
					if item.plural:
						self.out.config(text=f"You bought {item_name}")
					else:
						self.out.config(text=f"You bought a {item_name}")

					self.sub_from_inv("gold", item.cost)
					
					if hasattr(item, "tier"):
						# replace item in list of buyable items
						del self.buyable_items[item_name]
						new_item_cls = item.factory(item.tier + 1)
						self.buyable_items[new_item_cls().name] = new_item_cls

						# replace item in the menu
						self.stock.delete(
							item_name.title()
							+ ": "
							+ str(item.cost)
						)
						self.stock.add_command(
							label=(
								new_item_cls().name.title()
								+ ": "
								+ str(new_item_cls().cost)
							),
							command=self.buy_item_fact(new_item_cls().name)
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

	def flee(self):
		"""Leave a fight without winning or losing"""

		chance = randint(0, 100)
		if chance > 50:
			self.navigation_mode()
			# create an icon for an enemy the player knows about
			
			self.nav.draw_enemy_marker(self.player_loc[0], self.player_loc[1])
			
			self.out.config(text="You got away.")
		else:
			self.cur_room().en.attack()
			self.out.config(text="You couldn't get away.")


# END

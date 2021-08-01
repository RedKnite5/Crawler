"""Module for graphical elements of Crawler"""

# GUI.py

__all__ = ["GUI"]

import tkinter as tk
from tkinter import font
from random import randint

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


class Screen(object):
	"""Base class for different screens"""

	def __init__(self, master) -> None:
		self.frame: tk.Frame = tk.Frame(master)

	def remove(self) -> None:
		"""Remove the frame from the master window"""

		self.frame.grid_remove()

	def show(self) -> None:
		"""Display the screen"""

		self.frame.grid(row=0, column=0)
		self.frame.focus_set()



class Navigation(Screen):
	"""The navigation screen with the map of the current floor"""

	def __init__(
			self,
			master,
			p_max_health: int,
			p_loc: list[int],
			inv_mode,
			cur_room,
			write_out) -> None:
	
		super().__init__(master)
		
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
				self.enc.remove()
				self.nav.show()
				self.screen = "navigation"

			if self.screen != "fight":
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
	
		self.mark_visited(*self.player_loc)

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
			
		self.mark_visited(*self.player_loc)
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


class GameOver(Screen):
	"""Screen for after the player loses"""
	
	def __init__(self, master) -> None:
		super().__init__(master)
		
		self.game_over: tk.Canvas = tk.Canvas(
			self.frame,
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
		
		
		'''
		self.restart_button: tk.Button = tk.Button(
			self.game_over_frame,
			text="Restart",
			command=restart,
			width=10
		)
		
		self.game_over.create_window(W, H * 3/4, window=self.restart_button)
		self.restart_button.lift()
		'''
	

class InventoryScreen(Screen):
	"""Inventory screen"""
	
	def __init__(self, master, inven, buyable: dict, stock, leave_inv, write_out) -> None:
		super().__init__(master)
		
		self.inven = inven
		self.buyable_items = buyable
		self.stock = stock
		self.write_out = write_out
		
		for i in self.buyable_items:
			# actual things you can buy
			self.stock.add_command(
				label=f"{i.title()}: {self.buyable_items[i]().cost}",
				command=self.buy_item_fact(i)
			)
		
		self.back_btn: tk.Button = tk.Button(
			self.frame,
			text="leave",
			command=leave_inv
		)
		self.back_btn.grid(row=0, column=1)
		
		self.inv_scr: tk.Canvas = tk.Canvas(self.frame, width=W, height=H)
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
					tags=f"{w},{h}"
				)

	def inv_click(self, event) -> None:
		"""Use an item when you click on it in the inventory"""
		
		x: int = event.x * INV_WIDTH // W
		y: int = event.y * INV_HEIGHT // H
		
		index: int = y * INV_WIDTH + x
		
		try:
			if index in self.inven:
				self.inven[index].use()
				self.sub_from_inv(self.inven[index].name, 1)
		except AttributeError:
			pass

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
						self.write_out(f"You bought {item_name}")
					else:
						self.write_out(f"You bought a {item_name}")

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
					self.write_out("You do not have enough Gold for that")
					
		return buy_specific_item		


class Battle(Screen):
	"""Screen for fighting enemies"""

	def __init__(self, master, cur_room, flee) -> None:
		super().__init__(master)
		
		#  fight screen
		self.cbt_scr: tk.Canvas = tk.Canvas(self.frame, width=W + 100, height=H)
		self.cbt_scr.grid(row=0, column=0, columnspan=3)
		
		self.att_b: tk.Button = tk.Button(
			self.frame,
			text="Attack",
			command=lambda: cur_room().en.be_attacked()
		)
		self.att_b.grid(row=1, column=0)

		self.run_b: tk.Button = tk.Button(self.frame, text="Flee", command=flee)
		self.run_b.grid(row=1, column=2)

	def update_healthbar(self, health: int, max_health: int) -> None:
		"""Update the healthbar on the battle screen"""
	
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

	def show_image(self, image: ImageTk.PhotoImage) -> None:
		"""Display the image of the enemy"""
		
		self.cbt_scr.create_image(
			210,
			40,  # 40 is the nw
			image=image,
			anchor="nw"
		)

	def fight(self, en_health: int, en_max_health: int, p_health: int, p_max_health: int) -> None:
		"""Set up fight screen"""
		
		self.cbt_scr.delete("all")

		# enemy health bar
		self.cbt_scr.create_rectangle(W + 90, 10, W - 10, 30)

		# enemy health
		self.cbt_scr.create_rectangle(
			W + 90,
			10,
			W + 90 - (100 * en_health / en_max_health),
			30,
			fill="red",
			tags="en_bar"
		)

		# player healthbar
		self.cbt_scr.create_rectangle(
			10,
			H - 30,
			110,
			H - 10
		)
		self.cbt_scr.create_rectangle(
			10,
			H - 30,
			10 + (100 * p_health / p_max_health), H - 10,
			fill="green",
			tags="fight_healthbar"
		)
		self.cbt_scr.create_text(
			60,
			H - 20,
			text=f"{p_health}/{p_max_health}",
			tags="fight_healthbar_text"
		)

	def update_en_healthbar(self, health: int, max_health: int) -> None:
		"""Update the enemy healthbar"""
		
		self.cbt_scr.coords(
			"en_bar",
			W + 90, 10, W + 90 - (100 * health / max_health), 30
		)


class EncounterScreen(Screen):
	"""Encounter screen of non hostile nature"""

	def __init__(self, master, cur_room, leave) -> None:
		super().__init__(master)
		
		self.enc_scr: tk.Canvas = tk.Canvas(self.frame, width=W + 100, height=H)
		self.enc_scr.grid(row=0, column=0, columnspan=4)

		# Having a button labeled "Leave" also sounds like going down
		# the stairs
		self.leave_btn = tk.Button(
			self.frame, text="Leave", command=leave
		)
		self.leave_btn.grid(row=1, column=2)

		self.inter_btn: tk.Button = tk.Button(
			self.frame,
			text="",
			command=lambda: cur_room().en.interact()
		)
		self.inter_btn.grid(row=1, column=1)

	def show_image(self, image: ImageTk.PhotoImage, place: str) -> None:
		"""Show the encounter image"""
		
		self.enc_scr.create_image(
			210,
			130,  # 130 is the center
			image=image,
			anchor=place
		)



class GUI(object):
	"""The user interface for the game"""

	def __init__(
			self,
			inven,
			buyable: tuple,
			p_damage: int,
			p_defence: int,
			p_max_health: int,
			player_loc,
			cur_room,) -> None:

		self.screen: str = "navigation"

		self.master = tk.Tk()
		
		self.player_loc = player_loc

		# window name
		self.master.title(string="The Dungeon")
		self.empty_menu = tk.Menu(self.master)
		
		# top level shop menu
		self.shop = tk.Menu(self.master)
		# drop down menu
		self.stock = tk.Menu(self.shop, tearoff=0)

		self.shop.add_cascade(menu=self.stock, label="Shop")
		
		buyable_items: dict = {item().name: item for item in buyable}
		
		# add menu to screen
		self.master.config(menu=self.shop)
		
		
		self.nav = Navigation(
			self.master,
			p_max_health,
			self.player_loc,
			self.inventory_mode,
			cur_room,
			self.write_out
		)
		
		self.gmo = GameOver(
			self.master
		)
		
		self.inv = InventoryScreen(
			self.master,
			inven,
			buyable_items,
			self.stock,
			self.leave_inv,
			self.write_out
		)
		
		self.bat = Battle(
			self.master,
			cur_room,
			self.flee
		)
		
		self.enc = EncounterScreen(
			self.master,
			self.cur_room,
			self.leave
		)
		
		self.stats = MultiframeWidget(
			{
				"nav": self.nav.frame,
				"bat": self.bat.frame,
				"inv": self.inv.frame
			},
			tk.Message,
			text=""
		)
		self.stats.widgets["nav"].grid(row=1, column=1, columnspan=2)
		self.stats.widgets["bat"].grid(row=1, column=3)
		self.stats.widgets["inv"].grid(row=0, column=2)
		
		self.update_stats(p_damage, p_defence)
		
		self.out = MultiframeWidget(
			{
				"nav": self.nav.frame,
				"bat": self.bat.frame,
				"inv": self.inv.frame
			},
			tk.Message,
			text="Welcome to The Dungeon. Come once, stay forever!",
			width=W + 100
		)
		self.out.widgets["nav"].grid(row=5, column=0, columnspan=4)
		self.out.widgets["bat"].grid(row=2, column=0, columnspan=3)
		self.out.widgets["bat"].grid(row=2, column=1, columnspan=3)
		
		self.nav.show()
		self.screen = "navigation"

	def show_image(self, image: ImageTk.PhotoImage, enemy: bool, place: str) -> None:
		"""Show the image on the battle screen or the encounter screen"""
		
		if enemy:
			self.bat.show_image(image)
			return
	
		if image:
			# encounter icon
			self.enc.show_image(image, place.lower())

	def inventory_mode(self) -> None:
		"""Display the player's inventory"""

		self.nav.remove()
		self.bat.remove()
		
		self.inv.show()

	def dungeon_config(self, dungeon) -> None:
		"""Configure settings that require that the dungeon object exist"""

		self.dungeon = dungeon

	def leave_inv(self) -> None:
		"""Switch from the inventory screen to the previous screen"""

		self.inv.remove()
		if self.screen == "navigation":
			self.nav.show()
		elif self.screen == "battle":
			self.bat.show()

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

		self.bat.update_healthbar(health, max_health)
		self.nav.update_healthbar(health, max_health)

	def leave(self) -> None:
		"""Flee a fight or leave a room"""

		if self.screen == "fight":
			self.flee()
		else:
			self.enc.remove()
			self.nav.show()
			self.screen = "navigation"
			
			self.nav.draw_encounter(
				self.cur_room().en.icon,
				*self.player_loc,
			)

	def clear_screen(self) -> None:
		"""Remove all frames and menus"""

		self.nav.remove()
		self.bat.remove()
		self.inv.remove()
		self.enc.remove()
		self.master.config(menu=self.empty_menu)

	def lose(self) -> None:
		"""Change screen to the game over screen"""

		self.screen = "game over"
		self.clear_screen()
		self.gmo.show()

	def cur_room(self):
		"""Return the Room object that they player is currently in"""

		return self.dungeon.current_floor[self.player_loc[0]][self.player_loc[1]]

	def flee(self) -> None:
		"""Leave a fight without winning or losing"""

		chance = randint(0, 100)
		if chance > 50:
			self.bat.remove()
			self.nav.show()
			self.screen = "navigation"
			
			# create an icon for an enemy the player knows about
			self.nav.draw_enemy_marker(*self.player_loc)
			
			self.write_out("You got away.")
		else:
			self.cur_room().en.attack()
			self.write_out("You couldn't get away.")


# END

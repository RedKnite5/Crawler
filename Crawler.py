import tkinter as tk
from tkinter import font
import random as rand
from math import fabs as abs
from math import atan, pi
from itertools import chain
from PIL import Image
from PIL import ImageTk
from PIL import ImageOps
#    python Crawler1.py


dun_w = 11   # number of rooms wide         # variable intialization
dun_h = 11
w=300  # width of map screen
h=300
cost_mul = 1
starting_gold = 150
distance_diff = 70
default_max_health = 100
default_damage = 10
heal_pot_val = 50
slime_heart_val = 5

smw = w / dun_w  # width of a room in pixels
smh = h / dun_h
screen = "navigation"
monsters_killed = 0

master = tk.Tk()
master.title(string="The Dungeon")  # window name

end_font = font.Font(size=40)  # more advanced variable initialization
empty_menu = tk.Menu(master)
output = tk.StringVar()
output.set("Welcome to The Dungeon!")

stats_output = tk.StringVar()
stats_output.set("")

default_image = Image.open("ImageNotFound_png.png")
default_image = default_image.resize((180, 180))
default_tkimage = ImageTk.PhotoImage(default_image)

goblin_image = Image.open("TypicalGoblin_png.png")  # enemy icon stuff
goblin_image = ImageOps.mirror(goblin_image.resize((180, 180)))
gob_tkimage = ImageTk.PhotoImage(goblin_image)

slime_image = Image.open("SlimeMonster_png.png")
slime_image = slime_image.resize((180, 180))
slime_tkimage = ImageTk.PhotoImage(slime_image)


class room(object):
	'''Class for individual cells with encounters in them.'''
	
	def __init__(self, difficulty):
		"room creation"
		
		self.visited = False
		self.type = rand.randint(1, 1000) + difficulty
		if self.type > 1100:
			self.info = "This is a room with a slime monster"
			self.en = Slime()
		elif 1100 >= self.type > 100:
			self.info = "This is a room with a goblin"
			self.en = Goblin()  # enemy generation
		elif self.type <= 100:
			self.info = "This is an empty room"
			self.en = Enemy()

	def enter(self):
		"Set up to enter a room."
		output.set(self.info)
		if self.en.alive == True:
			if self.type > 100:
				clear_screen()
				cbt_scr.grid(row=0, column=0, columnspan=3)
				att_b.grid(row=1, column=0)
				b[4].grid(row=1, column=1)
				stats.grid(row=1, column=3)
				run_b.grid(row=1, column=2)
				out.grid(row=2, column=0, columnspan=3)
				entry.grid(row=3, column=0, columnspan=3)
				
				self.en.fight()


class Collectable_Item(object):
	'''Class for any item that can be gained by the player.'''
	
	def __init__(self, amount=1):
		self.amount = amount
		self.name = "undefined_collectable_item"
	
	def __str__(self):
		return self.name
	
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


class Gold(Collectable_Item):
	'''Collectable currency'''

	def __init__(self, amount=0):
		super().__init__(amount)
		self.name = "gold"


class Player(object):
	'''Class for the player. Includes stats and actions.'''
	
	def __init__(self, race="human"):
		"setting stats and variables"
		
		self.loc = [int((dun_w - 1) / 2), int((dun_h - 1) / 2)]
		self.max_health = default_max_health
		self.health = self.max_health
		self.damage = default_damage
		self.defence = 0
		self.inven = {"gold": Gold(starting_gold)}
		self.equipment = {}
		
	def move(self,dir):
		"player movement on map function"
		
		dun[self.loc[0]][self.loc[1]].visited = True
		disp.itemconfig(
			str(self.loc[0]) + "," + str(self.loc[1]),
			fill="yellow")
		
		if dir == "north" and self.loc[1] > 0:   # up
			self.loc[1] -= 1
			disp.move("player", 0, -1 * smh)
		elif dir == "south" and self.loc[1] < dun_h-1:  # down
			self.loc[1] += 1
			disp.move("player", 0, smh)
		elif dir == "west" and self.loc[0] > 0:  # left
			self.loc[0] -= 1
			disp.move("player", -1 * smw, 0)
		elif dir == "east" and self.loc[0] < dun_w-1:  # right
			self.loc[0] += 1
			disp.move("player", smw, 0)
		dun[self.loc[0]][self.loc[1]].enter()
			
	def disp_in(self):
		'''Display the player's inventory'''

		hold = ""
		for key, val in self.inven.items():
			hold += "\n" + str(key).title() + ": " + str(val.amount)
		output.set(hold[1:])

p = Player()  # player creation


class Enemy(object):
	def __init__(self): #   create enemy
		self.alive = True
		self.max_health = 1
		self.health = 1
		self.damage = 1
		self.loot = {"undefined_collectable_item": Collectable_Item()}  # must be done again after stats are finalized
		self.image = default_tkimage
		
	def fight(self):
		global screen
		
		screen = "fight"
		cbt_scr.create_rectangle(w + 90, 10, w - 10, 30) # enemy health bar
		
		cbt_scr.create_rectangle(   # enemy health
			w + 90, 10, w + 90 - (100 * self.health / self.max_health), 30,
			fill="red", tags="en_bar")
		
		cbt_scr.create_rectangle(
			10, h - 30, 10 + p.max_health, h - 10) # player healthbar
		cbt_scr.create_rectangle(
			10, h - 30, 10 + (100 * p.health / p.max_health), h - 10,
			fill="green", tags="fight_healthbar")
		cbt_scr.create_text(
			60, h - 20,
			text="{0}/{1}".format(p.health, p.max_health),
			tags="fight_healthbar_text")
		
		cbt_scr.create_image(     # enemy icon
			210, 40, image=self.image, anchor="nw")
	
	def en_attack(self):  # attack the player
		damage_delt = 0
		damage_delt = round(self.damage * (1 - 2 * atan(p.defence / 20) / pi))
		p.health -= damage_delt
		if p.health <= 0:
			lose()
		update_healthbar()
		output.set("The enemy did " + str(damage_delt) + " damage!")
		
	def be_attacked(self):  # the player attacks
		self.health -= p.damage
		if self.health <= 0:
			self.die()
		cbt_scr.coords(
			"en_bar",
			w + 90, 10, w + 90 - (100 * self.health / self.max_health), 30)
		if self.alive == True:
			self.en_attack()
		
	def die(self):
		global monsters_killed
		
		self.alive = False
		monsters_killed += 1
		hold = "You got: \n"
		for key, val in self.loot.items():  # display loot
			hold += str(key).title() + ": " + str(val.amount) + "\n"
		output.set(hold)
		
		disp.delete("enemy" + str(p.loc[0]) + "," + str(p.loc[1]))
		cur_room().info = "This is an empty room."
		
		for i in self.loot:  # take loot
			if i in p.inven:
				p.inven[i] += self.loot[i]
			else:
				p.inven[i] = self.loot[i]
				
		navigation_mode()


class Goblin(Enemy):
	'''Common weak enemy'''
	
	def __init__(self):
		super().__init__()
		self.max_health = rand.randint(30, 40) + monsters_killed
		self.health = self.max_health
		self.damage = rand.randint(3, 8) + monsters_killed // 3
		self.loot = {
			"gold": Gold(self.max_health // 3 + self.damage // 2 + 2)
		}
		if rand.randint(0, 2) == 0:
			self.loot["health potion"] = Health_Pot()
		self.image = gob_tkimage


class Slime(Enemy):
	'''Higher level enemy'''

	def __init__(self):
		super().__init__()
		self.max_health = rand.randint(50, 70) + (3 * monsters_killed) // 2
		self.health = self.max_health
		self.damage = rand.randint(10, 20) + monsters_killed // 2
		self.loot = {
			"gold": Gold(self.max_health // 3 + self.damage // 2 + 2)
		}
		if rand.randint(0, 15) == 0:
			self.loot["slime heart"] = Slime_Heart()
		
		self.image = slime_tkimage


class Usable_Item(Collectable_Item):
	'''An item that can be used and consumed on use'''

	def __init__(self):
		super().__init__()
		self.name = "undefined_usable_item"
	
	def use(self):
		output.set("Used " + self.name.title())
		p.inven[self.name] -= 1


class Equipable_Item(Collectable_Item):
	'''An item that can be equiped and unequiped'''

	def __init__(self):
		super().__init__()
		self.name = "undefined_equipable_item"
		self.space = equipment[self.name]
		self.equiped = False  # would prefer for this to be a temp variable
	
	def equip(self):
		if occupied_equipment(p.equipment).count(self.space[0]) >= \
			self.space[1]:
			output.set(
				"You can not equip more than {} of this".format(
					self.space[1]))
		else:
			self.equiped = True
			output.set("You equip the " + self.name)
			p.inven[self.name] -= 1
			
			if self.space[0] not in occupied_equipment(p.equipment):
				p.equipment[self.name] = [self.space, 1]
			else:
				p.equipment[self.name][1] += 1

	
	def unequip(self):
		if self.name in p.equipment:
			self.unequiped = True  # would prefer for this to be a
			                       # temporary variable
			p.inven[self.name] += 1
			p.equipment[self.name][1] -= 1
			if p.equipment[self.name][1] <= 0:
				p.equipment.pop(self.name)
		

class Buyable_Item(Collectable_Item):
	'''An item that is sold in the shop'''

	def __init__(self):
		super().__init__()
		self.cost = 0
		self.name = "undefined_buyable_item"

	def __str__(self):
		return self.name
		
	def effect(self):
		"The effect the item has just my having it"

		pass


class Health_Pot(Usable_Item):
	'''An item that heals the player'''

	def __init__(self):
		super().__init__()
		self.name = "health potion"
	
	def use(self):
		super().use()
		p.health += heal_pot_val
		if p.health > p.max_health:
			p.health = p.max_health
		
		update_healthbar()


class Slime_Heart(Usable_Item):
	'''An item that increases the player's max HP'''
	
	def __init__(self):
		super().__init__()
		self.name = "slime heart"

	def use(self):
		super().use()
		p.max_health += slime_heart_val
		p.health += slime_heart_val

		update_healthbar()


class Sword(Buyable_Item, Equipable_Item):  # sword in shop
	def __init__(self):
		super().__init__()
		self.name = "sword"
		self.cost = 50 * cost_mul
		self.space = equipment[self.name]
		
	def equip(self):
		super().equip()
		if self.equiped:
			p.damage += 5
			self.equiped = False  # reset this variable
			update_stats()
	
	def unequip(self):
		super().unequip()
		if self.unequiped:
			p.damage -= 5
			self.unequiped = False  # reset this variable
			update_stats()


class Armor(Buyable_Item, Equipable_Item):
	def __init__(self):
		super().__init__()
		self.name = "armor"
		self.cost = 100 * cost_mul
		self.space = equipment[self.name]

	def equip(self):
		super().equip()
		if self.equiped:
			p.defence += 10
			self.equiped = False  # reset this variable
			update_stats()
	
	def unequip(self):
		super().unequip()
		if self.unequiped:
			p.defence -= 10
			self.unequiped = False  # reset this variable
			update_stats()


def move_north(): p.move("north")  #  button functions
def move_south(): p.move("south")
def move_west(): p.move("west")
def move_east(): p.move("east")

def up_key(event):  # key binding functions
	if screen == "navigation":
		p.move("north")
def down_key(event):
	if screen == "navigation":
		p.move("south")
def right_key(event):
	if screen == "navigation":
		p.move("east")
def left_key(event):
	if screen == "navigation":
		p.move("west")
		
def enter_key(event):
	'''This function triggers when you press the enter key in the
	entry box. It is to use or equip something in your inventory'''

	item = entry.get().lower()

	if item in p.inven:
		if p.inven[item].amount > 0:
			if isinstance(p.inven[item], Usable_Item):
				p.inven[item].use()
			elif item in equipment:
				p.inven[item].equip()
			else:
				output.set("That item is not usable")
		else:
			output.set("You do not have any of that")
	else:
		output.set("You do not have any of that")


def occupied_equipment(ment):
	"Figure out what equipment spaces are used"
	vals = tuple(ment.values())
	total = []
	for i in vals:
		total += [i[0][0]] * i[1]
	return total


def update_healthbar():
	cbt_scr.coords(
		"fight_healthbar",
		10, h - 30, 10 + (100 * p.health / p.max_health), h - 10)
	cbt_scr.itemconfig(
		"fight_healthbar_text",
		text="{0}/{1}".format(p.health, p.max_health))
	
	healthbar.coords(
		"navigation_healthbar",
		10, 10, 10 + (100 * p.health / p.max_health), 30)
	healthbar.itemconfig(
		"navigation_healthbar_text",
		text="{0}/{1}".format(p.health, p.max_health))


def buy_item_fact(item_name, amount=1, *args):
	'''Factor for buying things in the shop'''

	def buy_specific_item():
		for i in range(amount):
			item = buyable_items[item_name](*args)
			
			if p.inven["gold"].amount >= item.cost:
				if item_name in p.inven:
					p.inven[item_name].amount += 1
				else:
					p.inven[item_name] = item
				item.effect()    #   passive effect from having it
				output.set("You bought a " + item_name)
				p.inven["gold"] -= item.cost
			else:
				output.set("You do not have enough Gold for that")
	return buy_specific_item


buyable_items = {
	"sword": Sword,
	"armor": Armor
}

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
	"Return the Room object that they player is currently in"

	room = dun[p.loc[0]][p.loc[1]]
	return(room)


def clear_screen():
	"Remove all widgets"

	for i in navigation_widgets + fight_widgets + other_widgets:
		i.grid_remove()
	master.config(menu=empty_menu)


def attack():
	cur_room().en.be_attacked()

	
def flee():  # leave a fight
	chance = rand.randint(0, 100)
	if chance > 50:
		navigation_mode()
		disp.create_oval(    # create an icon for an enemy the player knows
			smw * p.loc[0] + smw / 4, smh * p.loc[1] + smh / 4,    #   about
			smw * p.loc[0] + smw * 3/4, smh * p.loc[1] + smh * 3/4,
			fill="red", tags="enemy" + str(p.loc[0]) + "," + str(p.loc[1]))
		cur_room().info = "A room with an enemy in it."
		output.set("You got away.")
	else:
		cur_room().en.en_attack()
		output.set("You couldn't get away.")


def navigation_mode():
	"Switch to navigation screen"
	global screen
	cbt_scr.delete("all")
	for i in fight_widgets:
		i.grid_remove()
	for i in navigation_widgets:
		i.grid()
	out.grid(row=5, column=0, columnspan=4)
	b[4].grid(row=1, column=0)
	entry.grid(row=6, column=1, columnspan=2)
	stats.grid(row=1, column=1, columnspan=2)
	master.config(menu=shop)
	screen = "navigation"
	healthbar.coords(
		"navigation_healthbar",
		10, 10, 10 + (100 * p.health / p.max_health), 30)

	
def room_info(event):
	"Give information about rooms by clicking on them"
	x, y = event.x, event.y
	subjects = disp.find_overlapping(x - 1, y - 1, x + 1, y + 1)
	sub = []
	for i in subjects:
		if disp.type(i) == "rectangle":
			sub.append(i)
	if len(sub) == 1:
		tag = disp.gettags(sub[0])[0].split(",")
		clicked_room = dun[int(tag[0])][int(tag[1])]
		
		if int(tag[0]) == p.loc[0] and int(tag[1]) == p.loc[1]:
			output.set("This is your current location.")
		elif clicked_room.visited == True:
			output.set(clicked_room.info)
		else:
			output.set("Unknown")


def lose():
	screen = "game over"
	clear_screen()
	game_over.grid(row=0,column=0)


def update_stats():
	stats_output.set(
		"Damage: {0}\nDefence: {1}".format(p.damage, p.defence))


def restart():
	global dun, p, monsters_killed
	
	del dun
	dun = gen_dun(1)
	
	del p
	p = Player()
	
	monsters_killed = 0
	
	update_healthbar()
	update_stats()
	game_over.grid_remove()
	screen = "navigation"
	navigation_mode()
	disp.delete("all")
	create_display()
	output.set("Welcome to The Dungeon!")
	

def gen_dun(floor):
	'''Generate a floor of the Dungeon'''
	
	dun = []
	for i in range(dun_w): # map generation
		column = []
		for k in range(dun_h):
			column.append(room((abs(i - 5) + abs(k - 5)) * distance_diff))
		dun.append(column)
	dun[int((dun_w - 1) / 2)][int((dun_h - 1) / 2)].type = 0
	dun[int((dun_w - 1) / 2)][int((dun_h - 1) / 2)].info = \
		"This is the starting room. There is nothing of significance here."
	return dun


def create_display():
	for i in range(dun_w):  #  display creation
		for k in range(dun_h):
			disp.create_rectangle(
				smw * i, smh * k, smw * i + smw, smh * k + smh,
				fill="grey", tags=str(i) + "," + str(k))

	disp.create_oval(
		smw * p.loc[0] ,smh * p.loc[1], # player icon creation
		smw * p.loc[0] + smw, smh * p.loc[1] +smh,
		fill = "green", tags = "player")


dun = gen_dun(1)

b = [tk.Button(master) for i in range(5)] # button creation
	
b[0].configure(text="North", command=move_north) # button configuation
b[3].configure(text="South", command=move_south)
b[1].configure(text="West", command=move_west)
b[2].configure(text="East", command=move_east)

b[4].configure(text="Inventory", command=p.disp_in) # more button configuration

b[0].grid(row=2, column=1) # button placement
b[1].grid(row=3, column=0)
b[2].grid(row=3, column=2)
b[3].grid(row=4, column=1)
b[4].grid(row=1, column=0)


disp = tk.Canvas(master, width=w, height=h)  # canvas creation
disp.grid(row=0, column=3, rowspan=5)

create_display()

healthbar = tk.Canvas(
	master, width=100 + 10, height=30) # health bar creation
healthbar.grid(row=0, column=0, columnspan=3)

healthbar.create_rectangle(10, 10, 10 + 100, 30)  # health bar drawing
healthbar.create_rectangle(10, 10, 10 + (100 * p.health / p.max_health), 30,
	fill="green", tags="navigation_healthbar")
healthbar.create_text(
	60, 20,
	text="{0}/{1}".format(p.health, p.max_health),
	tags="navigation_healthbar_text")

update_stats()
stats = tk.Message(master, textvariable=stats_output)
stats.grid(row=1, column=1, columnspan=2)

out = tk.Message(
	master, textvariable=output, width=w + 100)  # output text creation
out.grid(row=5, column=0, columnspan=4)

entry = tk.Entry(master)
entry.grid(row=6, column=1, columnspan=2)

shop = tk.Menu(master) # top level shop menu
stock = tk.Menu(shop, tearoff=0) # drop down menu
for i in buyable_items:
	stock.add_command(   # actual things you can buy
		label=i.title() + " " + str(buyable_items[i]().cost),
		command=buy_item_fact(i))

shop.add_cascade(menu=stock, label="Shop")
master.config(menu=shop) # add menu to screen

restart_button = tk.Button(
	master, text="Restart", command=restart, width=10)

game_over = tk.Canvas(master, width=w + 100, height=h)
game_over.create_rectangle(0, 0, w + 100, h + 50, fill="black")
game_over.create_text(
	w/2 + 50, h/2,
	text="GAME OVER", fill="green", font=end_font)
game_over.create_window(w, h * 3/4, window=restart_button)
restart_button.lift()

#     fight screen
cbt_scr = tk.Canvas(master, width=w + 100, height=h)

att_b = tk.Button(master, text="Attack", command=attack)
run_b = tk.Button(master, text="Flee", command=flee)

fight_widgets = [cbt_scr, att_b, run_b]
navigation_widgets = b[:-1] + [disp, healthbar, out]
other_widgets = [b[4], entry, stats, restart_button, game_over]


master.bind("<Up>", up_key)  # key bindings
master.bind("<Down>", down_key)
master.bind("<Right>", right_key)
master.bind("<Left>", left_key)

master.bind("<Return>", enter_key)
disp.bind("<Button 1>", room_info)

master.mainloop()

import unittest

import pyautogui

from config import *
from errors import *
from inven import Inventory
from GUI import GUI
from Crawler import *

class Item(object):
	def __init__(self, name):
		self.name = name


class TestInventory(unittest.TestCase):
	def test_insert1(self):
		i = Inventory()
		i.insert("item", Item("item"))
		self.assertTrue("item" in i)
	
	def test_insert2(self):
		i = Inventory()
		i.insert("item", Item("item"))
		self.assertTrue(0 in i)











if __name__ == "__main__":

	unittest.main()

	'''
	print("\n" * 3)

	monsters_killed = 0

	inventory = Inventory()

	buyable = (Sword, HealthPot, armor_factory(1))

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

	dungeon = Dungeon()
	gui.dungeon_config(dungeon)

	p.floor = dungeon.current_floor

	gui.master.mainloop()
	'''


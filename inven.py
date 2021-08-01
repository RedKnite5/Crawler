"""Module for the inventory class """

from errors import *
from config import *

__all__ = ["Inventory"]


class InventoryIterator(object):
	"""Iterator for the inventory class"""

	def __init__(self, d_iter) -> None:
		self.d = d_iter

	def __iter__(self):
		return self

	def __next__(self):
		return next(self.d)[0]


class Inventory(object):
	"""Class to store all the items the player has"""

	def __init__(self) -> None:

		# every item is stored under its name as: [item, index] in data
		# and under index as: item in flat
		self.data: dict = {}
		self.flat: dict = {}
		self.pages: int = 1

	def __getattr__(self, attr: str):
		return getattr(self.data, attr)

	def __getitem__(self, key):
		if isinstance(key, str):
			return self.data[key][0]
		elif isinstance(key, int):
			return self.flat[key]

		raise InvalidInventoryKey(f"type: {type(key)}")

	def __setitem__(self, key, item) -> None:
		if isinstance(key, str):
			if key in self.data:
				num = self.data[key][1]
				self.data[key][0] = item
				self.flat[num] = item
			else:
				self.insert(key, item)
		elif isinstance(key, int):
			self.flat[key] = item
			self.data[item.name] = [item, key]
		else:
			raise InvalidInventoryKey(f"type: {type(key)}")

	def __delitem__(self, key) -> None:
		if isinstance(key, str):
			num = self.data[key][1]
			del self.data[key]
			del self.flat[num]
		elif isinstance(key, int):
			name = self.flat[key].name
			del self.flat[key]
			del self.data[name]
		else:
			raise InvalidInventoryKey(f"type: {type(key)}")

	def __len__(self) -> int:
		return len(self.data)

	def __contains__(self, key) -> bool:
		if isinstance(key, str):
			return key in self.data
		elif isinstance(key, int):
			return key in self.flat

		raise InvalidInventoryKey(f"type: {type(key)}")

	def __iter__(self) -> InventoryIterator:
		return InventoryIterator(iter(self.data))

	def add(self, key: str, item) -> int:
		"""Add an item to both dictionaries"""

		# it is the same object in both dictionaries
		if key in self.data:
			self.data[key][0] += item
			return self.data[key][1]
		else:
			return self.insert(key, item)

	def insert(self, key: str, item) -> int:
		"""Insert an new item to both dictionaries"""

		index: int = 0
		for index in range(len(self.flat) + 1):
			if index not in self.flat:
				self.flat[index] = item
				break
		self.data[key] = [item, index]
		if index > INV_WIDTH * INV_HEIGHT * self.pages:
			self.pages += 1
		return index

	def sub(self, key, amount: int) -> int:
		"""Remove a certain amount of an item from the inventory and remove
		it from both dictionaries if appropriate"""

		count: int = 0
		if isinstance(key, str):
			self.data[key][0] -= amount

			count = self.data[key][0].amount
			if count <= 0:
				index = self.data[key][1]
				del self.data[key]
				del self.flat[index]
		elif isinstance(key, int):
			self.flat[key] -= amount

			count = self.flat[key].amount
			if count <= 0:
				name = self.flat[key].name
				del self.flat[key]
				del self.data[name]
		else:
			raise InvalidInventoryKey(f"type: {type(key)}")

		return count


# END

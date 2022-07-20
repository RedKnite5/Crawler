"""Module for the inventory class """

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterator
from typing import (TYPE_CHECKING, overload, Literal,
					Callable, cast, Protocol, TypeVar,
					Generic)

from errors import *
from config import *

__all__ = ["Inventory"]

class HasNameProtocol(Protocol):
	name: str
	amount: int

	def __iadd__(self, other: HasName | int) -> HasName: ...
	def __sub__(self, other: HasName | int) -> HasName: ...
	def __isub__(self, other: HasName | int) -> HasName: ...

HasName = TypeVar("HasName", bound=HasNameProtocol)



@dataclass
class ItemAndIndex(Generic[HasName]):
	item: HasName
	index: int
	
	@overload
	def __getitem__(self, index: Literal[0]) -> HasName: ...

	@overload
	def __getitem__(self, index: Literal[1]) -> int: ...
	
	def __getitem__(self, index: Literal[0, 1]) -> HasName | int:
		if index == 0:
			return self.item
		elif index == 1:
			return self.index

	def __setitem__(self, index: Literal[0, 1], value: HasName | int) -> None:
		if index == 0:
			value = cast(HasName, value)
			self.item = value
		elif index == 1:
			value = cast(int, value)
			self.index = value

	
class InventoryIterator(object):
	"""Iterator for the inventory class"""

	def __init__(self, d_iter: Iterator[str]) -> None:
		self.d: Iterator[str] = d_iter

	def __iter__(self) -> Iterator[str]:
		return self

	def __next__(self) -> str:
		return next(self.d)[0]


class Inventory(Generic[HasName]):
	"""Class to store all the items the player has"""

	def __init__(self) -> None:

		# every item is stored under its name as: [item, index] in data
		# and under index as: item in flat
		self.data: dict[str, ItemAndIndex] = {}
		self.flat: dict[int, HasName] = {}
		self.pages: int = 1

	def __getattr__(self, attr: str) -> Callable:
		return getattr(self.data, attr)

	def __getitem__(self, key: str | int) -> HasName:
		if isinstance(key, str):
			return self.data[key][0]
		elif isinstance(key, int):
			return self.flat[key]

		raise InvalidInventoryKey(f"type: {type(key)}")

	def __setitem__(self, key: str | int, item: HasName) -> None:
		if isinstance(key, str):
			if key in self.data:
				num = self.data[key][1]
				self.data[key][0] = item
				self.flat[num] = item
			else:
				self.insert(key, item)
		elif isinstance(key, int):
			self.flat[key] = item
			self.data[item.name] = ItemAndIndex(item, key)
		else:
			raise InvalidInventoryKey(f"type: {type(key)}")

	def __delitem__(self, key: str | int) -> None:
		if isinstance(key, str):
			num: int = self.data[key][1]
			del self.data[key]
			del self.flat[num]
		elif isinstance(key, int):
			name: str = self.flat[key].name
			del self.flat[key]
			del self.data[name]
		else:
			raise InvalidInventoryKey(f"type: {type(key)}")

	def __len__(self) -> int:
		return len(self.data)

	def __contains__(self, key: str | int) -> bool:
		if isinstance(key, str):
			return key in self.data
		elif isinstance(key, int):
			return key in self.flat

		raise InvalidInventoryKey(f"type: {type(key)}")

	def __iter__(self) -> InventoryIterator:
		return InventoryIterator(iter(self.data))

	def add(self, key: str, item: HasName) -> int:
		"""Add an item to both dictionaries"""

		# it is the same object in both dictionaries
		if key in self.data:
			self.data[key][0] += item
			return self.data[key][1]
		else:
			return self.insert(key, item)

	def insert(self, key: str, item: HasName) -> int:
		"""Insert an new item to both dictionaries"""

		index: int = 0
		for index in range(len(self.flat) + 1):
			if index not in self.flat:
				self.flat[index] = item
				break
		self.data[key] = ItemAndIndex(item, index)
		if index > INV_WIDTH * INV_HEIGHT * self.pages:
			self.pages += 1
		return index

	def sub(self, key: str | int, amount: int) -> int:
		"""Remove a certain amount of an item from the inventory and remove
		it from both dictionaries if appropriate"""

		count: int = 0
		if isinstance(key, str):
			self.data[key][0] -= amount

			count = self.data[key][0].amount
			if count <= 0 and key != "gold":
				index = self.data[key][1]
				del self.data[key]
				del self.flat[index]
		elif isinstance(key, int):
			self.flat[key] -= amount

			count = self.flat[key].amount
			if count <= 0 and key != "gold":
				name = self.flat[key].name
				del self.flat[key]
				del self.data[name]
		else:
			raise InvalidInventoryKey(f"type: {type(key)}")

		return count


# END

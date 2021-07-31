"""Exceptions for Crawler"""

__all__ = [
	"CrawlerError",
	"ItemNotFoundError",
	"NotEquippedError",
	"EquipmentFullError",
	"UseItemWithZeroError",
	"InvalidInventoryKey"
]


class CrawlerError(Exception):
	"""Base Exception for Crawler"""


class ItemNotFoundError(KeyError, CrawlerError):
	"""An item was not found when in an inventory when it should have been."""


class NotEquippedError(ValueError, CrawlerError):
	"""Equipment that was not equipped was unequipped"""


class EquipmentFullError(ValueError, CrawlerError):
	"""Equipment that was equipped in a slot that was already full"""


class UseItemWithZeroError(ValueError, CrawlerError):
	"""Attempted to use an item that the player had zero of"""


class InvalidInventoryKey(TypeError, CrawlerError):
	"""Use a invalid type for indexing the inventory object"""


__all__ = [
	"CrawlerError",
    "ItemNotFoundError",
    "NotEquipedError",
    "EquipmentFullError",
    "UseItemWithZeroError"
]

class CrawlerError(Exception):
    """Base Exception for Crawler"""

class ItemNotFoundError(KeyError, CrawlerError):
	"""An item was not found when in an inventory when it should have been."""

class NotEquipedError(ValueError, CrawlerError):
	"""Equipment that was not equiped was unequiped"""

class EquipmentFullError(ValueError, CrawlerError):
	"""Equipment that was equiped in a slot that was already full"""

class UseItemWithZeroError(ValueError, CrawlerError):
	"""Attemped to use an item that the player had zero of"""
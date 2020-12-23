
__all__ = [
    "ItemNotFoundError",
    "NotEquipedError",
    "EquipmentFullError",
    "UseItemWithZeroError"
]

class SwitchError(Exception):
    """Base Exception for Switch"""

class ItemNotFoundError(KeyError, SwitchError):
	"""An item was not found when in an inventory when it should have been."""

class NotEquipedError(ValueError, SwitchError):
	"""Equipment that was not equiped was unequiped"""

class EquipmentFullError(ValueError, SwitchError):
	"""Equipment that was equiped in a slot that was already full"""

class UseItemWithZeroError(ValueError, SwitchError):
	"""Attemped to use an item that the player had zero of"""
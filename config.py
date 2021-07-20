
"""Configuration file for constants"""

__all__ = [
	"ENEMIES",
	"DUN_W",
	"DUN_H",
	"W",
	"H",
	"SMW",
	"SMH",
	"INV_WIDTH",
	"INV_HEIGHT",
	"IBW",
	"IBH",
	"COST_MUL",
	"STARTING_GOLD",
	"DISTANCE_DIFF",
	"DEFAULT_MAX_HEALTH",
	"DEFAULT_DAMAGE",
	"DEFAULT_DEFENCE",
	"HEAL_POT_VAL",
	"SLIME_HEART_VAL",
	"DRIDER_CUTOFF",
	"SLIME_CUTOFF",
	"GOB_CUTOFF",
	"NON_VIOLENT_ENC_CUTOFF",
	"STARTING_ROOM_TYPE",
	"DOWN_STAIRS_TYPE",
	"UP_STAIRS_TYPE"
]

# whether enemies spawn or not
ENEMIES = True
# number of rooms wide
DUN_W = 3
DUN_H = 3
# width of map screen in pixels
W = 300
H = 300
# width of a room in pixels
SMW = W // DUN_W
SMH = H // DUN_H

INV_WIDTH = 5
INV_HEIGHT = 5

IBW = W // INV_WIDTH
IBH = H // INV_HEIGHT

COST_MUL = 1
STARTING_GOLD = 300
# the amount that distance from the center makes enemies stronger
DISTANCE_DIFF = 70
DEFAULT_MAX_HEALTH = 100
DEFAULT_DAMAGE = 10
DEFAULT_DEFENCE = 0
# the amount of a health potion heals
HEAL_POT_VAL = 50
# the amount of health a slime heart gives
SLIME_HEART_VAL = 5
# minimum difficulty of a drider
DRIDER_CUTOFF = 1700
# minimum difficulty of a slime
SLIME_CUTOFF = 1000
# minimum difficulty of a goblin
GOB_CUTOFF = 100
NON_VIOLENT_ENC_CUTOFF = 1
STARTING_ROOM_TYPE = 0
DOWN_STAIRS_TYPE = -1
UP_STAIRS_TYPE = -2

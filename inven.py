from config import *

__all__ = ["Inventory"]


class Inventory_Iterator(object):
	def __init__(self, d_iter):
		self.d = d_iter
	
	def __iter__(self):
		return self
	
	def __next__(self):
		return next(self.d)[0]


class Inventory(object):
	def __init__(self):
		
		# every item is stored under its name as: [item, index] in data
		# and under index as: item in flat
		self.data = {}
		self.flat = {}
		self.pages  = 1
	
	def __getattr__(self, attr):
		return getattr(self.data, attr)

	def __getitem__(self, key):
		if isinstance(key, str):
			return self.data[key][0]
		elif isinstance(key, int):
			return self.data[key]

	def __setitem__(self, key, item):
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
			

	def __delitem__(self, key):
		if isinstance(key, str):
			num = self.data[key][1]
			del self.data[key]
			del self.flat[num]
		elif isinstance(key, int):
			name = self.flat[key].name
			del self.flat[key]
			del self.data[name]

	def __len__(self):
		return len(self.data)

	def __contains__(self, key):
		if isinstance(key, str):
			return key in self.data
		elif isinstance(key, int):
			return key in self.flat

	def __iter__(self):
		return Inventory_Iterator(iter(self.data))
	
	def add(self, key, item) -> int:
		
		# it is the same object in both dictoraries
		if key in self.data:
			self.data[key][0] += item
		else:
			return self.insert(key, item)
	
	def insert(self, key, item):
		assert isinstance(key, str)
		
		index = 0
		for index in range(len(self.flat)):
			if index not in self.flat:
				self.flat[index] = item
				break
		self.data[key] = [item, index]
		if index > INV_WIDTH * INV_HEIGHT * self.pages:
			self.pages += 1
		return index
	
	
			






	



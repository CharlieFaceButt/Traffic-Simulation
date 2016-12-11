import Tkinter
import math

class TrafficAgent(object):
	def __init__(self, width, length, mess):
		super(TSObject, self).__init__()
		self.w = width
		self.l = length
		# Velocity
		self.v = 0
		# Acceleration
		self.a = 0
		# Mess
		self.m = mess
		

class TACar(TrafficAgent):
	# 2 meters
	__default_width = 2
	# 3 meters
	__default_length = 3
	# 1 ton
	__default_mess = 1

	def __init__(self, width = __default_width, length = __default_length, mess = __default_mess):
		super(TSCar, self).__init__(width, length, mess)
		
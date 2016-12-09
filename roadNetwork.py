import Tkinter
import math

class RNGate:

	def __init__(self, loc_x, loc_y, loc_z, width, direction):
		self.x = loc_x
		self.y = loc_y
		self.z = loc_z
		self.width = width
		self.direction = direction

	def __str__(self):
		s = "Gate " + str(id(self)) + " at (" + str(self.x) + "," + str(self.y) + "," + str(self.z) + ") with width " + str(self.width)
		return s

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return (self.x == other.x and self.y == other.y and self.z == other.z and self.width == other.width and self.direction == other.direction)
		return NotImplemented

	def __ne__(self, other):
		if isinstance(other, self.__class__):
			return not self.__eq__(other)
		return NotImplemented

# Basic super class for all road elements, all road elements 
# has location features and size features and entry and exit
class RNElement(object):

	def __init__(self, loc_x, loc_y, loc_z, width, length):
		self.x = loc_x
		self.y = loc_y
		self.z = loc_z
		self.w = width
		self.l = length

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return (self.x == other.x and self.y == other.y and self.z == other.z and self.w == other.w and self.l == other.l)
		return NotImplemented

	def __ne__(self, other):
		if isinstance(other, self.__class__):
			return not self.__eq__(other)
		return NotImplemented

# Road tile is the basic element of lanes, 
# and usually only one car is allowed to pass through
class RNRoadTile(RNElement):

	def __str__(self):
		s = "Tile " + str(id(self)) + " at (" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ")" 
		return s

	def __init__(self, loc_x, loc_y, loc_z, width, length, slope, direction):
		super(RNRoadTile, self).__init__(loc_x, loc_y, loc_z, width, length)
		self.slope = slope
		self.direction = direction

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return (super(RNRoadTile, self).__eq__(other) and self.slope == other.slope and self.direction == other.direction)
		return NotImplemented

	def __ne__(self, other):
		if isinstance(other, self.__class__):
			return not self.__eq__(other)
		return NotImplemented

	def get_entry(self):
		return RNGate(self.x - self.l * math.cos(self.direction) / 2, self.y - self.l * math.sin(self.direction) / 2, self.z - self.l * self.slope / 2, self.w, self.direction)
		
	def get_exit(self):
		return RNGate(self.x + self.l * math.cos(self.direction) / 2, self.y + self.l * math.sin(self.direction) / 2, self.z + self.l * self.slope / 2, self.w, self.direction)

	# Determine if two road tile is fully connected
	@staticmethod
	def is_connected(tile_ahead, tile_after):
		aheadExit = tile_ahead.get_exit()
		afterEntry = tile_after.get_entry()
		return aheadExit == afterEntry

	@staticmethod
	def is_combinable(tile_first, tile_next):
		if tile_first.z != tile_next.z or tile_first.direction != tile_next.direction or tile_first.slope != tile_next.slope:
			return False
		sw = tile_next.w + tile_first.w
		dx = abs(tile_next.x - tile_first.x)
		dy = abs(tile_next.y - tile_first.y)
		direction = tile_first.direction
		if abs(dx - abs(sw * math.sin(direction)) / 2) > 0.01 * dx or abs(dy - abs(sw * math.cos(direction)) / 2) > 0.01 * dy:
			return False
		return True

		
# Lanes are sets of road tiles. Combine lanes to form roads
class RNLane(RNElement):
	
	def __str__(self):
		s = "Lane " + str(id(self)) + ":\n\tlength: " + str(self.l) + "\n\tstart: " + str(self.get_entry()) + "\n\tend: " + str(self.get_exit())
		return s

	def __init__(self, road_tiles):
		N = len(road_tiles)
		# Lane can be constructed only if the tiles can form a lane
		if N > 0 and RNLane.is_consistent(road_tiles):
			# The middle tile as the location center for the lane
			middleTileIdx = 0
			# Make sure the middle tile covers the middle point of lane
			# based on length
			middleLength = 0
			# Sum of tile length as the length of lane
			totalLength = 0
			# Average of width as the width of lane
			sumWidth = 0
			# Calculate attributes above
			for tile in road_tiles:
				totalLength = totalLength + tile.l
				sumWidth = sumWidth + tile.l * tile.w
				if totalLength/2 > middleLength:
					middleLength = middleLength + road_tiles[middleTileIdx].l
					middleTileIdx = middleTileIdx + 1
			middleTile = road_tiles[middleTileIdx - 1]
			# Using the super constructor
			super(RNLane, self).__init__(middleTile.x, middleTile.y, middleTile.z, sumWidth/totalLength, totalLength)
			# Remember the collection of tiles
			self.tiles = road_tiles
		else:
			raise Exception("RNLane", "unable to construct inconsistent road_tiles")

	# Determine if a list of tiles can form a lane
	@staticmethod
	def is_consistent(tileList):
		for idx in xrange(1,len(tileList)):
			if not RNRoadTile.is_connected(tileList[idx-1], tileList[idx]):
				return False
		return True

	# Entry of the lane is the entry of its first tile
	def get_entry(self):
		return self.tiles[0].get_entry()
	
	# Exit of the lane is the exit of its last tile
	def get_exit(self):
		return self.tiles[-1].get_exit()


# Road representation, consists of parallel lanes, these lanes
# must be going from the same place to the same end and must be 
# attached with some other lanes in the road.
class RNRoad(RNElement):

	def __init__(self, road_lanes):
		M = len(road_lanes)
		if M > 0 and RNRoad.is_combinable(road_lanes):
			middle_x = 0
			middle_y = 0
			middle_z = 0
			totalWidth = 0
			for lane in road_lanes:
				middle_x = middle_x + lane.x
				middle_y = middle_y + lane.y
				middle_z = middle_z + lane.z
				totalWidth = totalWidth + lane.w
			middle_x = middle_x / len(road_lanes)
			middle_y = middle_y / len(road_lanes)
			middle_z = middle_z / len(road_lanes)
				
			super(RNRoad, self).__init__(middle_x, middle_y, middle_z, totalWidth, road_lanes[0].l)
			self.lanes = road_lanes
		else:
			raise Exception("RNRoad", "lanes are not combinable.")

	def __str__(self):
		return "Road " + str(id(self)) + "\n\tLength: " + str(self.l) + "\n\tNumber of lanes: " + str(len(self.lanes)) + "\n\tStarts at: " + str(self.get_entry()) + "\n\tEnds at: " + str(self.get_exit())

	# Determine whether a set of lanes can combined as a road
	@staticmethod
	def is_combinable(lanes):
		if len(lanes) < 2:
			return True
		N = len(lanes[0].tiles)
		for i in xrange(1,len(lanes)):
			if len(lanes[i].tiles) != N:
				return False
		currentLaneIdx = 0
		while currentLaneIdx < len(lanes) - 1:
			lane = lanes[currentLaneIdx]
			nextLane = lanes[currentLaneIdx + 1]
			for j in xrange(0, N):
				if not RNRoadTile.is_combinable(lane.tiles[j], nextLane.tiles[j]):
					return False
			currentLaneIdx = currentLaneIdx + 1
		return True

	def get_entries(self):
		entryList = list()
		for lane in self.lanes:
			entryList.append(lane.get_entry())
		return entryList

	def get_exits(self):
		entryList = list()
		for lane in self.lanes:
			entryList.append(lane.get_exit())
		return entryList
		
	def get_entry(self):
		entry = RNGate(0,0,0,0,0)
		for lane_entry in self.get_entries():
			entry.x = entry.x + lane_entry.x
			entry.y = entry.y + lane_entry.y
			entry.z = entry.z + lane_entry.z
			entry.width = entry.width + lane_entry.width
			entry.direction = entry.direction + lane_entry.direction
		entry.x = entry.x / len(self.lanes)
		entry.y = entry.y / len(self.lanes)
		entry.z = entry.z / len(self.lanes)
		entry.direction = entry.direction / len(self.lanes)
		return entry

	def get_exit(self):
		exit = RNGate(0,0,0,0,0)
		for lane_exit in self.get_exits():
			exit.x = exit.x + lane_exit.x
			exit.y = exit.y + lane_exit.y
			exit.z = exit.z + lane_exit.z
			exit.width = exit.width + lane_exit.width
			exit.direction = exit.direction + lane_exit.direction
		exit.x = exit.x / len(self.lanes)
		exit.y = exit.y / len(self.lanes)
		exit.z = exit.z / len(self.lanes)
		exit.direction = exit.direction / len(self.lanes)
		return exit

class RNIntersection(RNElement):

	def __init__(self, incoming_roads, outgoing_roads):
		self.entries = list()
		loc_x = 0
		loc_y = 0
		loc_z = 0
		totalWidth = 0
		for road in incoming_roads:
			loc_x = loc_x + road.x
			loc_y = loc_y + road.y
			loc_z = loc_z + road.z
			totalWidth = totalWidth + road.get_entry().w
			self.entries.append(road.get_exits())
		self.exits = list()
		for road in outgoing_roads:
			loc_x = loc_x + road.x
			loc_y = loc_y + road.y
			loc_z = loc_z + road.z
			totalWidth = totalWidth + road.get_entry().w
			self.exits.append(road.get_entries())
		super(intersection, self).__init__(loc_x, loc_y, loc_z, totalWidth, 0)

	def __str__(self):
		return "Intersection " + str(id(self)) + " at (" + str(self.x) + "," + str(self.y) + "," + str(self.z) + ") connecting " + str()

# class RNCross(RNIntersection):

# 	def __init__(self, incoming_roads, outgoing_roads):
# 		super(RNCross, self).__init__()
# 		self.arg = arg

# class RNFork(RNGate):

# 	def __init__(self, incoming_road, outgoing_roads):
# 		super(ClassName, self).__init__()
# 		self.arg = arg
		
# class RNMerge(RNGate):

# 	def __init__(self, incoming_roads, outgoing_road):
# 		super(RNMerge, self).__init__()
# 		self.arg = arg
		
def test_road():
	print "test1"

	t1 = RNRoadTile(0, 0, 0, 4, 10, 0, 0)
	t2 = RNRoadTile(10, 0, 0, 4, 10, 0, 0)
	t3 = RNRoadTile(20, 0, 0, 4, 10, 0, 0)
	l1 = RNLane([t1,t2,t3])

	t4 = RNRoadTile(0, 4, 0, 4, 10, 0, 0)
	t5 = RNRoadTile(10, 4, 0, 4, 10, 0, 0)
	t6 = RNRoadTile(20, 4, 0, 4, 10, 0, 0)
	l2 = RNLane([t4,t5,t6])

	r1 = RNRoad([l1,l2])
	print r1

	t21 = RNRoadTile(40, 0, 0, 4, 10, 0, 0)
	t22 = RNRoadTile(50, 0, 0, 4, 10, 0, 0)
	t23 = RNRoadTile(60, 0, 0, 4, 10, 0, 0)
	l21 = RNLane([t21,t22,t23])

	t24 = RNRoadTile(40, 4, 0, 4, 10, 0, 0)
	t25 = RNRoadTile(50, 4, 0, 4, 10, 0, 0)
	t26 = RNRoadTile(60, 4, 0, 4, 10, 0, 0)
	l22 = RNLane([t24,t25,t26])

	r2 = RNRoad([l21,l22])
	print r2

	t21 = RNRoadTile(40, 0, 0, 4, 10, 0, 0)
	t22 = RNRoadTile(50, 0, 0, 4, 10, 0, 0)
	t23 = RNRoadTile(60, 0, 0, 4, 10, 0, 0)
	l21 = RNLane([t21,t22,t23])

	t24 = RNRoadTile(40, 4, 0, 4, 10, 0, 0)
	t25 = RNRoadTile(50, 4, 0, 4, 10, 0, 0)
	t26 = RNRoadTile(60, 4, 0, 4, 10, 0, 0)
	l22 = RNLane([t24,t25,t26])

	r2 = RNRoad([l21,l22])
	print r2

test_road()
import Tkinter
import math
from random import *

class RNLocation(object):

	def __init__(self, loc_x, loc_y, loc_z):
		self.x = loc_x
		self.y = loc_y
		self.z = loc_z

	def distance_to(self, loc):
		return math.sqrt(math.pow((self.x - loc.x),2) + math.pow((self.y - loc.y),2) + math.pow((self.z - loc.z),2))
		

class RNGate(RNLocation):

	def __init__(self, loc_x, loc_y, loc_z, width, direction):
		super(RNGate, self).__init__(loc_x, loc_y, loc_z)
		self.width = width
		if direction > math.pi:
			direction = direction - 2 * pi
		if direction < - math.pi:
			direction = direction + 2 * pi
		self.direction = direction

	def __str__(self):
		s = "Gate " + str(id(self)) + " at (" + str(self.x) + "," + str(self.y) + "," + str(self.z) + ") with width " + str(self.width)
		return s

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return (abs(self.x - other.x) < 0.1 and \
				abs(self.y == other.y) < 0.1 and \
				abs(self.z == other.z) < 0.1 and \
				self.width == other.width and \
				self.direction == other.direction)
		return NotImplemented

	def __ne__(self, other):
		if isinstance(other, self.__class__):
			return not self.__eq__(other)
		return NotImplemented

	@staticmethod
	def combine_gate(gateSet):
		entry = RNGate(0,0,0,0,0)
		for lane_entry in gateSet:
			entry.x = entry.x + lane_entry.x
			entry.y = entry.y + lane_entry.y
			entry.z = entry.z + lane_entry.z
			entry.width = entry.width + lane_entry.width
			entry.direction = entry.direction + lane_entry.direction
		N = len(gateSet)
		entry.x = entry.x / N
		entry.y = entry.y / N
		entry.z = entry.z / N
		entry.direction = entry.direction / N
		return entry

	def can_intersect(self, gate):
		maxWidth = max(self.width, gate.width)
		if self.distance_to(gate) < maxWidth * 2:
			return True
		else:
			return False

	def get_left(self):
		return self.x - abs(self.width * math.cos(self.direction - math.pi/2))

	def get_right(self):
		return self.x + abs(self.width * math.cos(self.direction - math.pi/2))
	
	def get_top(self):
		return self.y + abs(self.width * math.sin(self.direction - math.pi/2))
	
	def get_bottom(self):
		return self.y - abs(self.width * math.sin(self.direction - math.pi/2))


# Basic super class for all road elements, all road elements 
# has location features and size features and entry and exit
class RNElement(RNLocation):

	def __init__(self, loc_x, loc_y, loc_z, width, length):
		super(RNElement, self).__init__(loc_x, loc_y, loc_z)
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
		if direction > math.pi:
			direction = direction - 2 * pi
		if direction < - math.pi:
			direction = direction + 2 * pi
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
			print "Not combinable tile because of z/direction/slope: " + str(tile_first.z) + "/" + str(tile_first.direction) + "/" + str(tile_first.slope) + " != " + str(tile_first.z) + "/" + str(tile_first.direction) + "/" + str(tile_first.slope)
			return False
		sw = tile_next.w + tile_first.w
		dx = abs(tile_next.x - tile_first.x)
		dy = abs(tile_next.y - tile_first.y)
		direction = tile_first.direction
		if abs(dx - abs(sw * math.sin(direction)) / 2) > 0.01 * (dx + 1) or abs(dy - abs(sw * math.cos(direction)) / 2) > 0.01 * (dy + 1):
			print str(tile_first)
			print str(tile_next)
			print "sw: " + str(sw)
			print "direction: " + str(direction)
			print "dx : dxsw = " + str(dx) + " : " + str(sw * math.sin(direction))
			print "dy : dysw = " + str(dy) + " : " + str(sw * math.cos(direction))
			print "Not combinable tile because edge not close"
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
				print "Not consistent: " + str(tileList[idx - 1]) + " and " + str(tileList[idx])
				print str(tileList[idx - 1].get_exit()) + " to " + str(tileList[idx].get_entry())
				return False
		return True

	@staticmethod
	def is_combinable(lanes):
		if len(lanes) < 2:
			return True
		N = len(lanes[0].tiles)
		for i in xrange(1,len(lanes)):
			if len(lanes[i].tiles) != N:
				"Not combinable lane because different length"
				return False
		currentLaneIdx = 0
		while currentLaneIdx < len(lanes) - 1:
			lane = lanes[currentLaneIdx]
			nextLane = lanes[currentLaneIdx + 1]
			for j in xrange(0, N):
				if not RNRoadTile.is_combinable(lane.tiles[j], nextLane.tiles[j]):
					print "Not combinable lane tile (" + str(lane.tiles[j]) + ", " + str(nextLane.tiles[j])
					return False
			currentLaneIdx = currentLaneIdx + 1
		return True

	# Entry of the lane is the entry of its first tile
	def get_entry(self):
		return self.tiles[0].get_entry()
	
	# Exit of the lane is the exit of its last tile
	def get_exit(self):
		return self.tiles[-1].get_exit()

	def get_preenter_location(self, position):
		if position < 0 or position > self.l:
			return None

		length = position
		for tile in self.tiles:
			if length <= tile.l:
				gate = tile.get_entry()
				# Parellel position but outside the lane
				x = gate.x + length * math.cos(tile.direction) + tile.w * math.cos(tile.direction - math.pi/2)
				y = gate.y + length * math.sin(tile.direction) + tile.w * math.sin(tile.direction - math.pi/2)
				z = gate.z + length * tile.slope
				return RNLocation(x, y, z)
			else:
				length = length - tile.l

		return None

	def get_location(self, position):
		if position < 0 or position > self.l:
			return None

		length = position
		for tile in self.tiles:
			if length <= tile.l:
				gate = tile.get_entry()
				# Parellel position but outside the lane
				x = gate.x + length * math.cos(tile.direction)
				y = gate.y + length * math.sin(tile.direction)
				z = gate.z + length * tile.slope
				return RNLocation(x, y, z)
			else:
				length = length - tile.l

		return None


# Road representation, consists of parallel lanes, these lanes
# must be going from the same place to the same end and must be 
# attached with some other lanes in the road.
class RNRoad(RNElement):

	def __init__(self, road_lanes):
		M = len(road_lanes)
		if M > 0 and RNLane.is_combinable(road_lanes):
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
			print "Road created"
		else:
			print "M:" + str(M)
			raise Exception("RNRoad", "lanes are not combinable.")

	def __str__(self):
		return "Road " + str(id(self)) + "\n\tLength: " + str(self.l) + "\n\tNumber of lanes: " + str(len(self.lanes)) + "\n\tStarts at: " + str(self.get_entry()) + "\n\tEnds at: " + str(self.get_exit())

	# Determine whether a set of lanes can combined as a road

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
		return RNGate.combine_gate(self.get_entries())

	def get_exit(self):
		return RNGate.combine_gate(self.get_exits())

	def get_geo(self):
		return [self.x, -self.y, self.z, self.w, self.l]

class RNIntersection(RNElement):

	def __init__(self, incoming_roads, outgoing_roads):
		print "Create intersection"
		self.entries = list()
		self.exits = list()
		for road in incoming_roads:
			self.entries.append(road.get_exits())
		for road in outgoing_roads:
			self.exits.append(road.get_entries())
		self.updateGeo()

	def __str__(self):
		return "Intersection " + str(id(self)) + " at (" + str(self.x) + "," + str(self.y) + "," + str(self.z) + \
			") size (" + str(self.w) + "," + str(self.l) + ") connecting "\
			+ str(len(self.entries)) + " entries and " + str(len(self.exits)) + " exits"

	def updateGeo(self):
		print "Update intersection geography"
		loc_x = 0
		loc_y = 0
		loc_z = 0
		totalWidth = 0
		left = float('inf')
		right = float('-inf')
		top = float('-inf')
		bottom = float('inf')
		for gates in self.entries + self.exits:

			entry = RNGate.combine_gate(gates)

			loc_x = loc_x + entry.x
			loc_y = loc_y + entry.y
			loc_z = loc_z + entry.z
			totalWidth = totalWidth + entry.width

			left = min(left, entry.get_left())
			right = max(right, entry.get_right())
			top = max(top, entry.get_top())
			bottom = min(bottom, entry.get_bottom())
			# print "[left: " + str(left) + ", right: " + str(right) + ", top: " + str(top) + ", bottom: " + str(bottom) + "]"

		N = len(self.entries) + len(self.exits)
		loc_x = loc_x / N
		loc_y = loc_y / N
		loc_z = loc_z / N
		totalWidth = totalWidth / N
		super(RNIntersection, self).__init__(loc_x, loc_y, loc_z, right - left, top - bottom)

	def get_area(self):
		return self.w * self.l

	@staticmethod
	def generate_intersection(incomming_roads, outgoing_roads):
		print "Generate intersection:"
		sect = RNIntersection(incomming_roads, outgoing_roads)
		# Valid area
		mWidth = 0
		for gateSet in sect.entries + sect.exits:
			gate = RNGate.combine_gate(gateSet)
			mWidth = max(mWidth, gate.width)
		
		if sect.get_area() > mWidth * mWidth * 2:
			print "Cannot generate intersection, roads are too far away"
			print "\tArea: " + str(sect.get_area())
			print "\tWidth: " + str(mWidth)
			return None
		else:
			print str(sect)
			return sect

	def can_attach(self, gate):
		if self.distance_to(gate) < max(self.w, self.l) * 2:
			return True
		else:
			return False

	# Attach a road with one side of the road
	def attach_new_road(self, road, side):
		gates = None
		if side == "exit":
			if self.distance_to(road.get_exit()) > self.w * 2:
				return False
			gates = road.get_exits()
			self.entries.append(gates)
			print "Road exit attached to intersection"
		elif side == "entry":
			if self.distance_to(road.get_entry()) > self.w * 2:
				return False
			gates = road.get_entries()
			self.exits.append(gates)
			print "Road entry attached to intersection"
		else:
			print "Attach road side: " + side
			return False
		
		self.updateGeo()

			
class RoadNetwork(object):
	
	def __init__(self):
		print "Create road network"
		self.roads = list()
		self.intersections = list()
		self.forks = list()
		self.merges = list()
		# Records the next possible elements
		self.map = dict()
		# Records the previous possible elements
		self.reverseMap = dict()

	def link(self, previous, next):
		if isinstance(previous, RNLocation) and isinstance(next, RNLocation):
			nList = None
			print "Add map record"
			if self.map.has_key(previous):
				nList = self.map[previous]
				print "\tHas record: " + str(previous)
			else:
				nList = list()
				print "\tCreate new record"
			nList.append(next)
			self.map[previous] = nList

			print "Add reverseMap record"
			pList = None
			if self.reverseMap.has_key(next):
				pList = self.reverseMap[next]
				print "\tHas record: " + str(next) + ", " + str(pList)
			else:
				print "\tCreate new record"
				pList = list()
			pList.append(previous)
			self.reverseMap[next] = pList

	@staticmethod
	def generate_road(start_x, start_y, start_z, end_x, end_y, end_z, total_width, tile_length = None, n_lanes = 1):
		if n_lanes <= 0:
			n_lanes = 1

		sLoc = RNLocation(start_x, start_y, start_z)
		eLoc = RNLocation(end_x, end_y, end_z)
		# The road length
		roadLength = sLoc.distance_to(eLoc)
		# The road direction
		roadDirection = math.acos((end_x - start_x) / roadLength)
		if end_y - start_y < 0:
			roadDirection = - roadDirection
		# The road slope
		roadSlope = (end_z - start_z) / roadLength
		# Length of each tile and number of tiles
		tileLength = tile_length
		if tile_length == None:
			tileLength = roadLength
		n_tiles = int(math.ceil(roadLength / tileLength))
		# Width of each tile
		tileWidth = total_width / n_lanes
		# Create road
		lanes = list()
		for lIndex in xrange(0,n_lanes):
			# Create lane
			tiles = list()
			wfraction = float(1 + 2 * lIndex - n_lanes) / (2 * n_lanes)
			# print "Number of lanes: " + str(n_lanes)
			# print "Fraction: " + str(wfraction)
			offset_x = total_width * wfraction * math.cos(roadDirection - math.pi / 2)
			# print "Offset x: " + str(offset_x)
			offset_y = total_width * wfraction * math.sin(roadDirection - math.pi / 2)
			# print "Offset y: " + str(offset_y)
			for tIndex in xrange(0,n_tiles):
				# Create tile
				fraction = (tIndex + 0.5) / n_tiles
				tX = start_x + (end_x - start_x) * fraction + offset_x
				tY = start_y + (end_y - start_y) * fraction + offset_y
				tZ = start_z + (end_z - start_z) * fraction
				tiles.append(RNRoadTile(tX, tY, tZ, tileWidth, tileLength, roadSlope, roadDirection))
			# Connect tiles to lane
			newLane = RNLane(tiles)
			print "New lane: " + str(newLane)
			lanes.append(newLane)
		# Combine lanes to raod
		print "Road generated"
		return RNRoad(lanes)

	# Find and attach intersection with road
	def attach_road_with_closest_intersection(self, road, side):
		print "Finding closest intersection to attach to " + str(road)
		exitIntersection = None
		entryIntersection = None
		found = None
		if side == "exit":
			exitGate = road.get_exit()
			exitIntersection = self.find_intersection(exitGate)
			if exitIntersection != None:
				print "\n\tAttach on road exit: " + str(exitIntersection)
				self.link(road, exitIntersection)
				exitIntersection.attach_new_road(road, "exit")
				found = exitIntersection
		if side == "entry":
			entryGate = road.get_entry()
			entryIntersection = self.find_intersection(entryGate)
			if entryIntersection != None:
				print "\n\tAttach on road entry: " + str(entryIntersection)
				self.link(entryIntersection, road)
				entryIntersection.attach_new_road(road, "entry")
				found = entryIntersection

		if exitIntersection == None and entryIntersection == None:
			print "\n\tNo intersection found to attach"

		return found

	def attach_road_with_closest_road(self, road, road_side):
		print "Find closest road to attach to " + str(road)
		newIntersection = None
		if road_side == "exit":
			(exitRoad, side) = self.find_road(road.get_exit())
			if exitRoad != None:
				print "\n\tAttach on road exit: " + str(exitRoad)
				if side == "exit":
					newIntersection = RNIntersection([exitRoad, road],[])
					self.link(road, newIntersection)
					self.link(exitRoad, newIntersection)
					self.intersections.append(newIntersection)
				elif side == "entry":
					newIntersection = RNIntersection([road], [exitRoad])
					self.link(road, newIntersection)
					self.link(newIntersection, exitRoad)
					self.intersections.append(newIntersection)
		if road_side == "entry":
			(entryRoad, side) = self.find_road(road.get_entry())
			if entryRoad != None:
				print "\n\tAttach on road entry: " + str(entryRoad)
				if side == "exit":
					newIntersection = RNIntersection([entryRoad],[road])
					self.link(newIntersection, road)
					self.link(entryRoad, newIntersection)
					self.intersections.append(newIntersection)
				elif side == "entry":
					newIntersection = RNIntersection([], [road, entryRoad])
					self.link(newIntersection, road)
					self.link(newIntersection, entryRoad)
					self.intersections.append(newIntersection)

		if newIntersection == None:
			print "\n\tNo road to attach."
			return None
		else:
			print "Intersection attached: " + str(newIntersection)
			return newIntersection

	# Find the road on map that can intersect with the given gate
	def find_road(self, newGate):
		for road in self.roads:
			if road.get_entry().can_intersect(newGate):
				return (road, "entry")
			elif road.get_exit().can_intersect(newGate):
				return (road, "exit")
		return (None, None)

	# Find the intersection that can attach the given gate
	def find_intersection(self, newGate):
		for intersection in self.intersections:
			if intersection.can_attach(newGate):
				print "Intersection found"
				return intersection
		return None
	
	def do_add_road(self, \
		start_x, start_y, start_z, \
		end_x, end_y, end_z, \
		lane_width, tile_length, n_lanes, connect = True):
		# Create the road
		newRoad = RoadNetwork.generate_road(\
			start_x, start_y, start_z, end_x, end_y, end_z, \
			lane_width * n_lanes, tile_length, n_lanes)
		# Connect new road with other elements
		newIntersections = list()
		oldIntersections = list()
		if connect:
			# Connect intersection at exit
			print "Connect road exit"
			oldInterSect = self.attach_road_with_closest_intersection(newRoad, "exit")
			# Connect roads if no intersection connected to road exit
			if oldInterSect == None:
				newIntersection = self.attach_road_with_closest_road(newRoad, "exit")
				if newIntersection != None:
					newIntersections.append(newIntersection)
			else:
				oldIntersections.append(oldInterSect)
			# Do the same thing for road entry
			print "Connect road entry"
			oldInterSect = self.attach_road_with_closest_intersection(newRoad, "entry")
			if oldInterSect == None:
				newIntersection = self.attach_road_with_closest_road(newRoad, "entry")
				if newIntersection != None:
					newIntersections.append(newIntersection)
			else:
				oldIntersections.append(oldInterSect)
		# Remember the road
		self.roads.append(newRoad)
		return (newRoad, newIntersections, oldIntersections)

	def random_position_on_road(self, road = None):
		if road == None:
			road = self.roads[randint(0, len(self.roads) - 1)]
		lane = road.lanes[-1]
		position = random() * lane.l
		return (road, lane, position)



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
	print "Road 1: " + str(r1)

	t21 = RNRoadTile(40, 0, 0, 4, 10, 0, 0)
	t22 = RNRoadTile(50, 0, 0, 4, 10, 0, 0)
	t23 = RNRoadTile(60, 0, 0, 4, 10, 0, 0)
	l21 = RNLane([t21,t22,t23])

	t24 = RNRoadTile(40, 4, 0, 4, 10, 0, 0)
	t25 = RNRoadTile(50, 4, 0, 4, 10, 0, 0)
	t26 = RNRoadTile(60, 4, 0, 4, 10, 0, 0)
	l22 = RNLane([t24,t25,t26])

	r2 = RNRoad([l21,l22])
	print "Road 2: " + str(r2)

	upDirection = math.pi/2
	t31 = RNRoadTile(28, -27, 0, 4, 10, 0, upDirection)
	t32 = RNRoadTile(28, -17, 0, 4, 10, 0, upDirection)
	t33 = RNRoadTile(28, -7, 0, 4, 10, 0, upDirection)
	l31 = RNLane([t31,t32,t33])

	t34 = RNRoadTile(32, -27, 0, 4, 10, 0, upDirection)
	t35 = RNRoadTile(32, -17, 0, 4, 10, 0, upDirection)
	t36 = RNRoadTile(32, -7, 0, 4, 10, 0, upDirection)
	l32 = RNLane([t34,t35,t36])

	r3 = RNRoad([l31,l32])
	print "Road 3: " + str(r3)

	upDirection = math.pi/2
	t41 = RNRoadTile(28, 11, 0, 4, 10, 0, upDirection)
	t42 = RNRoadTile(28, 21, 0, 4, 10, 0, upDirection)
	t43 = RNRoadTile(28, 31, 0, 4, 10, 0, upDirection)
	l41 = RNLane([t41,t42,t43])

	t44 = RNRoadTile(32, 11, 0, 4, 10, 0, upDirection)
	t45 = RNRoadTile(32, 21, 0, 4, 10, 0, upDirection)
	t46 = RNRoadTile(32, 31, 0, 4, 10, 0, upDirection)
	l42 = RNLane([t44,t45,t46])

	r4 = RNRoad([l41,l42])
	print "Road 4: " + str(r4)

	IntSect = RNIntersection.generate_intersection([r1,r3],[r2,r4])
	print IntSect

	rn = RoadNetwork()

# test_road()
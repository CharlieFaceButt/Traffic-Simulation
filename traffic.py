import Tkinter
import math
from roadNetwork import *
from random import *
		

class CarAgent(RNLocation):

	# 2 meters
	default_width = 2.0
	# 3 meters
	default_length = 3.0
	# 1 ton
	default_mess = 1.0
	# 50 meters
	default_entering_distance = 10.0
	# The power of acceleration
	default_accel_power = 1
	# The power of deceleration
	default_decel_power = 2
	# Speed limit
	default_speed_limit = 30


	def __init__(self, loc_x, loc_y, loc_z,\
		width = default_width, length = default_length, mess = default_mess):
		
		super(CarAgent, self).__init__(loc_x, loc_y, loc_z)
		self.w = width
		self.l = length

		# To calculate IDM
		self.max_a = 1.0
		# Velocity
		self.v = 0.0		# IDM parameter
		# Acceleration
		self.a = 0.0
		# Mess
		self.m = mess
		# Status: created, travelling, reached
		self.status = "created"

		# Waited time
		self.timeWaited = 0
		# Sensors and state features
		self.follow = None
		self.lead = None
		# Current observed position
		self.onRoad = None
		self.onLane = None
		self.onPos = None
		# Next observed position want to go
		self.nextRoad = None
		self.nextLane = None
		self.nextPos = None
		# The destination
		self.destRoad = None
		self.destLane = None
		self.destPos = None
		# Route record and current index
		self.trace = list()
		# None means random walk
		self.route = None

	def get_approaching_rate(self):
		if self.follow == None:
			return 0
		else:
			return self.v - self.follow.v

	def get_following_distance(self):
		if self.follow == None:
			return float("inf")
		elif self.onRoad == self.follow.onRoad:
			return self.follow.onPos - self.onPos - float(self.l + self.follow.l) / 2
		else:
			return self.l - self.onPos + self.follow.onPos

	# Given traffic environment, determine things that a car can observe
	# Update car attributes
	def get_percept(self, environment):
		percept = dict()
		if self.status == "created":
			# print "Percepted as created"
			# Check in comming cars on road.
			percept["incomming"] = environment.get_incomming_car(self.nextRoad, self.nextLane, self.nextPos)
		elif self.status == "travelling":
			# print "Percepted as travelling"
			# Location update
			(road, lane, position) = environment.cars[self]
			if road != self.onRoad:
				self.onRoad = road # percept["road"]
				# Random next road for restless car
				if self.route == None:
					if environment.net.map.has_key(road):
						nList = environment.net.map[road]
						if isinstance(nList[0], RNIntersection):
							nList = environment.net.map[nList[0]]
						self.nextRoad = nList[randint(0, len(nList) - 1)]
					else:
						self.nextRoad = None
				# Get next road from route for normal car
				else:
					if len(self.route) > 0:
						self.route.remove(self.nextRoad)
						self.trace.append(self.nextRoad)
						if len(self.route) > 0:
							self.nextRoad = self.route[0]
						else:
							self.nextRoad = None
					else:
						self.nextRoad = None
			if lane != self.onLane:
				self.onLane = lane # percept["lane"]
			if position != self.onPos:
				self.onPos = position # percept["position"]
			# Previous car
			(pCar, pLane) = environment.get_previous_car(self)
			if pCar != self.follow:
				self.follow = pCar

			percept["previous_car"] = pCar
			percept["change_lane"] = pLane
		# elif self.status == "reached":
			# print "Percepted as reached"
		# elif self.status == "end":
			# print "Percepted as end"
		
		return percept

	def get_action(self, percept):
		action = dict()
		action["type"] = "none"
		# When created or reached, set up a new destination and initialize with a route
		if self.status == "created":
			incommingCar = percept["incomming"]
			wait = False
			# Check if can enter the road
			if incommingCar != None and self.distance_to(incommingCar) < self.default_entering_distance:
				wait = True
				# print "Action: wait"

			# Suppose it can not
			if wait:
				action["type"] = "wait_to_enter"
				self.timeWaited = self.timeWaited + 1
			# If it can enter the road
			else:
				# print "Action: travel"
				self.timeWaited = 0
				action["type"] = "enter_network"
				action["to_road"] = self.nextRoad
				action["to_lane"] = self.nextLane
				action["to_position"] = self.nextPos
				action["new_status"] = "travelling"

		# When initialized: wait enough entering distance to enter the road
		# Model patience: the entering distance limit decrease through time
		# Model safety: entering distance limit decrease when traffic speed is lower
		# The status become travelling once enter the road



		# IDM when travelling
		# Stop for traffic light, slow down for yellow light
		# Change lane if turning on next intersection
		# Change lane if multiple choice and current traffic speed is lower 
		
		elif self.status == "travelling":
			action["type"] = "move"
			# Update velocity and acceleration
			pCar = percept["previous_car"]
			self.update_motion(pCar, pCar)
			# Calculate next position
			toPos = self.onPos + self.v
			# Normal car Reached destination
			if self.destRoad != None and self.onRoad == self.destRoad and toPos >= self.destPos:
				if self.route == None or len(self.route) == 0:
					# print "Car reached destination"
					action["type"] = "reach_destination"
					action["new_status"] = "reached"
			# Move in the same road
			elif toPos <= self.onLane.l:
				action["to_road"] = self.onRoad
				action["to_lane"] = self.onLane
				action["to_position"] = toPos
			# Move to the next road
			else:
				# Restless car reach dead end
				if self.nextRoad == None:
					action["type"] = "reach_dead_end"
					action["new_status"] = "end"
				else:
					action["to_road"] = self.nextRoad
					if pCar == None:
						action["to_lane"] = percept["change_lane"]
					else:
						action["to_lane"] = pCar.onLane
					action["to_position"] = toPos - self.onLane.l


		# Slow down and stop when reach destination
		return action

	# Intelligent driver model
	def update_motion(self, previous_car, front_car):
		# Tendency of accelaration
		tend_accelerate = 1
		if previous_car != None and front_car != None:
			if front_car.v != 0:
				tend_accelerate = 1 - math.pow((self.v/front_car.v), self.default_accel_power)
		# Desired minimum gap
		min_gap = self.get_desired_minimum_gap()
		# Tendency of deceleration/brack
		tend_decelerate = math.pow((min_gap / self.get_following_distance()), self.default_decel_power) - 1
		# The result
		self.a = self.max_a * (tend_accelerate - tend_decelerate)
		self.v = self.v + self.a
		if self.v < 0:
			self.v = 0
		if self.v > self.default_speed_limit:
			self.v = self.default_speed_limit

	# In IDM, this describes the safety gap
	def get_desired_minimum_gap(self):
		
		return self.get_approaching_rate() * self.v / math.sqrt(self.default_accel_power * self.default_accel_power)
		# Currently fixed
		

	def update_route(self, search):
		if self.onRoad == None:
			if self.nextRoad == None:
				self.route = None
			else:
				self.route = search(self.nextRoad, self.destRoad)
		else:
			self.route = search(self.onRoad, self.destRoad)


class TrafficAgent(object):
	def __init__(self, road_network):
		super(TrafficAgent, self).__init__()
		self.net = road_network
		# The environment
		self.cars = dict()

	def add_random_car(self):
		# Select a random staring place
		(road, lane, position) = self.net.random_position_on_road()
		# Car should be off the road before entering the road network
		carLoc = lane.get_preenter_location(position)
		# Create a car at the pre-enter location
		car = CarAgent(carLoc.x, carLoc.y, carLoc.z)
		# Not on road but the next road is designated
		car.nextRoad = road
		car.nextLane = lane
		car.nextPos = position
		# Random destination
		(car.destRoad, car.destLane, car.destPos) = self.net.random_position_on_road()
		# Manage route
		car.update_route()
		# Record car
		self.cars[car] = (None, None, None)
		return car


	def add_restless_car(self):
		# Select a random staring place
		(road, lane, position) = self.net.random_position_on_road()
		# Car should be off the road before entering the road network
		carLoc = lane.get_preenter_location(position)
		# Create a car at the pre-enter location
		car = CarAgent(carLoc.x, carLoc.y, carLoc.z)
		# Not on road but the next road is designated
		car.nextRoad = road
		car.nextLane = lane
		car.nextPos = position
		# Record car
		self.cars[car] = (None, None, None)
		return car

	def get_previous_car(self, car):
		(road, lane, position) = self.cars[car]

		if road == None:
			return (None, None)

		pCar = None
		currentPos = road.l
		nextLane = None
		laneLastCar = dict()

		if car.nextRoad != None:
			currentPos = road.l + car.nextRoad.l
		# Choose previous car on current road, choose car on next road if
		# no car in current road
		for c in self.cars.keys():
			(cRoad, cLane, cPos) = self.cars[c]
			# Same road same lane choose closest next
			if cRoad == car.onRoad and cLane == car.onLane and cPos > position:
				if pCar == None or cPos < currentPos:
					pCar = c
					currentPos = cPos
			# Next road record last car for each lane
			elif cRoad == car.nextRoad and currentPos > road.l:
				if laneLastCar.has_key(cLane):
					(lastCar, lastPos) = laneLastCar[cLane]
					if cPos + road.l < lastPos:
						laneLastCar[cLane] = (c, cPos + road.l)
				else:
					laneLastCar[cLane] = (c, cPos + road.l)

		# If last car in next road
		if currentPos > road.l:
			currentPos = road.l
			# Choose the lane with farthest last car
			for lane in car.nextRoad.lanes:
				if laneLastCar.has_key(lane):
					(lastCar, lastPos) = laneLastCar[lane]
					if lastPos > currentPos:
						currentPos = lastPos
						pCar = lastCar
						nextLane = lane
				else:
					pCar = None
					nextLane = lane
					break

		return (pCar, nextLane)

	def get_incomming_car(self, road, lane, position):
		iCar = None
		iPos = None
		for c in self.cars.keys():
			(cRoad, cLane, cPos) = self.cars[c]
			if cLane == lane and cPos < position:
				if iCar == None or cPos > iPos:
					iCar = c
					iPos = cPos
		return iCar
		
	def update_cars(self):
		percepts = list()
		for car in self.cars.keys():
			percepts.append((car, car.get_percept(self)))
		actions = list()
		for (car, percept) in percepts:
			actions.append((car, car.get_action(percept)))
		rs = list()
		for (car, action) in actions:
			rs.append((car, self.process_action(car, action)))
		return rs
		
	# How phisical world respond to car's action
	def process_action(self, car, action):
		if action.has_key("new_status"):
			car.status = action["new_status"]

		if action["type"] == "wait_to_enter":
			return None
		elif action["type"] == "enter_network":
			newR = action["to_road"]
			newL = action["to_lane"]
			newP = action["to_position"]
			self.cars[car] = (newR, newL, newP)
			return newL.get_location(newP)
		elif action["type"] == "move":
			newR = action["to_road"]
			newL = action["to_lane"]
			newP = action["to_position"]
			self.cars[car] = (newR, newL, newP)
			return newL.get_location(newP)
		elif action["type"] == "reach_destination":
			self.cars[car] = (None, None, None)
			return car.onLane.get_preenter_location(car.onPos)
		elif action["type"] == "reach_dead_end":
			self.cars[car] = (None, None, None)
			return None
		return None

	# From a starting point, with chance
	def generate_random_route_with_destination(self, from_road, chance_next_road):
		route = list()
		route.append(from_road)
		print "Route starts at " + str(from_road)
		current_element = from_road
		for idx in xrange(0,10):
			# With certain chance, go to another road
			if randint(0,chance_next_road) == 0:
				break
			# End if the road ends
			if not self.net.map.has_key(current_element):
				break

			# All possible element from current road
			nList = self.net.map[current_element]
			current_element = nList[0]
			# If it is an intersection, randomly choose the next road
			if isinstance(current_element, RNIntersection):
				route.append(current_element)
				print "Add intersection"
				nList = self.net.map[current_element]
				current_element = nList[randint(0, len(nList) - 1)]

			route.append(current_element)
			print "Add element"

		# Generate destination on the last road
		(newR, newL, newP) = self.net.random_position_on_road(current_element)
		print "Random route and destination generated"
		return (route, newR, newL, newP)

	def remove_traffic(self):
		self.cars.clear()


	def a_star_route_search(start_road, end_road):
		pass

	def dijikstra_route_search(start_road, end_road):
		pass


		
import Tkinter
from roadNetwork import *
from traffic import *
from random import *

defaultNCars = 100

class TrafficSimulator(object):

	__default_lane_width = 4

	def __init__(self):	
		# Environment
		self.network = RoadNetwork()
		self.nodes = list()
		# Agents
		self.isCarSimulating = False
		self.traffic = TrafficAgent(self.network)
		self.carPoints = dict()

		self.nLane = 2

		self.nCars = 0

		# For road line creation
		self.lines = list()
		self.start_x = None
		self.start_y = None
		self.end_x = None
		self.end_y = None
		self.sOval = None
		self.eOval = None
		self.currentLine = None

		self.t = 0

		self.window = Tkinter.Tk()
		self.window.title("Traffic simulation")
		self.window.geometry('+200+10')

		self.canvas = Tkinter.Canvas(self.window, bg = "#ffffff", height = 700, width = 960)
		# canvas = Tkinter.Canvas(backupCanvas)
		self.canvas.pack()
		self.canvas.bind("<B1-Motion>", self.cursor_drag)
		self.canvas.bind("<Button-1>", self.left_btn_pressed)
		self.canvas.bind("<ButtonRelease-1>", self.left_btn_released)
		self.canvas.bind("<Double-Button-1>", self.left_double_click)

		self.window.after(40, self.updateCars())

		# self.carLabel = "Car type: random walk"
		self.carSimLabel = None
		self.laneNLabel = None
		self.nCarEntry = None
		configWindow = TrafficSimulator.prepare_configuration(self)

		configWindow.mainloop()
		self.window.mainloop()

	def left_double_click(self, event):
		# Start or end car simulation
		if self.isCarSimulating:
			print "End traffic simulation"
			# End traffic
			self.traffic.remove_traffic()
			for (car, point) in self.carPoints.items():
				self.canvas.delete(point)
			self.carPoints.clear()
			self.nCars = 0
			self.carSimLabel.config(text = "Car simulation: Off")
			self.isCarSimulating = False
		else:
			print "Start traffic simulation"
			# Start traffic
			# self.generate_continuous_traffic()
			# self.generate_random_traffic()
			self.carSimLabel.config(text = "Car simulation: On")
			self.isCarSimulating = True


	@staticmethod
	def prepare_configuration(resp):
		global defaultNCars

		print "Show configuration"
		root = Tkinter.Tk()
		# Reset button
		carTypeBtn = Tkinter.Button(root, text = "Reset simulator", command = resp.reset_simulator)
		carTypeBtn.pack()
		# Car simulation switch
		configCarSimLabel = Tkinter.Label(root, text = "Car simulation: Off")
		configCarSimLabel.pack()
		resp.carSimLabel = configCarSimLabel
		# Lane number of each road
		addLaneNBtn = Tkinter.Button(root, text = "Increment lanes in road", command = resp.increament_lane_in_road)
		addLaneNBtn.pack()
		configLaneNLabel = Tkinter.Label(root, text = str(resp.nLane) + " lanes each road")
		configLaneNLabel.pack()
		resp.laneNLabel = configLaneNLabel
		minusLaneNBtn = Tkinter.Button(root, text = "Decrement lanes in road", command = resp.decrement_lane_in_road)
		minusLaneNBtn.pack()
		# Car number entry
		configCarNLabel = Tkinter.Label(root, text = "Max number of cars")
		configCarNLabel.pack()
		configCarNEntry = Tkinter.Entry(root, textvariable = Tkinter.StringVar(root, value = str(defaultNCars)), justify = 'center')
		configCarNEntry.pack()
		resp.nCarEntry = configCarNEntry

		return root

	def increament_lane_in_road(self):
		self.nLane = self.nLane + 1
		self.laneNLabel.config(text = str(self.nLane) + " lanes each road")

	def decrement_lane_in_road(self):
		if self.nLane > 1:
			self.nLane = self.nLane - 1
		self.laneNLabel.config(text = str(self.nLane) + " lanes each road")

	def do_change_car_type(self):
		print "Change car type"

	def generate_random_traffic(self):
		for idx in xrange(100):
			newCar = self.traffic.add_random_car()
			carPoint = self.canvas.create_oval(newCar.x - 2, -newCar.y - 2, newCar.x + 2, -newCar.y + 2)
			self.carPoints[newCar] = carPoint

	def updateCars(self):
		global defaultNCars

		if self.isCarSimulating:
			# print "Time: " + str(self.t)
			value = self.nCarEntry.get()
			# print "max car: " + str(value)
			if value == None or len(value) == 0:
				self.nCarEntry.delete(0, Tkinter.END)
				self.nCarEntry.insert(Tkinter.END, str(defaultNCars))
				value = str(defaultNCars)
			if self.nCars < int(value):
				# print str(self.nCars)
				self.nCars = self.nCars + 1
				newCar = self.traffic.add_restless_car()
				carPoint = self.canvas.create_oval(newCar.x - 2, -newCar.y - 2, newCar.x + 2, -newCar.y + 2)
				self.carPoints[newCar] = carPoint

			updatedCars = self.traffic.update_cars()
			for (car, newLoc) in updatedCars:
				if newLoc != None:
					self.canvas.coords(self.carPoints[car], newLoc.x - 2, -newLoc.y - 2, newLoc.x + 2, -newLoc.y + 2)
				# else:
				# 	self.canvas.delete(point)
				# 	self.carPoints.pop(car)

			self.t = self.t + 1
			self.log()
		self.window.after(40, self.updateCars)

	def left_btn_pressed(self, event):
		# canvas = Tkinter.canvas(backupCanvas)
		self.start_x, self.start_y = event.x, event.y
		self.end_x, self.end_y = event.x, event.y
		self.currentLine = self.canvas.create_line(event.x, event.y, event.x, event.y, arrow = "last")
		self.sOval = self.canvas.create_oval(event.x - 1, event.y - 1, event.x + 1, event.y + 1)
		self.eOval = self.canvas.create_oval(event.x - 1, event.y - 1, event.x + 1, event.y + 1)

	def cursor_drag(self, event):
		if event.x != self.end_x or event.y != self.end_y:
			self.end_x, self.end_y = event.x, event.y
			self.canvas.coords(self.currentLine, self.start_x, self.start_y, event.x, event.y)
			self.canvas.coords(self.eOval, event.x - 1, event.y - 1, event.x + 1, event.y + 1)

	def left_btn_released(self, event):
		if self.start_x == None:
			return
		if abs(self.start_x - self.end_x) < 2 and abs(self.start_y - self.end_y) < 2:
			self.canvas.delete(self.currentLine)
		else:
			# Add new road intersection and corresponding view
			(newRoad, newInterSects, oldInterSects) = self.network.do_add_road(self.start_x, -self.start_y, 0, self.end_x, -self.end_y, 0, \
				self.__default_lane_width, None, self.nLane, connect = True)
			self.canvas.delete(self.currentLine)
			self.generate_lines_from_lanes(newRoad)
			for intersection in newInterSects:
				currentNode = self.canvas.create_oval(intersection.x - intersection.w/2, -intersection.y - intersection.l/2, intersection.x + intersection.w/2, -intersection.y + intersection.l/2)
				self.nodes.append((currentNode, intersection))
			for intersection in oldInterSects:
				node = self.get_view_for_intersection(intersection)
				self.canvas.coords(node, intersection.x - intersection.w/2, -intersection.y - intersection.l/2, intersection.x + intersection.w/2, -intersection.y + intersection.l/2)
				

		self.start_x = None
		self.start_y = None
		self.end_x = None
		self.end_y = None
		self.canvas.delete(self.sOval)
		self.canvas.delete(self.eOval)
		self.sOval = None
		self.eOval = None

	def reset_simulator(self):	
		print "reset simulator"	
		# Environment
		self.network.clear()
		self.nodes = list()
		# Agents
		self.isCarSimulating = False
		self.carSimLabel.config(text="Car simulation: Off")
		self.traffic.remove_traffic()
		self.carPoints = dict()

		self.nLane = 2
		self.laneNLabel.config(text= str(self.nLane) + " lanes each road")
		self.nCarEntry.delete(0,Tkinter.END)
		self.nCarEntry.insert(Tkinter.END, str(defaultNCars))

		self.nCars = 0

		self.canvas.delete("all")

		# For road line creation
		self.lines = list()
		self.start_x = None
		self.start_y = None
		self.end_x = None
		self.end_y = None
		self.sOval = None
		self.eOval = None
		self.currentLine = None
		
		self.t = 0

	def scroll_up(event):
		pass

	def scroll_down(event):
		pass

	def generate_lines_from_lanes(self, road):
		for lane in road.lanes:
			start = lane.get_entry()
			end = lane.get_exit()
			self.lines.append((self.canvas.create_line(start.x, -start.y, end.x, -end.y, arrow = "last"), road))

	def get_view_for_intersection(self, intersection):
		for (node, interSect) in self.nodes:
			if interSect == intersection:
				return node

	def log(self):
		sumV = 0
		minV = float('inf')
		maxV = float('-inf')
		for (car, point) in self.carPoints.items():
			sumV = sumV + car.v
			if car.v < minV:
				minV = car.v
			if car.v > maxV:
				maxV = car.v
		if len(self.carPoints) != 0 and self.t % 20 == 0:
			print "Min / Ave / Max = [" + str(minV) + " / " + str(float(sumV) / len(self.carPoints)) + " / " + str(maxV) + "]"


ts = TrafficSimulator()



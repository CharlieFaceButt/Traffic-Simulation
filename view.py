import Tkinter
from roadNetwork import *


class TrafficSimulator(object):

	__default_lane_width = 4
	__default_n_lane = 2

	def __init__(self):	
		self.network = RoadNetwork()
		self.nodes = list()

		# For road line creation
		self.lines = list()
		self.start_x = None
		self.start_y = None
		self.end_x = None
		self.end_y = None
		self.sOval = None
		self.eOval = None
		self.currentLine = None

		self.window = Tkinter.Tk()
		self.window.title("Traffic simulation")
		# backupCanvas = Tkinter.Canvas(window, bg = "#ffffff", height = 540, width = 960)
		self.canvas = Tkinter.Canvas(self.window, bg = "#ffffff", height = 540, width = 960)
		# canvas = Tkinter.Canvas(backupCanvas)
		self.canvas.pack()
		self.canvas.bind("<B1-Motion>", self.cursor_drag)
		self.canvas.bind("<Button-1>", self.left_btn_pressed)
		self.canvas.bind("<ButtonRelease-1>", self.left_btn_released)
		self.window.mainloop()

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
		if abs(self.start_x - self.end_x) < 2 and abs(self.start_y - self.end_y) < 2:
			self.canvas.delete(self.currentLine)
		else:
			(newRoad, newInterSects, oldInterSects) = self.network.do_add_road(self.start_x, -self.start_y, 0, self.end_x, -self.end_y, 0, \
				self.__default_lane_width, None, self.__default_n_lane, connect = True)
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

ts = TrafficSimulator()



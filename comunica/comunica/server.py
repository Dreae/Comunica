import socket, threading, select, time, json, random
from .client import ChatClient
from . import lock

class ChatServer(object):
	def __init__(self, port=8080, bind=''):
		self._socket = socket.socket()
		self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.bind = bind
		self.port = port
		self._shutdown_req = False
		self.reactors = [Reactor() for x in range(4)]
	
	def serve(self):
		self._socket.bind((self.bind, self.port))
		self._socket.listen(3)
		while not self._shutdown_req:
			r, w, e = select.select([self._socket], [], [], 0.5)
			if self._socket in r:
				try:
					conn, addr = self._socket.accept()
				except:
					continue
				
				client = ChatClient(conn, addr)
				if client.handshake():
					room = self.get_room(client.room)
					if room:
						room.clients.append(client)
						client.room = room
					else:
						client._sock.shutdown()
						client._sock.close()
						
	def get_room(self, room):
		for reactor in self.reactors:
			lock.acquire()
			for rm in reactor.rooms:
				if rm.name == room:
					lock.release()
					return rm
			lock.release()
		return None
		
	def add_room(self, new_room):
		room = Room(new_room)
		random.choice(self.reactors).rooms.append(room)
		
		
class Room(object):
	def __init__(self, name):
		self.name = name
		self.clients = []
	
	def serve(self):
		if not self.clients:
			return
		r, w, e = select.select(self.clients, self.clients, [], 0.5)
		if r:
			for client in r:
				client.handle()
		if w:
			for client in w:
				if client.waiting_to_write():
					client.write()
			
	def sendToRoom(self, client, msg):
		if not client.name:
			return
		dict = {'evt': 'message', 'from': (client.name, client.name_color), 'value': msg}
		payload = json.dumps(dict).encode('utf-8')
		self._broadcast(payload)
		
	def _broadcast(self, payload):
		for client in self.clients:
			client.send(payload)
	
	def set_nick(self, client, nick):
		while nick in [c.name for c in self.clients if c != client]:
			nick += '_'
			if len(nick) > 24:
				nick = nick[1:25]
		client.name = nick
		
	def shutdown(self):
		for client in self.clients:
			client.kill()
		
class Reactor(object):
	def __init__(self):
		self.rooms = []
		self._shutdown_req = False
		self._thread = threading.Thread(target=self.react)
		self._thread.start()
		
	def react(self):
		while not self._shutdown_req:
			if self.rooms:
				for room in self.rooms:
					room.serve()
			else:
				time.sleep(1)
		for room in self.rooms:
			room.shutdown()
				
	def shutdown(self):
		self._shutdown_req = True
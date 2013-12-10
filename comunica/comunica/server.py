import socket, threading, select, time, json
from .client import ChatClient

class ChatServer(object):
	def __init__(self, port=8080, bind=''):
		self._socket = socket.socket()
		self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.bind = bind
		self.port = port
		self.rooms = []
		self._shutdown_req = False
	
	def serve(self):
		self._socket.bind((self.bind, self.port))
		self._socket.listen(3)
		while not self._shutdown_req:
			r, w, e = select.select([self._socket], [], [], 0.5)
			if self._socket in r:
				conn, addr = self._socket.accept()
				client = ChatClient(conn, addr)
				if client.handshake():
					room = self.get_room(client.room)
					if room:
						room.clients.append(client)
						client.room = room
					else:
						client._sock.close()
						
	def get_room(self, room):
		for rm in self.rooms:
			if rm.name == room:
				return rm
		return None
		
	def add_room(self, new_room):
		room = Room(new_room)
		self.rooms.append(room)
		threading.Thread(target=room.serve).start()
		
class Room(object):
	def __init__(self, name):
		self.name = name
		self.clients = []
		self._shutdown_req = False
	
	def serve(self):
		while not self._shutdown_req:
			while not self.clients:
				time.sleep(1)
			r, w, e = select.select(self.clients, [], [], 0.5)
			if r:
				for client in r:
					client.handle()
			
	def sendToRoom(self, client, msg):
		if not client.name:
			return
		dict = {'evt': 'message', 'from': (client.name, client.name_color), 'value': msg}
		payload = json.dumps(dict).encode('utf-8')
		self._broadcast(payload)
		
	def _broadcast(self, payload):
		response = chr(0x81)+chr(len(payload))+payload
		r, w, e = select.select([], self.clients, [], 0.05)
		for client in w:
			try:
				client._sock.send(response)
			except:
				client._sock.close()
				self.clients.remove(client)
	
	def set_nick(self, client, nick):
		while nick in [c.name for c in self.clients if c != client]:
			nick += '_'
			if len(nick) > 24:
				nick = nick[1:25]
		client.name = nick
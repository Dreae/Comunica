import socket, threading, select, time, json, random
from .client import ChatClient
from .room import Room
from .ORM import ComunicaRoom, Base, ComunicaMod
from . import lock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

class ChatServer(object):
	def __init__(self, registry):
		self._socket = socket.socket()
		self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.registry = registry
		self._shutdown_req = False
		self.reactors = [Reactor() for x in range(4)]
		self.database = DatabaseConnection(self.registry)
		self.database.load_rooms(self)
	
	def serve(self):
		self._socket.bind((self.registry.bind, self.registry.port))
		self._socket.listen(3)
		while not self._shutdown_req:
			r, w, e = select.select([self._socket], [], [], 0.5)
			if self._socket in r:
				try:
					conn, addr = self._socket.accept()
				except:
					continue
				conn.setblocking(0)	
				client = ChatClient(conn, addr)
				if client.handshake():
					room = self.get_room(client.room)
					if room:
						client.buffer.append(self.settings())
						room.clients.append(client)
						client.room = room
					else:
						client._sock.close()
				else:
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
		
	def add_room(self, new_room, room_id):
		room = Room(self, new_room, room_id)
		random.choice(self.reactors).rooms.append(room)
		
	def settings(self):
		return json.dumps({'evt': 'server-info', 'name': self.registry.server, 'supports_auth': self.registry.supports_auth, 
							'host': self.registry.bind, 'port': self.registry.port}).encode('utf-8')
		
		
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
		
class DatabaseConnection(object):
	def __init__(self, registry):
		self.engine = create_engine(registry.database)
		self.Session = sessionmaker(bind=self.engine)()
		Base.metadata.create_all(self.engine)
	
	def load_rooms(self, server):
		for room in self.Session.query(ComunicaRoom).all():
			sever.add_room(room.name, room.id)
			
	def load_mods(self, room):
		return [mod.user.name for mod in self.Session.query(ComunicaMod).filter(ComunicaMod.room_id == room).all()]
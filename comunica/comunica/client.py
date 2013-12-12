import socket, hashlib, base64, json, re
from asyncore import _DISCONNECTED
from errno import EWOULDBLOCK

class ChatClient(object):
	def __init__(self, socket, addr):
		self._sock = socket
		self._addr = addr
		self.name = None
		self.name_color = '#000'
		self.buffer = []
	
	def set_color(self, color):
		if not 'rgb' in color:
			return False
		if re.findall(r'[^0-9\(\),rgb ]', color):
			return False
		self.name_color = color
		
	def handle(self):
		data = self.read()
		if not data: 
			return
		
		fin    = ord(data[0]) & 0x80 == 0x80
		rsv1   = ord(data[0]) & 0x40 == 0x40
		rsv2   = ord(data[0]) & 0x20 == 0x20
		rsv3   = ord(data[0]) & 0x10 == 0x10
		opcode = ord(data[0]) & 0xf
		masked = ord(data[1]) & 0x80 == 0x80
		paylen = ord(data[1]) & 0x7f
		
		if rsv1 or rsv2 or rsv3:
			self.kill()
		
		if paylen == 126:
			offset = 4
		elif paylen == 127:
			offset = 6
		else:
			offset = 2
		
		if masked:
			mask = data[offset:offset+4]
		
		payload = data[offset+4 if masked else 0:]
		
		if masked:
			frame = ''.join(unichr(ord(a) ^ ord(mask[i % 4])) for i, a in enumerate(payload))
		else:
			frame = payload
	
		if opcode == 0x09:
			self.send(frame, 0x8A)
			return
		
		try:
			event = json.loads(frame.decode('utf-8'))
		except:
			return
		if event['evt'] == 'message':
			self.room.sendToRoom(self, event['value'][:255])
		elif event['evt'] == 'set-nick':
			self.room.set_nick(self, event['value'][:24].strip())
		elif event['evt'] == 'get-viewers':
			self.send(json.dumps({'evt': 'viewers', 'value': [client.name for client in self.room.clients]}).encode('utf-8'), 0x81)
		elif event['evt'] == 'set-color':
			self.set_color(event['value'])
		elif event['evt'] == 'authenticate':
			if self.room.server.registry.auth_provider.authenticate(event['username'], event['password']): #TODO: run queries on new thread,
				self.room.authed_set_nick(self, event['username'])                                         #slow database blocks whole reactor
				self.send(json.dumps({'evt': 'auth-result', 'success': True, 'nick': event['username']}).encode('utf-8'), 0x81)
			else:
				self.room.set_nick(event['username'])
				self.send(json.dumps({'evt': 'auth-result', 'success': False, 'nick': self.name}).encode('utf-8'), 0x81)
			
	def handshake(self):
		data = self.read()
		if not data: 
			return
		lines = data.splitlines()
		for line in lines:
			if 'GET' in line:
				self.room = line.split(' ')[1].strip('/')
			elif 'Sec-WebSocket-Key' in line:
				self.key = line.split(': ', 1)[1]
				self.accept = base64.b64encode(hashlib.sha1(self.key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'.encode('utf-8')).digest()).encode('utf-8')

		if not hasattr(self, 'accept') or not hasattr(self, 'room'):
			return False
		response = 'HTTP/1.1 101 WebSocket Protocol Handshake\r\n'
		response += 'Upgrade: websocket\r\n'
		response += 'Connection: Upgrade\r\n'
		response += 'Sec-WebSocket-Protocol: comunica\r\n'
		response += 'Sec-WebSocket-Accept: {}\r\n\r\n'.format(self.accept)
		try:
			self._sock.send(response.encode('utf-8'))
		except socket.error:
			return False
		return True
	
	def send(self, payload, opcode):
		length = len(payload)
		if length <= 125:
			response = [opcode, len(payload)] + map(ord, payload)
		elif length <= 65535:
			response = [opcode, 126] + [len(payload) >> i & 0xff for i in [8,0]] + map(ord, payload)
		else:
			response = [opcode, 127] + [len(payload) >> i & 0xff for i in [24,16,8,0]] + map(ord, payload)
	
		try:
			self._sock.send(bytearray(response))
		except socket.error, why:
			if why.args[0] == EWOULDBLOCK:
				self.buffer.append(response)
				return
			elif why.args[0] in _DISCONNECTED:
				self.kill()
	
	def waiting_to_write(self):
		if self.buffer:
			return True
		return False
	
	def write(self):
		self.send(self.buffer.pop(0), 0x81)
	
	def read(self):
		data = ''
		try:
			data = self._sock.recv(1024).strip()
		except socket.error, why:
			if why.args[0] in _DISCONNECTED:
				self.kill()
				return None
		if not data: 
			self.kill()
			return None
		return data
	
	def fileno(self):
		return self._sock.fileno()
		
	def kill(self):
		self._sock.close()
		try:
			self.room.clients.remove(self)
		except:
			return
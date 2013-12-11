import socket, hashlib, base64, json, re
from asyncore import _DISCONNECTED
from errno import EWOULDBLOCK

class ChatClient(object):
	def __init__(self, socket, addr):
		self._sock = socket
		self._addr = addr
		self.name = None
		self.name_color = '#000'
		self.buffer = ''
	
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
		length = ord(data[1]) ^ 128
		if length == 126:
			offset = 4
		elif length == 127:
			offset = 6
		else:
			offset = 2			
		mask = data[offset:offset+4]
		payload = data[offset+4:]
		frame = ''.join(unichr(ord(a) ^ ord(mask[i % 4])) for i, a in enumerate(payload))
		try:
			event = json.loads(frame.decode('utf-8'))
		except:
			return
		if event['evt'] == 'message':
			self.room.sendToRoom(self, event['value'][:255])
		elif event['evt'] == 'set-nick':
			self.room.set_nick(self, event['value'][:24].strip())
		elif event['evt'] == 'get-viewers':
			self.send(json.dumps({'evt': 'viewers', 'value': [client.name for client in self.room.clients]}).encode('utf-8'))
		elif event['evt'] == 'set-color':
			self.set_color(event['value'])
			
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
		response += 'Sec-WebSocket-Accept: {}\r\n\r\n'.format(self.accept)
		try:
			self._sock.send(response.encode('utf-8'))
		except socket.error, why:
			if why.args[0] in _DISCONNECTED:
				self.kill()
			return False
		return True
		
	def send(self, payload):
		length = len(payload)
		if length <= 125:
			response = [0x81, len(payload)] + map(ord, payload)
		elif length <= 65535:
			response = [0x81, 126] + [len(payload) >> i & 0xff for i in [8,0]] + map(ord, payload)
		else:
			response = [0x81, 127] + [len(payload) >> i & 0xff for i in [24,16,8,0]] + map(ord, payload)
	
		try:
			self._sock.send(bytearray(response))
		except socket.error, why:
			if why.args[0] == EWOULDBLOCK:
				self.buffer += "\n" + response
				return
			elif why.args[0] in _DISCONNECTED:
				self.kill()
	
	def waiting_to_write(self):
		if self.buffer:
			return True
		return False
	
	def write(self):
		lines = self.buffer.split('\n')
		try:
			self._sock.send(lines[0])
		except socket.error, why:
			if why.args[0] == EWOULDBLOCK:
				return
			elif why.args[0] in _DISCONNECTED:
				self.kill()
				return
		self.buffer = lines[1:]
	
	def read(self):
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
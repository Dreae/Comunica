import socket, hashlib, base64, json
from asyncore import _DISCONNECTED
from errno import EWOULDBLOCK

class ChatClient(object):
	def __init__(self, socket, addr):
		self._sock = socket
		self._addr = addr
		self.name = None
		self.name_color = '#000'
		self.buffer = ''
	
	def handle(self):
		try:
			self.data = self._sock.recv(1024).strip()
		except socket.error, why:
			if why.args[0] in _DISCONNECTED:
				self._sock.close()
				self.room.clients.remove(self)
		if not self.data: 
			self._sock.close()
			self.room.clients.remove(self)
			return
		mask = self.data[2:6]
		payload = self.data[6:]
		frame = ''.join(unichr(ord(a) ^ ord(mask[i % 4])) for i, a in enumerate(payload))
		try:
			event = json.loads(frame.decode('utf-8'))
		except:
			return
		if event['evt'] == 'message':
			self.room.sendToRoom(self, event['value'])
		elif event['evt'] == 'set-nick':
			self.room.set_nick(self, event['value'][0:24])
		elif event['evt'] == 'get-viewers':
			self.send(json.dumps({'viewers': [client.name for client in self.room.clients]}).encode('utf-8'))

	def handshake(self):
		data = self._sock.recv(1024).strip()
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
		response = chr(0x81)+chr(len(payload))+payload
		try:
			self._sock.send(response)
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
	
	def fileno(self):
		return self._sock.fileno()
		
	def kill(self):
		self._sock.shutdown()
		self._sock.close()
		try:
			self.room.clients.remove(self)
		except:
			return
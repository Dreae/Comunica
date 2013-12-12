import passlib.hash, time, threading
from sqlalchemy import create_engine, text
from .config import ConfigRegistry

class BaseAuthProvider(object):
	def __init__(self, config_registry):
		self.engine = create_engine(config_registry.auth_connection)
		self.select_query = config_registry.auth_selectSQL
		self.hashfunc = self.load_hashfunc(config_registry.auth_hashfunc)
		self.queue = []
		self._shutdown_req = False
		self.thread = threading.Thread(target=self.proc_queue).start()
	
	def proc_queue(self):
		while not self._shutdown_req:
			if not self.queue:
				time.sleep(1)
			else:
				cmd = self.queue.pop(0)
				if cmd['cmd'] == 'authenticate':
					self.authenticate(cmd['client'], cmd['username'], cmd['password'])
					
	def req_auth(self, client, username, password):
		self.queue.append({'cmd': 'authenticate', 'username': username, 'password': password, 'client': client})
		
	def authenticate(self, client, username, password):
		print "WARNING: Un-handled authenticate call in {}".format('.'.join([self.__class__.__module__, self.__class__.__name__]))
		return False
	
	def load_hashfunc(self):
		print "WARNING: Un-handled load_hashfunc call in {}".format('.'.join([self.__class__.__module__, self.__class__.__name__]))
		return False
	
class AuthProvider(BaseAuthProvider):
	def load_hashfunc(self, hashfunc):
		if hashfunc == 'md5':
			return passlib.hash.md5_crypt.verify
		elif hashfunc == 'bcrypt':
			return passlib.hash.bcrypt.verify
		elif hashfunc == 'sha1':
			return passlib.hash.sha1_crypt.verify
		elif hashfunc == 'sha256':
			return passlib.hash.sha256_crypt.verify
		elif hashfunc == 'sha512':
			return passlib.hash.sha512_crypt.verify
		elif hashfunc == 'pbkdf2_sha1':
			return passlib.hash.pbkdf2_sha1.verify
		elif hashfunc == 'pbkdf2_sha256':
			return passlib.hash.pbkdf2_sha256.verify
		elif hashfunc == 'pbkdf2_sha512':
			return passlib.hash.pbkdf2_sha512.verify
		else:
			return lambda password, hash: password == hash
		
	def authenticate(self, client, username, password):
		hash = self.engine.execute(text(self.select_query), username=username).scalar()
		if hash:
			client.queue.append({'event': 'auth-result', 'success': self.hashfunc(password, hash), 'nick': username})
		else:
			client.queue.append({'event': 'auth-result', 'success': False, 'nick': username})
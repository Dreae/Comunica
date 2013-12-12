import passlib.hash
from sqlalchemy import create_engine, text
from .config import ConfigRegistry

class BaseAuthProvider(object):
	def __init__(self, config_registry):
		self.engine = create_engine(config_registry.auth_connection)
		self.select_query = config_registry.auth_selectSQL
		self.hashfunc = self.load_hashfunc(config_registry.auth_hashfunc)
		
	def authenticate(self, username, password):
		print "WARNING: Un-handled authenticate call in {}".format('.'.join([self.__class__.__module__, self.__class__.__name__]))
		return False
	
	def load_hashfunc(self):
		print "WARNING: Un-handled load_hashfunc call in {}".format('.'.join([self.__class__.__module__, self.__class__.__name__]))
		return False
	
class AuthProvider(BaseAuthProvider):
	def load_hashfunc(self, hashfunc):
		if hashfunc == 'md5':
			return passlib.hash.md5_crypt.verify
		elif hashfunc = 'bcrypt':
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
		
	def authenticate(self, username, password):
		hash = self.engine.execute(text(self.select_query), username=username).scalar()
		return self.hashfunc(password, hash)
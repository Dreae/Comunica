import xml.etree.ElementTree as ET
import importlib

class ConfigRegistry(object):
	def __init__(self, config_file):
		tree = ET.parse(config_file)
		root = tree.getroot()
		self.server = root.findtext('server/name', 'Comunica')
		self.bind = root.findtext('server/network/bind', '0.0.0.0')
		
		try:
			self.port = int(root.findtext('server/network/port', '8080'))
		except:
			self.port = 8080
		
		self.database = root.findtext('database/connection', 'sqlite:///comunica.db')
		self.supports_auth = root.findtext('auth/supported', 'false').lower() in ['true', 'yes', '1', 't']
		
		self.auth_connection = root.findtext('auth/connection', None)
		self.auth_selectSQL = root.findtext('auth/passwordSQL', None)
		self.auth_hashfunc = root.findtext('auth/passwordHash', 'plain').lower()
		
		if not self.auth_connection or not self.auth_selectSQL:
			self.supports_auth = False
		else:
			try:
				auth_provider = root.findtext('auth/provider', 'comunica.auth.AuthProvider')
				module_name, class_name = auth_provider.rsplit('.', 1)
				module = importlib.import_module(module_name)
				cls = getattr(module, class_name)
				self.auth_provider = cls(self)
			except:
				self.supports_auth = False
		
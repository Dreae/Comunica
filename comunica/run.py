from comunica.server import ChatServer
from comunica.config import ConfigRegistry
import os

if __name__ == "__main__":
	registry = ConfigRegistry('%s/config/comunica.xml' % os.path.dirname(os.path.realpath(__file__)))
	server = ChatServer(registry)
	server.add_room('lobby')
	server.serve()
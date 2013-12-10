from comunica.server import ChatServer

if __name__ == "__main__":
	server = ChatServer()
	server.add_room('lobby')
	server.serve()
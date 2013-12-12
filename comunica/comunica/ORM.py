from sqlalchemy import Column, ForeignKey, PrimaryKeyConstraint, String, Integer
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ComunicaRoom(Base):
	__tablename__ = 'comunica_rooms'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(64))
	
	def __init__(self, name):
		self.name = name
	
class ComunicaUser(Base):
	__tablename__ = 'comunica_users'
	
	id = Column(Integer, primary_key=True)
	name = Column(String(64), unique=True)
	
	def __init__(self, name):
		self.name = name
	
class ComunicaMod(Base):
	__tablename__ = 'comunica_rooms_mods'
	
	user_id = Column(Integer, ForeignKey('comunica_users.id', ondelete='CASCADE'))
	user = relationship('ComunicaUser', backref=backref('rooms', cascade='all, delete', lazy='joined'))
	room_id = Column(Integer, ForeignKey('comunica_rooms.id', ondelete='CASCADE'))
	room = relationship('ComunicaRoom', backref=backref('mods', cascade='all, delete', lazy='joined'))
	__table_args__ = (PrimaryKeyConstraint('user_id', 'room_id'), {})
	
	def __init__(self, userid, roomid):
		self.user_id = userid
		self.room_id = roomid
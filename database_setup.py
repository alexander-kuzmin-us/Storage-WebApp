from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'picture': self.picture
        }


class AutoRepairCenter(Base):
    __tablename__ = 'autorepaircenter'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    user = relationship(User)
    container_item = relationship('ContainerItem', 
                                 cascade='all, delete-orphan',
                                 backref='autorepaircenter')
    
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id
        }


class ContainerItem(Base):
    __tablename__ = 'container_item'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    price = Column(String(8))
    type = Column(String(250))
    autorepaircenter_id = Column(Integer, 
                               ForeignKey('autorepaircenter.id', ondelete='CASCADE'),
                               nullable=False)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'type': self.type,
            'autorepaircenter_id': self.autorepaircenter_id,
            'user_id': self.user_id
        }


# Create an engine that stores data in the local directory's autorepaircenter.db file
engine = create_engine('sqlite:///autorepaircenter.db')

# Create all tables in the engine
Base.metadata.create_all(engine)

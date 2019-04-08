from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Storage(Base):
    __tablename__ = 'storage'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,
       }

class ContainerItem(Base):
    __tablename__ = 'container_item'


    name =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    storage_id = Column(Integer,ForeignKey('storage.id'))
    storage = relationship(Storage)


    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'description'         : self.description,
           'id'         : self.id,
       }



engine = create_engine('sqlite:///storage.db')


Base.metadata.create_all(engine)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Storage, Base, ContainerItem

engine = create_engine('sqlite:///storage.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()



#Container for Boston Public
storage1 = Storage(name = "Boston Public")

session.add(storage1)
session.commit()


containerItem1 = ContainerItem(name = "Old boat", description = "The oldest boat in Boston")

session.add(containerItem1)
session.commit()


containerItem2 = ContainerItem(name = "New sail", description = "New sail, can be used with any boats")

session.add(containerItem2)
session.commit()


#Container for Cambridge Public
storage2 = Storage(name = "Cambridge Public")

session.add(storage2)
session.commit()


containerItem1 = ContainerItem(name = "Old bicycle", description = "The oldest bicycle in Cambridge")

session.add(containerItem1)
session.commit()


containerItem2 = ContainerItem(name = "New wheel tire", description = "New wheel tire, can be used with any bicycles")

session.add(containerItem2)
session.commit()


print "Added Container Items"

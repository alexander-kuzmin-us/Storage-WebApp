from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Storage, ContainerItem
from flask import session as login_session
import random
import string


app = Flask(__name__)


#Connect to Database and create database session
engine = create_engine('sqlite:///storage.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return "The current session state is %s" % login_session['state']


#JSON APIs to view storage Information
@app.route('/storage/<int:storage_id>/container/JSON')
def StorageContainerJSON(storage_id):
    storage = session.query(Storage).filter_by(id = storage_id).one()
    items = session.query(ContainerItem).filter_by(storage_id = storage_id).all()
    return jsonify(ContainerItems=[i.serialize for i in items])


@app.route('/storage/<int:storage_id>/container/<int:container_id>/JSON')
def ContainerItemJSON(storage_id, container_id):
    Container_Item = session.query(ContainerItem).filter_by(id = container_id).one()
    return jsonify(Container_Item = Container_Item.serialize)

@app.route('/storage/JSON')
def StoragesJSON():
    storages = session.query(Storage).all()
    return jsonify(storages= [r.serialize for r in storages])


#Show all storages
@app.route('/')
@app.route('/storage/')
def ShowStorages():
  storages = session.query(Storage).order_by(asc(Storage.name))
  return render_template('storages.html', storages = storages)

#Create a new storage
@app.route('/storage/new/', methods=['GET','POST'])
def NewStorage():
  if request.method == 'POST':
      NewStorage = Storage(name = request.form['name'])
      session.add(NewStorage)
      flash('New storage %s Successfully Created' % NewStorage.name)
      session.commit()
      return redirect(url_for('ShowStorages'))
  else:
      return render_template('newstorage.html')

#Edit a storage
@app.route('/storage/<int:storage_id>/edit/', methods = ['GET', 'POST'])
def EditStorage(storage_id):
  editedstorage = session.query(Storage).filter_by(id = storage_id).one()
  if request.method == 'POST':
      if request.form['name']:
        editedstorage.name = request.form['name']
        flash('storage Successfully Edited %s' % editedstorage.name)
        return redirect(url_for('ShowStorages'))
  else:
    return render_template('editstorage.html', storage = editedstorage)


#Delete a storage
@app.route('/storage/<int:storage_id>/delete/', methods = ['GET','POST'])
def DeleteStorage(storage_id):
  storageToDelete = session.query(Storage).filter_by(id = storage_id).one()
  if request.method == 'POST':
    session.delete(storageToDelete)
    flash('%s Successfully Deleted' % storageToDelete.name)
    session.commit()
    return redirect(url_for('ShowStorages', storage_id = storage_id))
  else:
    return render_template('deletestorage.html',storage = storageToDelete)

#Show a storage container
@app.route('/storage/<int:storage_id>/')
@app.route('/storage/<int:storage_id>/container/')
def ShowContainer(storage_id):
    storage = session.query(Storage).filter_by(id = storage_id).one()
    items = session.query(ContainerItem).filter_by(storage_id = storage_id).all()
    return render_template('container.html', items = items, storage = storage)



#Create a new container item
@app.route('/storage/<int:storage_id>/container/new/',methods=['GET','POST'])
def NewContainerItem(storage_id):
  storage = session.query(Storage).filter_by(id = storage_id).one()
  if request.method == 'POST':
      newItem = ContainerItem(name = request.form['name'], description = request.form['description'], storage_id = storage_id)
      session.add(newItem)
      session.commit()
      flash('New Container %s Item Successfully Created' % (newItem.name))
      return redirect(url_for('ShowContainer', storage_id = storage_id))
  else:
      return render_template('newcontaineritem.html', storage_id = storage_id)

#Edit a container item
@app.route('/storage/<int:storage_id>/container/<int:container_id>/edit', methods=['GET','POST'])
def EditContainerItem(storage_id, container_id):

    editedItem = session.query(ContainerItem).filter_by(id = container_id).one()
    storage = session.query(Storage).filter_by(id = storage_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        flash('Container Item Successfully Edited')
        return redirect(url_for('ShowContainer', storage_id = storage_id))
    else:
        return render_template('editcontaineritem.html', storage_id = storage_id, container_id = container_id, item = editedItem)


#Delete a container item
@app.route('/storage/<int:storage_id>/container/<int:container_id>/delete', methods = ['GET','POST'])
def DeleteContainerItem(storage_id, container_id):
    storage = session.query(Storage).filter_by(id = storage_id).one()
    itemToDelete = session.query(ContainerItem).filter_by(id = container_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Container Item Successfully Deleted')
        return redirect(url_for('ShowContainer', storage_id = storage_id))
    else:
        return render_template('deletecontaineritem.html', item = itemToDelete)




if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)

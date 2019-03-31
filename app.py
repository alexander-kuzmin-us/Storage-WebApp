from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Storage, ContainerItem

app = Flask(__name__)

#Connect to Database and create database session
engine = create_engine('sqlite:///storage.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/about/')
def about():
    return render_template('about.html')


#Show all Storages
@app.route('/')
@app.route('/storage/')
def showStorages():
    storages = session.query(Storage).order_by(asc(Storage.name))
    return render_template('storages.html', storages=storages)


#Create a new Storage
@app.route('/storage/new', methods=['GET','POST'])
def newStorage():
    if request.method == 'POST':
      newstorage = Storage(name = request.form['name'])
      session.add(newstorage)
      flash('New Storage %s Successfully Created' % newstorage.name)
      session.commit()
      return redirect(url_for('showstorages'))
    else:
     return render_template("newstorage.html")


#Edit a Storage
@app.route('/storage/<int:storage_id>/edit/', methods = ['GET', 'POST'])
def editStorage(storage_id):
    editstorage = session.query(Storage).filter_by(id = storage_id).one()
    if request.method == 'POST':
      if request.form['name']:
        editstorage.name = request.form['name']
        flash('Storage Successfully Edited %s' % editstorage.name)
        return redirect(url_for('showstorages'))
    else:
        return render_template('editstorage.html', storage = editstorage)


#Delete a Storage
@app.route('/storage/<int:storage_id>/delete/', methods = ['GET','POST'])
def deleteStorage(storage_id):
    storagetodelete = session.query(Storage).filter_by(id = storage_id).one()
    if request.method == 'POST':
        session.delete(storagetodelete)
        flash('%s Successfully Deleted' % storagetodelete.name)
        session.commit()
        return redirect(url_for('showstorages', storage_id = storage_id))
    else:
        return render_template('deletestorage.html', storage = storagetodelete)


#Show a Storage container
@app.route('/storage/<int:storage_id>/')
@app.route('/storage/<int:storage_id>/container/')
def showContainer(storage_id):
    storage = session.query(Storage).filter_by(id = storage_id).one()
    items = session.query(ContainerItem).filter_by(storage_id = storage_id).all()
    return render_template("container.html", items = items, storage = storage)


#Create a new item in the container
@app.route('/storage/<int:storage_id>/container/new', methods=['GET','POST'])
def newContainerItem(storage_id):
    storage = session.query(Storage).filter_by(id = storage_id).one()
    if request.method == 'POST':
        newItem = ContainerItem(name = request.form['name'], description = request.form['description'], storage_id = storage_id)
        session.add(newItem)
        session.commit()
        flash('New Container %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showContainer', storage_id = storage_id))
    else:
        return render_template('newcontaineritem.html', storage_id = storage_id)


#Edit an item in the container
@app.route('/storage/<int:storage_id>/container/<int:container_id>/edit',  methods=['GET','POST'])
def editContainerItem(storage_id, container_id):
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
        return redirect(url_for('showContainer', storage_id = storage_id))
    else:
        return render_template('editcontaineritem.html', storage_id = storage_id, container_id = container_id, item = editedItem)


#Delete an item in the container
@app.route('/storage/<int:storage_id>/container/<int:container_id>/delete', methods = ['GET','POST'])
def deleteContainerItem(storage_id, container_id):
    storage = session.query(Storage).filter_by(id = storage_id).one()
    itemToDelete = session.query(ContainerItem).filter_by(id = container_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Container Item Successfully Deleted')
        return redirect(url_for('showContainer', storage_id = storage_id))
    else:
        return render_template('deletecontaineritem.html', item = itemToDelete)


if __name__=="__main__":
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)

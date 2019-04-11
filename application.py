from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from flask_oauth import OAuth
from flask import session as login_session
import random
import string
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Storage, ContainerItem


# You must configure these 3 values from Google APIs console
# https://code.google.com/apis/console
GOOGLE_CLIENT_ID = '462283270013-4l8lmtsrefrernp61ipu1s89tqqbsdcd.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = 'SHk33xIo-L7PiPQMLQ74-0_2'
REDIRECT_URI = '/oauth2callback'  # one of the Redirect URIs from Google APIs console

SECRET_KEY = 'development key'
DEBUG = True


app = Flask(__name__)
app.debug = DEBUG
app.secret_key = SECRET_KEY
oauth = OAuth()


#Connect to Database and create database session
engine = create_engine('sqlite:///storage.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


google = oauth.remote_app('google',
base_url='https://www.google.com/accounts/',
authorize_url='https://accounts.google.com/o/oauth2/auth',
request_token_url=None,
request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.email',
'response_type': 'code'},
access_token_url='https://accounts.google.com/o/oauth2/token',
access_token_method='POST',
access_token_params={'grant_type': 'authorization_code'},
consumer_key=GOOGLE_CLIENT_ID,
consumer_secret=GOOGLE_CLIENT_SECRET)

@app.route('/')
def index():
access_token = session.get('access_token')
if access_token is None:
return redirect(url_for('login'))

access_token = access_token[0]
from urllib2 import Request, urlopen, URLError

headers = {'Authorization': 'OAuth '+access_token}
req = Request('https://www.googleapis.com/oauth2/v1/userinfo',
None, headers)
try:
res = urlopen(req)
except URLError, e:
if e.code == 401:
# Unauthorized - bad token
session.pop('access_token', None)
return redirect(url_for('login'))
return res.read()

return res.read()

@app.route('/login')
def login():
callback=url_for('authorized', _external=True)
return google.authorize(callback=callback)

@app.route(REDIRECT_URI)
@google.authorized_handler
def authorized(resp):
access_token = resp['access_token']
session['access_token'] = access_token, ''
return redirect(url_for('index'))

@google.tokengetter
def get_access_token():
return session.get('access_token')


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

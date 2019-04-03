from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Storage, ContainerItem
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xecdeppp//33]/'


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Public Storage App"


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
    #return "The current session state is %s" % login_session['state']
    return render_template('login.html')


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Restaurant Information
@app.route('/storage/<int:storage_id>/container/JSON')
def storageContainerJSON(storage_id):
    storage = session.query(Storage).filter_by(id=storage_id).one()
    items = session.query(ContainerItem).filter_by(
        storage_id=storage_id).all()
    return jsonify(ContainerItems=[i.serialize for i in items])


@app.route('/storage/<int:storage_id>/container/<int:container_id>/JSON')
def containerItemJSON(storage_id, container_id):
    Container_Item = session.query(ContainerItem).filter_by(id=container_id).one()
    return jsonify(Container_Item=Container_Item.serialize)


@app.route('/storage/JSON')
def storagesJSON():
    storages = session.query(Storage).all()
    return jsonify(storages=[r.serialize for r in strages])


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

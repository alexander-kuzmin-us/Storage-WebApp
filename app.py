from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, AutoRepairCenter, ContainerItem, User
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


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Auto Repair Center"


#Connect to Database and create database session
engine = create_engine('sqlite:///autorepaircenter.db')
Base.metadata.bind = engine


DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


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

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

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
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user.id


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


#JSON APIs to view AutoRepairCenter Information
@app.route('/autorepaircenter/<int:autorepaircenter_id>/container/JSON')
def AutorepairCentercenterContainerJSON(autorepaircenter_id):
    autorepaircenter = session.query(AutoRepairCenter).filter_by(id = autorepaircenter_id).one()
    items = session.query(ContainerItem).filter_by(autorepaircenter_id = autorepaircenter_id).all()
    return jsonify(ContainerItems=[i.serialize for i in items])


@app.route('/autorepaircenter/<int:autorepaircenter_id>/container/<int:container_id>/JSON')
def ContainerItemJSON(autorepaircenter_id, container_id):
    Container_Item = session.query(ContainerItem).filter_by(id = container_id).one()
    return jsonify(Container_Item = Container_Item.serialize)


@app.route('/autorepaircenter/JSON')
def AutoRepairCentercentersJSON():
    autorepaircenters = session.query(AutoRepairCenter).all()
    return jsonify(autorepaircenters= [r.serialize for r in autorepaircenters])


#Show all Autorepair centercenters
@app.route('/')
@app.route('/autorepaircenter/')
def showAutoRepairCenters():
    autorepaircenters = session.query(AutoRepairCenter).order_by(asc(AutoRepairCenter.name))
    if 'username' not in login_session:
        return render_template('publicautorepaircenters.html', autorepaircenters=autorepaircenters)
    else:
        return render_template('autorepaircenters.html', autorepaircenters=autorepaircenters)


#Create a new Autorepair centercenter
@app.route('/autorepaircenter/new/', methods=['GET', 'POST'])
def newAutoRepairCenter():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newAutoRepairCenter = AutoRepairCenter(name=request.form['name'], user_id=login_session['user_id'])
        session.add(newAutoRepairCenter)
        flash('New Auto Repair Center %s Successfully Created' % newAutoRepairCenter.name)
        session.commit()
        return redirect(url_for('showAutoRepairCenters'))
    else:
        return render_template('newautorepaircenter.html')


#Edit a Autorepair centercenter
@app.route('/autorepaircenter/<int:autorepaircenter_id>/edit/', methods = ['GET', 'POST'])
def editAutoRepairCenter(autorepaircenter_id):
    editedAutoRepairCenter = session.query(AutoRepairCenter).filter_by(id = autorepaircenter_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedAutoRepairCenter.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this autorepaircenter. Please create your own autorepaircenter in order to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedAutoRepairCenter.name = request.form['name']
            flash('AutoRepairCenter Successfully Edited %s' % editedAutoRepairCenter.name)
            return redirect(url_for('showAutoRepairCenters'))
        else:
            return render_template('editautorepaircenter.html', autorepaircenter = editedAutoRepairCenter)


#Delete a Autorepair centercenter
@app.route('/autorepaircenter/<int:autorepaircenter_id>/delete/', methods = ['GET','POST'])
def deleteAutoRepairCenter(autorepaircenter_id):
    autorepaircenterToDelete = session.query(AutoRepairCenter).filter_by(id = autorepaircenter_id).one()
    if 'username' not in login_session:
        return redirect('/login')
        if autorepaircenterToDelete.user_id != login_session['user_id']:
            return "<script>function myFunction() {alert('You are not authorized to delete this autorepaircenter. Please create your own autorepaircenter in order to delete.');}</script><body onload='myFunction()''>"
            if request.method == 'POST':
                session.delete(autorepaircenterToDelete)
                flash('%s Successfully Deleted' % autorepaircenterToDelete.name)
                session.commit()
                return redirect(url_for('showAutoRepairCenters', autorepaircenter_id = autorepaircenter_id))
            else:
                return render_template('deleteautorepaircenter.html',autorepaircenter = autorepaircenterToDelete)


#Show a Autorepair centercenter container
@app.route('/autorepaircenter/<int:autorepaircenter_id>/')
@app.route('/autorepaircenter/<int:autorepaircenter_id>/container/')
def showContainer(autorepaircenter_id):
    autorepaircenter = session.query(AutoRepairCenter).filter_by(id = autorepaircenter_id).one()
    creator = getUserInfo(autorepaircenter.user_id)
    items = session.query(ContainerItem).filter_by(autorepaircenter_id = autorepaircenter_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publiccontainer.html', items=items, autorepaircenter=autorepaircenter, creator=creator)
    else:
        return render_template('container.html', items = items, autorepaircenter = autorepaircenter, creator=creator)


#Create a new container Item
@app.route('/autorepaircenter/<int:autorepaircenter_id>/container/new/',methods=['GET','POST'])
def newContainerItem(autorepaircenter_id):
    if 'username' not in login_session:
        return redirect('/login')
        autorepaircenter = session.query(AutoRepairCenter).filter_by(id = autorepaircenter_id).one()
        if login_session['user_id'] != autorepaircenter.user_id:
            return "<script>function myFunction() {alert('You are not authorized to add container items to this Autocenter. Please create your own Autocenter in order to add items.');}</script><body onload='myFunction()''>"
            if request.method == 'POST':
                newItem = ContainerItem(name = request.form['name'], description = request.form['description'], price = request.form['price'], type = request.form['type'], autorepaircenter_id = autorepaircenter_id)
                session.add(newItem)
                session.commit()
                flash('New Container %s Item Successfully Created' % (newItem.name))
                return redirect(url_for('showContainer', autorepaircenter_id = autorepaircenter_id))
            else:
                return render_template('newcontaineritem.html', autorepaircenter_id = autorepaircenter_id)


#Edit a container Item
@app.route('/autorepaircenter/<int:autorepaircenter_id>/container/<int:container_id>/edit', methods=['GET','POST'])
def editContainerItem(autorepaircenter_id, container_id):
    if 'username' not in login_session:
        return redirect('/login')
        editedItem = session.query(ContainerItem).filter_by(id = container_id).one()
        autorepaircenter = session.query(AutoRepairCenter).filter_by(id = autorepaircenter_id).one()
        if login_session['user_id'] != autorepaircenter.user_id:
            return "<script>function myFunction() {alert('You are not authorized to edit Container items to this Autocenter. Please create your own Autocenter in order to edit items.');}</script><body onload='myFunction()''>"
            if request.method == 'POST':
                if request.form['name']:
                    editedItem.name = request.form['name']
                    if request.form['description']:
                        editedItem.description = request.form['description']
                        if request.form['price']:
                            editedItem.price = request.form['price']
                            if request.form['type']:
                                editedItem.type = request.form['type']
                                session.add(editedItem)
                                session.commit()
                                flash('Container Item Successfully Edited')
                                return redirect(url_for('showContainer', autorepaircenter_id = autorepaircenter_id))
                            else:
                                return render_template('editcontaineritem.html', autorepaircenter_id = autorepaircenter_id, container_id = container_id, item = editedItem)


#Delete a container Item
@app.route('/autorepaircenter/<int:autorepaircenter_id>/container/<int:container_id>/delete', methods = ['GET','POST'])
def deleteContainerItem(autorepaircenter_id,container_id):
    if 'username' not in login_session:
        return redirect('/login')
        autorepaircenter = session.query(AutoRepairCenter).filter_by(id = autorepaircenter_id).one()
        itemToDelete = session.query(ContainerItem).filter_by(id = container_id).one()
        if login_session['user_id'] != autorepaircenter.user_id:
            return "<script>function myFunction() {alert('You are not authorized to delete Container items to this Autocenter. Please create your own Autocenter in order to delete items.');}</script><body onload='myFunction()''>"
            if request.method == 'POST':
                session.delete(itemToDelete)
                session.commit()
                flash('Container Item Successfully Deleted')
                return redirect(url_for('showContainer', autorepaircenter_id = autorepaircenter_id))
            else:
                return render_template('deletecontaineritem.html', item = itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = 'localhost', port = 5000)

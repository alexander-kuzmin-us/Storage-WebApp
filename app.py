#!/usr/bin/env python3

# "Auto Repair Center" app is part of Udacity Full Stack Web Developer Nanodegree
from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   jsonify,
                   url_for,
                   flash,
                   session as login_session,
                   make_response)
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError
from database_setup import Base, AutoRepairCenter, ContainerItem, User
import random
import string
import json
import httplib2
import requests
import os
from functools import wraps
from werkzeug.exceptions import BadRequest
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

app = Flask(__name__)

# Load client secrets
CLIENT_SECRETS_FILE = 'client_secrets.json'
if os.path.exists(CLIENT_SECRETS_FILE):
    CLIENT_ID = json.loads(
        open(CLIENT_SECRETS_FILE, 'r').read())['web']['client_id']
else:
    CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')

APPLICATION_NAME = "Auto Repair Center"

# Connect to Database and create database session
engine = create_engine('sqlite:///autorepaircenter.db',
                       connect_args={'check_same_thread': False},
                       poolclass=StaticPool)
Base.metadata.bind = engine

# Create scoped session to ensure thread safety
session_factory = sessionmaker(bind=engine)
DBSession = scoped_session(session_factory)


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# User permissions check
def user_authorized(user_id):
    return 'user_id' in login_session and user_id == login_session['user_id']


# Create anti-forgery state token
@app.route('/login')
def show_login():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def g_connect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # Obtain authorization code
    try:
        code = request.data
    except BadRequest:
        response = make_response(json.dumps('Failed to read request data.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    except FileNotFoundError:
        response = make_response(
            json.dumps('Client secrets file not found.'), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    
    try:
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1].decode('utf-8'))
    except Exception as e:
        response = make_response(
            json.dumps(f'Failed to validate token: {str(e)}'), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    
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
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check if user is already connected
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    try:
        answer = requests.get(userinfo_url, params=params)
        data = answer.json()
    except Exception as e:
        response = make_response(
            json.dumps(f'Failed to get user info: {str(e)}'), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['username'] = data.get('name', '')
    login_session['picture'] = data.get('picture', '')
    login_session['email'] = data.get('email', '')

    # See if user exists, if it doesn't make a new one
    session = DBSession()
    try:
        user_id = get_user_id(login_session['email'], session)
        if not user_id:
            user_id = create_user(login_session, session)
        login_session['user_id'] = user_id
    except SQLAlchemyError as e:
        session.rollback()
        response = make_response(
            json.dumps(f'Database error: {str(e)}'), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    finally:
        session.close()

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; \
                height: 300px;border-radius: \
                150px;-webkit-border-radius: \
                150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    return output


# User Helper Functions
def create_user(login_session, session):
    new_user = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_user_info(user_id, session=None):
    if session is None:
        session = DBSession()
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user
    except SQLAlchemyError:
        return None
    finally:
        if session != DBSession():
            session.close()


def get_user_id(email, session=None):
    if session is None:
        session = DBSession()
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except SQLAlchemyError:
        return None
    finally:
        if session != DBSession():
            session.close()


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/g_disconnect')
def g_disconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        flash('Current user not connected.')
        return redirect(url_for('show_auto_repair_centers'))
    
    # Revoke token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    try:
        result = h.request(url, 'GET')[0]
    except Exception:
        flash('Failed to revoke token')
        
    # Clear session regardless of API revocation success
    for key in list(login_session.keys()):
        if key != 'state':
            login_session.pop(key)
    
    flash('Successfully logged out.')
    return redirect(url_for('show_auto_repair_centers'))


# JSON APIs to view AutoRepairCenter Information
@app.route('/api/autorepaircenters')
def autorepair_centers_json():
    session = DBSession()
    try:
        autorepaircenters = session.query(AutoRepairCenter).all()
        return jsonify(autorepaircenters=[r.serialize for r in autorepaircenters])
    except SQLAlchemyError:
        return jsonify(error="Database error"), 500
    finally:
        session.close()


@app.route('/api/autorepaircenters/<int:autorepaircenter_id>')
def autorepair_center_json(autorepaircenter_id):
    session = DBSession()
    try:
        autorepaircenter = session.query(AutoRepairCenter).filter_by(id=autorepaircenter_id).one()
        return jsonify(autorepaircenter=autorepaircenter.serialize)
    except SQLAlchemyError:
        return jsonify(error="Item not found or database error"), 404
    finally:
        session.close()


@app.route('/api/autorepaircenters/<int:autorepaircenter_id>/container')
def autorepair_center_container_json(autorepaircenter_id):
    session = DBSession()
    try:
        items = session.query(ContainerItem).filter_by(autorepaircenter_id=autorepaircenter_id).all()
        return jsonify(ContainerItems=[i.serialize for i in items])
    except SQLAlchemyError:
        return jsonify(error="Items not found or database error"), 404
    finally:
        session.close()


@app.route('/api/autorepaircenters/<int:autorepaircenter_id>/container/<int:container_id>')
def container_item_json(autorepaircenter_id, container_id):
    session = DBSession()
    try:
        container_item = session.query(ContainerItem).filter_by(
            id=container_id, autorepaircenter_id=autorepaircenter_id).one()
        return jsonify(Container_Item=container_item.serialize)
    except SQLAlchemyError:
        return jsonify(error="Item not found or database error"), 404
    finally:
        session.close()


# Show all Autorepair centers
@app.route('/')
@app.route('/autorepaircenters/')
def show_auto_repair_centers():
    session = DBSession()
    try:
        autorepaircenters = session.query(AutoRepairCenter).order_by(asc(AutoRepairCenter.name)).all()
        if 'username' not in login_session:
            return render_template(
                'publicautorepaircenters.html',
                autorepaircenters=autorepaircenters)
        else:
            return render_template(
                'autorepaircenters.html', 
                autorepaircenters=autorepaircenters)
    except SQLAlchemyError:
        flash("Error loading auto repair centers")
        return redirect(url_for('show_login'))
    finally:
        session.close()


# Create a new Autorepair center
@app.route('/autorepaircenters/new/', methods=['GET', 'POST'])
@login_required
def new_auto_repair_center():
    if request.method == 'POST':
        if not request.form.get('name'):
            flash('Please provide a name for the auto repair center')
            return render_template('new_auto_repair_center.html')
            
        session = DBSession()
        try:
            new_auto_repair_center = AutoRepairCenter(
                name=request.form['name'],
                user_id=login_session['user_id'])
            session.add(new_auto_repair_center)
            session.commit()
            flash(
                'New Auto Repair Center %s Successfully Created' %
                new_auto_repair_center.name)
            return redirect(url_for('show_auto_repair_centers'))
        except SQLAlchemyError:
            session.rollback()
            flash("Error creating new auto repair center")
            return render_template('new_auto_repair_center.html')
        finally:
            session.close()
    else:
        return render_template('new_auto_repair_center.html')


# Edit a Autorepair center
@app.route('/autorepaircenters/<int:autorepaircenter_id>/edit/',
           methods=['GET', 'POST'])
@login_required
def edit_auto_repair_center(autorepaircenter_id):
    session = DBSession()
    try:
        edited_auto_repair_center = session.query(
            AutoRepairCenter).filter_by(id=autorepaircenter_id).one()
        
        # Check if user is authorized
        if edited_auto_repair_center.user_id != login_session['user_id']:
            flash("You are not authorized to edit this auto repair center.")
            return redirect(url_for('show_auto_repair_centers'))
            
        if request.method == 'POST':
            if request.form.get('name'):
                edited_auto_repair_center.name = request.form['name']
                session.add(edited_auto_repair_center)
                session.commit()
                flash(
                    'Auto Repair Center Successfully Edited: %s' %
                    edited_auto_repair_center.name)
                return redirect(url_for('show_auto_repair_centers'))
            else:
                flash("Name is required")
        
        return render_template(
            'edit_auto_repair_center.html',
            autorepaircenter=edited_auto_repair_center)
    except SQLAlchemyError:
        session.rollback()
        flash("Error editing auto repair center")
        return redirect(url_for('show_auto_repair_centers'))
    finally:
        session.close()


# Delete a Autorepair center
@app.route('/autorepaircenters/<int:autorepaircenter_id>/delete/',
           methods=['GET', 'POST'])
@login_required
def delete_autorepair_center(autorepaircenter_id):
    session = DBSession()
    try:
        autorepaircenter_to_delete = session.query(
            AutoRepairCenter).filter_by(id=autorepaircenter_id).one()
        
        # Check if user is authorized
        if autorepaircenter_to_delete.user_id != login_session['user_id']:
            flash("You are not authorized to delete this auto repair center.")
            return redirect(url_for('show_auto_repair_centers'))
            
        if request.method == 'POST':
            session.delete(autorepaircenter_to_delete)
            session.commit()
            flash('%s Successfully Deleted' % autorepaircenter_to_delete.name)
            return redirect(url_for('show_auto_repair_centers'))
        else:
            return render_template(
                'delete_autorepair_center.html',
                autorepaircenter=autorepaircenter_to_delete)
    except SQLAlchemyError:
        session.rollback()
        flash("Error deleting auto repair center")
        return redirect(url_for('show_auto_repair_centers'))
    finally:
        session.close()


# Show a Autorepair center container
@app.route('/autorepaircenters/<int:autorepaircenter_id>/')
@app.route('/autorepaircenters/<int:autorepaircenter_id>/container/')
def show_container(autorepaircenter_id):
    session = DBSession()
    try:
        autorepaircenter = session.query(
            AutoRepairCenter).filter_by(id=autorepaircenter_id).one()
        creator = get_user_info(autorepaircenter.user_id, session)
        items = session.query(ContainerItem).filter_by(
            autorepaircenter_id=autorepaircenter_id).all()
        
        if ('username' not in login_session or 
                creator is None or 
                creator.id != login_session.get('user_id')):
            return render_template(
                'publiccontainer.html',
                items=items,
                autorepaircenter=autorepaircenter,
                creator=creator)
        else:
            return render_template(
                'container.html', 
                items=items, 
                autorepaircenter=autorepaircenter,
                creator=creator)
    except SQLAlchemyError:
        flash("Error loading auto repair center")
        return redirect(url_for('show_auto_repair_centers'))
    finally:
        session.close()


# Create a new container Item
@app.route('/autorepaircenters/<int:autorepaircenter_id>/container/new/',
           methods=['GET', 'POST'])
@login_required
def new_container_item(autorepaircenter_id):
    session = DBSession()
    try:
        autorepaircenter = session.query(
            AutoRepairCenter).filter_by(id=autorepaircenter_id).one()
            
        # Check if user is authorized
        if login_session['user_id'] != autorepaircenter.user_id:
            flash("You are not authorized to add items to this auto repair center.")
            return redirect(url_for('show_container', autorepaircenter_id=autorepaircenter_id))
            
        if request.method == 'POST':
            if not request.form.get('name'):
                flash('Please provide a name for the container item')
                return render_template(
                    'new_container_item.html', autorepaircenter_id=autorepaircenter_id)
                
            name = request.form.get('name', '')
            description = request.form.get('description', '')
            price = request.form.get('price', '')
            item_type = request.form.get('type', 'Body')
            
            new_item = ContainerItem(
                name=name, 
                description=description,
                price=price, 
                type=item_type,
                autorepaircenter_id=autorepaircenter_id,
                user_id=login_session['user_id'])
            session.add(new_item)
            session.commit()
            flash('New Container Item %s Successfully Created' % new_item.name)
            return redirect(url_for(
                'show_container', autorepaircenter_id=autorepaircenter_id))
        else:
            return render_template(
                'new_container_item.html', autorepaircenter_id=autorepaircenter_id)
    except SQLAlchemyError:
        session.rollback()
        flash("Error creating container item")
        return redirect(url_for('show_container', autorepaircenter_id=autorepaircenter_id))
    finally:
        session.close()


# Edit a container Item
@app.route('/autorepaircenters/<int:autorepaircenter_id>/container/<int:container_id>/edit',
           methods=['GET', 'POST'])
@login_required
def edit_container_item(autorepaircenter_id, container_id):
    session = DBSession()
    try:
        autorepaircenter = session.query(
            AutoRepairCenter).filter_by(id=autorepaircenter_id).one()
        edited_item = session.query(ContainerItem).filter_by(
            id=container_id, autorepaircenter_id=autorepaircenter_id).one()
            
        # Check if user is authorized
        if login_session['user_id'] != autorepaircenter.user_id:
            flash("You are not authorized to edit items in this auto repair center.")
            return redirect(url_for('show_container', autorepaircenter_id=autorepaircenter_id))
            
        if request.method == 'POST':
            if request.form.get('name'):
                edited_item.name = request.form['name']
            if request.form.get('description'):
                edited_item.description = request.form['description']
            if request.form.get('price'):
                edited_item.price = request.form['price']
            if request.form.get('type'):
                edited_item.type = request.form['type']
                
            session.add(edited_item)
            session.commit()
            flash('Container Item Successfully Edited')
            return redirect(url_for(
                'show_container', autorepaircenter_id=autorepaircenter_id))
        else:
            return render_template(
                'edit_container_item.html', 
                autorepaircenter_id=autorepaircenter_id,
                container_id=container_id, 
                item=edited_item)
    except SQLAlchemyError:
        session.rollback()
        flash("Error editing container item")
        return redirect(url_for('show_container', autorepaircenter_id=autorepaircenter_id))
    finally:
        session.close()


# Delete a container Item
@app.route('/autorepaircenters/<int:autorepaircenter_id>/container/<int:container_id>/delete',
           methods=['GET', 'POST'])
@login_required
def delete_container_item(autorepaircenter_id, container_id):
    session = DBSession()
    try:
        autorepaircenter = session.query(
            AutoRepairCenter).filter_by(id=autorepaircenter_id).one()
        item_to_delete = session.query(
            ContainerItem).filter_by(
                id=container_id, autorepaircenter_id=autorepaircenter_id).one()
                
        # Check if user is authorized
        if login_session['user_id'] != autorepaircenter.user_id:
            flash("You are not authorized to delete items from this auto repair center.")
            return redirect(url_for('show_container', autorepaircenter_id=autorepaircenter_id))
            
        if request.method == 'POST':
            session.delete(item_to_delete)
            session.commit()
            flash('Container Item Successfully Deleted')
            return redirect(url_for(
                'show_container', autorepaircenter_id=autorepaircenter_id))
        else:
            return render_template('delete_container_item.html', item=item_to_delete)
    except SQLAlchemyError:
        session.rollback()
        flash("Error deleting container item")
        return redirect(url_for('show_container', autorepaircenter_id=autorepaircenter_id))
    finally:
        session.close()


if __name__ == '__main__':
    app.secret_key = os.environ.get(
        'SECRET_KEY',
        ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32)))
    app.debug = False
    app.run(host='localhost', port=5000)

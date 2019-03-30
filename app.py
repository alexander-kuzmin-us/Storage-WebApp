from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app=Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Storage, ContainerItem

#Connect to Database and create database session
engine = create_engine('sqlite:///storage.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def login():
    return render_template ("login.html")

@app.route('/about/')
def about():
    return render_template ("about.html")

#Show all Storages
@app.route('/')
@app.route('/storage/')
def showstorages():
    storages = session.query(Storage).order_by(asc(Storage.name))
    return render_template("storages.html", storages = storages)

#Create a new Storage
@app.route('/storage/new', methods=['GET','POST'])
def newstorage():
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
def editstorage(storage_id):
    editstorage = session.query(Storage).filter_by(id = storage_id).one()
    if request.method == 'POST':
      if request.form['name']:
        editstorage.name = request.form['name']
        flash('Storage Successfully Edited %s' % editstorage.name)
        return redirect(url_for('showstorages'))
    else:
    return render_template("editstorage.html")

#Delete a Storage
@app.route('/storage/delete')
def deletestorage():
    return render_template("deletestorage.html")

#Show a Storage container
@app.route('/storage/')
@app.route('/storage/container')
def showContainer():
    return render_template("container.html")

#Create a new item in the container
@app.route('/storage/container/new')
def newContainerItem():
    return render_template("newcontaineritem.html")

#Edit an item in the container
@app.route('/storage/container/edit')
def editContainerItem():
    return render_template("editcontaineritem.html")


#Delete an item in the container
@app.route('/storage/container/delete')
def deleteContainerItem():
    return render_template("deletecontaineritem.html")


if __name__=="__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, AutoRepairCenter, ContainerItem


app = Flask(__name__)


#Connect to Database and create database session
engine = create_engine('sqlite:///autorepaircenter.db')
Base.metadata.bind = engine


DBSession = sessionmaker(bind=engine)
session = DBSession()


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
    return render_template('autorepaircenters.html', autorepaircenters = autorepaircenters)

#Create a new Autorepair centercenter
@app.route('/autorepaircenter/new/', methods=['GET','POST'])
def newAutoRepairCenter():
    if request.method == 'POST':
      newAutoRepairCenter = AutoRepairCenter(name = request.form['name'])
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
    items = session.query(ContainerItem).filter_by(autorepaircenter_id = autorepaircenter_id).all()
    return render_template('container.html', items = items, autorepaircenter = autorepaircenter)



#Create a new container Item
@app.route('/autorepaircenter/<int:autorepaircenter_id>/container/new/',methods=['GET','POST'])
def newContainerItem(autorepaircenter_id):
  autorepaircenter = session.query(AutoRepairCenter).filter_by(id = autorepaircenter_id).one()
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

    editedItem = session.query(ContainerItem).filter_by(id = container_id).one()
    autorepaircenter = session.query(AutoRepairCenter).filter_by(id = autorepaircenter_id).one()
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
    autorepaircenter = session.query(AutoRepairCenter).filter_by(id = autorepaircenter_id).one()
    itemToDelete = session.query(ContainerItem).filter_by(id = container_id).one()
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
  app.run(host = '0.0.0.0', port = 5000)

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

appCatalog = Flask(__name__)
import cgi
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, aliased
from database_setup import Base, CategoryTable, ItemTable
from werkzeug import secure_filename
#Import all the necesary files and clases for authentication
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

from flask import session as login_session
import random, string

appCatalog.config['SESSION_TYPE'] = 'filesystem'
CLIENT_ID = json.loads(open('client_secret.json','r').read())['web']['client_id']
engine = create_engine ('sqlite:///ItemCatalog.db')
Base.metadata.bind = engine
UPLOAD_FOLDER = 'static/uploads'
appCatalog.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DBSession = sessionmaker(bind=engine)
session = DBSession()

#Methods and views related to the user authentication.
@appCatalog.route('/gconnect',methods=['POST'])
def gconnect():
	#Gconnect function for linking the gmail account with the user session
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'),401)
		response.headers['Content-Type'] = 'application/json'
		return response
	code = request.data
	try:
		oauth_flow = flow_from_clientsecrets('client_secret.json',scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(json.dumps('Failed to upgrade the authorization code.'),401)
		response.headers['Content-Type'] = 'application/json'
		return response
	#Get the tokens for the current session
	token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'%token)
	h = httplib2.Http()
	#Get the result of the google api
	result = json.loads(h.request(url, 'GET')[1])

	#If there was an error in the access token info, kill it.
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 501)
		response.headers['Content-Type'] = 'application/json'
	#Verify that the access token is used for the intended user
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(json.dumps('Token user Id doesn\'t match given user ID'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	#Store the access token in the session for later use.
	login_session['credentials'] = credentials
	login_session['gplus_id'] = gplus_id

	#Get user info
	userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
	params = {'access_token':credentials.access_token, 'alt':'json'}
	answer = requests.get(userinfo_url, params=params)
	data = json.loads(answer.text)
	login_session['name'] = data['name']
	login_session['picture'] = data['picture']
	response = ''
	response += 'Connecting....'
	#flash('Welcome %s'%login_session['name'])
	return response

@appCatalog.route('/gdisconnect')
def gdisconnect():
	#Only disconnect a connected user
	credentials = login_session.get('credentials')
	if credentials is None:
		response = make_response(json.dumps('Current user is not connected.'),401)
		response.headers['Content-Type'] = 'application/json'
		return response
	#Execute Get HTTP request to revoke current token
	access_token = credentials.access_token
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s'%access_token
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
	#If succes delete al login session variables
	print result
	if result['status'] == '200':
		del login_session['credentials']
		del login_session['gplus_id']
		del login_session['name']
		del login_session['picture']

		response = make_response(json.dumps('Succesfully disconnected!.'))
		response.headers['Content-Type'] = 'application/json'
		return redirect('/')

	return 'Response status: '+result['status']

@appCatalog.route('/')
@appCatalog.route('/login')
def showLogin():
	"""Login view"""
	#First create the corresponding state for the login session.
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
	login_session['state'] = state
	sports_items = session.query(CategoryTable.name,CategoryTable.id,ItemTable.name).join(ItemTable.category).group_by(CategoryTable.id).order_by(CategoryTable.name).all()

	sport_list = []
	for sport in sports_items:
		sport_list.append({'name':str(sport[0]),'idcategory':sport[1],'item':sport[2]})
	#Get all categories and get the latest item.
	return render_template('home.html',sport_list=sport_list,item_title='Latest Items',buttons_rows=False,STATE=state)


@appCatalog.route('/home')
def home():
	sports_items = session.query(CategoryTable.name,CategoryTable.id,ItemTable.name).join(ItemTable.category).group_by(CategoryTable.id).order_by(CategoryTable.name).all()
	if 'name' not in login_session:
		return redirect('/')

	name = login_session['name']
	image = login_session['picture']
	sport_list = []
	for sport in sports_items:
		sport_list.append({'name':str(sport[0]),'idcategory':sport[1],'item':sport[2]})
	print login_session
	
	return render_template('home.html',sport_list=sport_list,item_title='Latest Items',buttons_rows=True,username=name,image=image)

@appCatalog.route('/filter-items/<int:idcategory>')
def filterItem(idcategory):
	sport_items = session.query(CategoryTable.name,ItemTable.id,ItemTable.name).join(ItemTable.category).filter(CategoryTable.id == idcategory).all()
	test = session.query(CategoryTable).all()
	items_list = []
	name = ''
	image = ''
	show_rows = True
	if 'name' not in login_session:
		show_rows = False
	else:
		name = login_session['name']
		image = login_session['picture']

	for item in sport_items:
		category_name = item[0]
		items_list.append({'category_name':str(item[0]),'id_item':item[1],'item_name':item[2]})
	info = "In this section you can view all items related to a specific category. Also you can "
	info += "filter results in the text field by typing the item's name."

	return render_template('items-by-category.html',items_list=items_list,category_name=category_name,info=info, show_rows=show_rows, username=name, image=image)

@appCatalog.route('/add-item')
def addItem():
	sports = session.query(CategoryTable).all()
	sport_list = []
	if 'name' not in login_session:
		return redirect('/')

	name = login_session['name']
	image = login_session['picture']
	info = "Here you can create new items, with a description and asociate them to a specific category."
	for sport in sports:
		sport_list.append({'name':str(sport.name),'id':sport.id})
	return render_template('create-item.html',sport_list=sport_list, info=info, username=name, image=image)

@appCatalog.route('/edit-item/<int:iditem>')
def editItem(iditem):
	model = session.query(ItemTable).filter(ItemTable.id == iditem).one()
	sports = session.query(CategoryTable).all()
	info = "Here you can edit the selected item, also the description and the category asociated with it."
	if 'name' not in login_session:
		return redirect('/')

	name = login_session['name']
	image = login_session['picture']
	sport_list = []
	item_model = []
	for sport in sports:
		sport_list.append({'name':str(sport.name),'id':sport.id})

	item_model.append({'name':model.name, 'id':iditem,'category':model.category_id,'image':model.image,'description':model.description,'sport_list':sport_list})

	return render_template('update-item.html',item_model=item_model, info=info, username=name, image=image)

@appCatalog.route('/update-item/<int:iditem>',methods=['GET','POST'])
def updateItem(iditem):
	
	if request.method=='POST':
		item_name = request.form['item_name']
		id_c = request.form['category']
		description = request.form['description']
		image = request.files['item-image']
		current_item = session.query(ItemTable).filter(ItemTable.id == iditem).one()
		current_item.name = item_name
		current_item.category_id = id_c
		current_item.description = description
		filename = secure_filename(image.filename)
		if filename!='':
			current_item.image = UPLOAD_FOLDER+'/'+filename
			image.save(os.path.join(appCatalog.config['UPLOAD_FOLDER'], filename))
		session.add(current_item)
		session.commit()
	return redirect('home')

@appCatalog.route('/add-category')
def addCategory():
	if 'name' not in login_session:
		return redirect('/')

	name = login_session['name']
	image = login_session['picture']
	info = "In this section you'll be able to create a new category."
	return render_template('create-category.html',info=info, username=name, image=image)

@appCatalog.route('/insert-item',methods=['GET','POST'])
def createItem():

	if request.method=='POST':
		item_name = request.form['item_name']
		id_c = request.form['category']
		description = request.form['description']
		image = request.files['item-image']
		filename = secure_filename(image.filename)
		image.save(os.path.join(appCatalog.config['UPLOAD_FOLDER'], filename))
		new_item = ItemTable(name=item_name, category_id=id_c, description=description, image= UPLOAD_FOLDER+'/'+filename)
		session.add(new_item)
		session.commit()
	sports = session.query(CategoryTable).all()
	sport_list = []
	for sport in sports:
		sport_list.append({'name':str(sport.name),'id':sport.id})
	return redirect('home')

@appCatalog.route('/insert-category',methods=['GET','POST'])
def createCategory():
	
	if request.method=='POST':
		category_name = request.form['category_name']
		new_category = CategoryTable(name=category_name)
		session.add(new_category)
		session.commit()
	return redirect('home')

@appCatalog.route('/remove-item/<int:iditem>',methods=['GET','POST'])
def removeItem(iditem):
	if 'name' not in login_session:
		return redirect('/')

	item = session.query(ItemTable).filter_by( id = iditem ).one()
	session.delete(item)
	session.commit()
	return redirect('home')

@appCatalog.route('/view-item/<int:iditem>')
def viewItem(iditem):
	info = "Here you can view the information about the item."
	model = session.query(ItemTable).filter(ItemTable.id == iditem).one()
	sports = session.query(CategoryTable).all()
	show_user = True
	name = ''
	image = ''

	if 'name' not in login_session:
		show_user = False
	else:
		name = login_session['name']
		image = login_session['picture']

	category = ''
	item_model = []
	for sport in sports:
		if sport.id==model.category_id:
			category = str(sport.name)

	item_model.append({'name':model.name, 'id':iditem,'category':category, 'description':model.description, 'image':model.image})
	return render_template('view-item.html',item_model=item_model, info = info, show_user=show_user, username=name, image=image)

if __name__=='__main__':
	appCatalog.debug = True;
	appCatalog.secret_key = 'JsBwnLvJQPsopQ0UN6Zkf9Av'
	appCatalog.run(host='0.0.0.0',port = 8000)

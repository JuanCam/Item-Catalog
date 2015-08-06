from flask import Flask, render_template, request, redirect, url_for
appCatalog = Flask(__name__)
import cgi
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, aliased
from database_setup import Base, CategoryTable, ItemTable

engine = create_engine ('sqlite:///ItemCatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
@appCatalog.route('/')
@appCatalog.route('/home')
def home():
	sports_items = session.query(CategoryTable.name,CategoryTable.id,ItemTable.name).join(ItemTable.category).group_by(CategoryTable.id).order_by(CategoryTable.name).all()

	sport_list = []
	for sport in sports_items:
		print sport[0]
		sport_list.append({'name':str(sport[0]),'idcategory':sport[1],'item':sport[2]})
		#
	return render_template('home.html',sport_list=sport_list,item_title='Latest Items')

@appCatalog.route('/filter-items/<int:idcategory>')
def filterItem(idcategory):
	sport_items = session.query(CategoryTable.name,ItemTable.id,ItemTable.name).join(ItemTable.category).filter(CategoryTable.id == idcategory).all()
	test = session.query(CategoryTable).all()
	items_list = []

	for item in sport_items:
		category_name = item[0]
		items_list.append({'category_name':str(item[0]),'id_item':item[1],'item_name':item[2]})
		
	return render_template('items-by-category.html',items_list=items_list,category_name=category_name)

@appCatalog.route('/add-item')
def addItem():
	sports = session.query(CategoryTable).all()
	sport_list = []
	for sport in sports:
		sport_list.append({'name':str(sport.name),'id':sport.id})
	return render_template('create-item.html',sport_list=sport_list)

@appCatalog.route('/edit-item/<int:iditem>')
def editItem(iditem):
	model = session.query(ItemTable).filter(ItemTable.id == iditem).one()
	sports = session.query(CategoryTable).all()

	sport_list = []
	item_model = []
	for sport in sports:
		sport_list.append({'name':str(sport.name),'id':sport.id})

	item_model.append({'name':model.name, 'id':iditem,'category':model.category_id,'description':model.description,'sport_list':sport_list})

	return render_template('update-item.html',item_model=item_model)

@appCatalog.route('/update-item/<int:iditem>',methods=['GET','POST'])
def updateItem(iditem):
	
	if request.method=='POST':
		item_name = request.form['item_name']
		id_c = request.form['category']
		description = request.form['description']
		current_item = session.query(ItemTable).filter(ItemTable.id == iditem).one()
		current_item.name = item_name
		current_item.category_id = id_c
		current_item.description = description
		session.add(current_item)
		session.commit()
	return redirect('home')

@appCatalog.route('/add-category')
def addCategory():
	return render_template('create-category.html')

@appCatalog.route('/insert-item',methods=['GET','POST'])
def createItem():
	
	if request.method=='POST':
		item_name = request.form['item_name']
		id_c = request.form['category']
		description = request.form['description']
		new_item = ItemTable(name=item_name, category_id=id_c, description=description)
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

	item = session.query(ItemTable).filter_by( id = iditem ).one()
	session.delete(item)
	session.commit()
	return redirect('home')

@appCatalog.route('/view-item/<int:iditem>')
def viewItem(iditem):
	model = session.query(ItemTable).filter(ItemTable.id == iditem).one()
	sports = session.query(CategoryTable).all()

	category = ''
	item_model = []
	for sport in sports:
		if sport.id==model.category_id:
			category = str(sport.name)

	item_model.append({'name':model.name, 'id':iditem,'category':category, 'description':model.description})


	return render_template('view-item.html',item_model=item_model)
if __name__=='__main__':
	appCatalog.debug = True;
	appCatalog.run(host='0.0.0.0',port = 8000)
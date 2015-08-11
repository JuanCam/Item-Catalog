# Catalog application for working with the CRUD of the Items and Categories
# as long as the user is logged in.
# Developed by : Juan Camilo Gutierrez Ruiz - 10/August/2015
import os
import httplib2
import json
import requests
import random
import string
from flask import Flask, render_template, request, redirect, url_for, flash, \
	jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, aliased
from database_setup import Base, CategoryTable, ItemTable
from werkzeug import secure_filename
# Import all the necesary files and clases for authentication
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import make_response
from flask import session as login_session


appCatalog = Flask(__name__)


appCatalog.config['SESSION_TYPE'] = 'filesystem'
CLIENT_ID = json.loads(open('client_secret.json',
                            'r').read())['web']['client_id']


# Declaration of the Flask app.
appCatalog = Flask(__name__)

appCatalog.config['SESSION_TYPE'] = 'filesystem'
CLIENT_ID = json.loads(open('client_secret.json',
                            'r').read())['web']['client_id']
engine = create_engine('sqlite:///ItemCatalog.db')
Base.metadata.bind = engine
UPLOAD_FOLDER = 'static/uploads'
appCatalog.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Methods and views related to the user authentication.
@appCatalog.route('/gconnect', methods=['POST'])
def gconnect():
    """function for linking the gmail account with the user session"""
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the '
                                            'authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Get the tokens for the current session
    token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % token)
    h = httplib2.Http()
    # Get the result of the google api
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, kill it.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 501)
        response.headers['Content-Type'] = 'application/json'
    # Verify that the access token is used for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps('Token user Id doesn\'t '
                                            'match given user ID'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = json.loads(answer.text)

    login_session['name'] = data['name']
    login_session['picture'] = data['picture']
    response = ''
    response += 'Connecting....'
    return response


@appCatalog.route('/gdisconnect')
def gdisconnect():
    """Disconnect a gmail connected user"""
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user is not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Execute Get HTTP request to revoke current token
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s'\
          % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    # If succes delete al login session variables

    if result['status'] == '200':
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['name']
        del login_session['picture']

        response = make_response(json.dumps('Succesfully disconnected!.'))
        response.headers['Content-Type'] = 'application/json'
        return redirect('/')

    return 'Response status: '+result['status']


# Root and login decorators
@appCatalog.route('/')
@appCatalog.route('/login')
def showLogin():
    """This method corresponds to the Login view - public"""

    # First create the corresponding state for the login session.
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state

    # Gets all the categories with the latest item.
    sports_items = session.query(CategoryTable.name, CategoryTable.id,
                                 ItemTable.name).\
        join(ItemTable.category).\
        group_by(CategoryTable.id).\
        order_by(CategoryTable.name).all()
    sport_list = []
    # Build the Category or Sport list for the template
    for sport in sports_items:
        sport_list.append({'name': str(sport[0]),
                           'idcategory': sport[1],
                           'item': sport[2]})

    # Flag variable button_rows shows or hide the Create Item/Category buttons.
    return render_template('home.html',
                           sport_list=sport_list,
                           item_title='Latest Items',
                           buttons_rows=False,
                           STATE=state)


@appCatalog.route('/home')
def home():
    """This method for the home view once a user is logged in. - not public"""

    # Gets all the categories with the latest item.
    sports_items = session.query(CategoryTable.name,
                                 CategoryTable.id, ItemTable.name).\
        join(ItemTable.category).\
        group_by(CategoryTable.id).\
        order_by(CategoryTable.name).all()
    # Protect the page
    if 'name' not in login_session:
        return redirect('/')

    name = login_session['name']
    image = login_session['picture']
    sport_list = []
    # Build the Category or Sport list for the template
    for sport in sports_items:
        sport_list.append({'name': str(sport[0]),
                           'idcategory': sport[1],
                           'item': sport[2]})

    # Flag variable button_rows shows or hide the Create Item/Category buttons.
    return render_template('home.html',
                           sport_list=sport_list,
                           item_title='Latest Items',
                           buttons_rows=True,
                           username=name,
                           image=image)


@appCatalog.route('/filter-items/<int:idcategory>')
def filterItem(idcategory):
    """This method renders the items-per-category view. - public
    Arguments: idcategory - Is the id of the selected category"""

    # Select all the items related to the selected category
    sport_items = session.query(CategoryTable.name,
                                ItemTable.id, ItemTable.name).\
        join(ItemTable.category).\
        filter(CategoryTable.id == idcategory).all()
    # List for appending each item and then render them
    items_list = []
    # Variables for the user info.
    name = ''
    image = ''
    # Flag for showing the edit/delete options.
    show_rows = True

    if 'name' not in login_session:
        show_rows = False
    else:
        name = login_session['name']
        image = login_session['picture']

    for item in sport_items:
        category_name = item[0]
        items_list.append({'category_name': str(item[0]),
                           'id_item': item[1],
                           'item_name': item[2]})
    # Info of the intro text in the HTML tamplate.
    info = "In this section you can view all items related to a specific " \
           "category. Also you can filter results in the text field by"\
           "typing the item's name."

    return render_template('items-by-category.html',
                           items_list=items_list,
                           category_name=category_name,
                           id_category=idcategory,
                           info=info,
                           show_rows=show_rows,
                           username=name,
                           image=image)


@appCatalog.route('/add-item')
def addItem():
    """This is the create item view - not public"""

    # Get the Current Categories, this is for constructing the select menu.
    sports = session.query(CategoryTable).all()
    sport_list = []
    if 'name' not in login_session:
        return redirect('/')

    name = login_session['name']
    image = login_session['picture']
    info = "Here you can create new items, with a description and" \
           "asociate them to a specific category."
    for sport in sports:
        sport_list.append({'name': str(sport.name),
                           'id': sport.id})
    return render_template('create-item.html',
                           sport_list=sport_list,
                           info=info,
                           username=name,
                           image=image)


@appCatalog.route('/edit-item/<int:iditem>')
def editItem(iditem):
    """Edit Item view, it allows the user to change
    the item information - not public
    Arguments : iditem - Corresponds to the id of the selected item"""

    # Get the item
    model = session.query(ItemTable).filter(ItemTable.id == iditem).one()
    sports = session.query(CategoryTable).all()
    info = "Here you can edit the selected item, also the description " \
           "and the category asociated with it."
    if 'name' not in login_session:
        return redirect('/')

    name = login_session['name']
    image = login_session['picture']
    sport_list = []
    item_model = []
    # Construct the Category list.
    for sport in sports:
        sport_list.append({'name': str(sport.name), 'id': sport.id})

    item_model.append({'name': model.name,
                       'id': iditem,
                       'category': model.category_id,
                       'image': model.image,
                       'description': model.description,
                       'sport_list': sport_list})

    return render_template('update-item.html',
                           item_model=item_model,
                           info=info,
                           username=name,
                           image=image)


@appCatalog.route('/update-item/<int:iditem>', methods=['GET', 'POST'])
def updateItem(iditem):
    """Update Item view action
    Arguments : iditem - is the id of the edited item"""

    # if the request method is post perform the update in the specific row
    if request.method == 'POST':
        item_name = request.form['item_name']
        id_c = request.form['category']
        description = request.form['description']
        image = request.files['item-image']
        current_item = session.query(ItemTable).\
            filter(ItemTable.id == iditem).one()
        current_item.name = item_name
        current_item.category_id = id_c
        current_item.description = description

        # Loads an image for the Item
        filename = secure_filename(image.filename)
        if filename != '':
            current_item.image = UPLOAD_FOLDER+'/'+filename
            # Save the image in the server
            image.save(os.path.join(appCatalog.config['UPLOAD_FOLDER'],
                                    filename))
        session.add(current_item)
        session.commit()

    return redirect('home')


@appCatalog.route('/add-category')
def addCategory():
    """View for creating a new category - not public"""
    if 'name' not in login_session:
        return redirect('/')

    name = login_session['name']
    image = login_session['picture']
    info = "In this section you'll be able to create a new category."
    return render_template('create-category.html',
                           info=info,
                           username=name,
                           image=image)


@appCatalog.route('/insert-item', methods=['GET', 'POST'])
def createItem():
    """View for creating a new Item"""
    if request.method == 'POST':
        item_name = request.form['item_name']
        id_c = request.form['category']
        description = request.form['description']
        image = request.files['item-image']
        filename = secure_filename(image.filename)

        if filename != '':
            # Save the image in the server if the filename is not empty.
            image.save(os.path.join(appCatalog.config['UPLOAD_FOLDER'],
                                    filename))
        new_item = ItemTable(name=item_name,
                             category_id=id_c,
                             description=description,
                             image=UPLOAD_FOLDER+'/'+filename)
        session.add(new_item)
        session.commit()
    return redirect('home')


@appCatalog.route('/insert-category', methods=['GET', 'POST'])
def createCategory():
    """Create Category action"""
    if request.method == 'POST':
        category_name = request.form['category_name']
        new_category = CategoryTable(name=category_name)
        session.add(new_category)
        session.commit()
    return redirect('home')


@appCatalog.route('/remove-item/<int:iditem>', methods=['GET', 'POST'])
def removeItem(iditem):
    """Delete the specific item
    Arguments : iditem - is the id of item that will be removed"""
    if 'name' not in login_session:
        return redirect('/')

    item = session.query(ItemTable).filter_by(id=iditem).one()
    session.delete(item)
    session.commit()
    return redirect('home')


@appCatalog.route('/view-item/<int:iditem>')
def viewItem(iditem):
    """Item General View - public
    Arguments: iditem - is the id of the selected item"""

    info = "Here you can view the information about the item."
    # Gets the specific information of the selected item.
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
        if sport.id == model.category_id:
            category = str(sport.name)

    item_model.append({'name': model.name,
                       'id': iditem,
                       'category': category,
                       'description': model.description,
                       'image': model.image})

    return render_template('view-item.html',
                           item_model=item_model,
                           info=info,
                           show_user=show_user,
                           username=name,
                           image=image)


@appCatalog.route('/filter-items/JSON')
def homeJSON():
    """Shows the JSON Format for all the items of a category"""

    sports = session.query(CategoryTable).all()
    JSON_export = []

    for sport in sports:
        sports_items = session.query(ItemTable).\
            filter_by(category_id=int(sport.id)).all()
        JSON_export.append({sport.name: [s.serial for s in sports_items]})

    return jsonify(Categories=JSON_export)

if __name__ == '__main__':
    appCatalog.debug = True
    appCatalog.secret_key = 'JsBwnLvJQPsopQ0UN6Zkf9Av'
    appCatalog.run(host='0.0.0.0', port=8000)

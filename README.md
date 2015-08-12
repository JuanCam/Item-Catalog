<h1>Item Catalog Website - Version 1.0 11/08/2015</h1>

GENERAL USAGE NOTES
-------------------

-First of all, for using this webiste follow this steps:<br>
*Install Vagrant and VirtualBox.<br>
*Clone the fullstack-nanodegree-vm.<br>
*Launch the Vagrant VM (vagrant up).<br>
*Upgrade Flask to Flask0.9v by typing pip install flask==0.9
*Download or clone this project (Item-Catalog) inside the vagrant folder.<br>
*Change directory to the project folder: first run the database_setup.py file (python database_setup.py) and then run the application within the VM (python catalog_app.py)<br>
*Access and test your application by visiting http://localhost:8000 locally, note the application will only run in the 8000 port.<br>
-The Item Catalog application consists of a list of sport items grouped by sports, you can view the specific information about the item, the category it belongs to and its corresponding image.<br>
-This application si divided into 2 modules.<br>
-The first one is for unregistered users who can view all the information about the items (Including a JSON file with the information of items per category), filter them by their names and the categories, but they cannot handle the CRUD.<br>
-The second one is for registered users who has the same permissions of the unregistered users, but besides that, they can handle the CRUD, by creating items and categories, editing items by clicking the pencil in the item-filtered by category view and deleting them in this same view (can log in with your gmail account).<br></br>
-Populate the database and enjoy this site.</br>

PULLING REQUEST
------------------
You can clone the project with this url https://github.com/JuanCam/Item-Catalog
feel free to improve the project and push your changes

CONTACT INFO
------------------
Author : Juan Camilo Gutierrez Ruiz<br>
Voice : 6262751<br>
Website : www.juan-latino.com<br>
e-mail : juacgr_4@hotmail.com<br>

Copyright 2015 Juan Corporation All rights reserved.
Item Catalog application and its use are subject to license agreement and are also subject to copyright trademark/pattent and/or other laws. 

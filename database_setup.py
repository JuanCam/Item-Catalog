# Database built on sqlalchemy that holds Items and Categories related to this items
# Developed by : Juan Camilo Gutierrez Ruiz - 20/July/2015
import os
import sys
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

#Table for the categories
class CategoryTable(Base):
	__tablename__= 'Category'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
# Table for the items
class ItemTable(Base):

	__tablename__ = 'Item'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=True)
	description = Column(String(1000), nullable=True)
	image = Column(String(250), nullable=False)
	category_id =Column(Integer, ForeignKey('Category.id'))
	category = relationship(CategoryTable)
	# Property which later will be used in the jsonify view.
	@property
	def serial(self):
		return{
		'name':self.name,
		'description':self.description,
		}

engine = create_engine('sqlite:///ItemCatalog.db')
Base.metadata.create_all(engine)
import os
import sys
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class CategoryTable(Base):
	__tablename__= 'Category'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)

class ItemTable(Base):
	__tablename__ = 'Item'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=True)
	description = Column(String(1000), nullable=True)
	image = Column(String(250), nullable=False)
	category_id =Column(Integer, ForeignKey('Category.id'))
	category = relationship(CategoryTable)

engine = create_engine('sqlite:///ItemCatalog.db')
Base.metadata.create_all(engine)
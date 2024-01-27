import json
import os
from pydantic import BaseModel, validator, ValidationError
from typing import Optional
from sqlalchemy import create_engine, text, Column, Integer, String, MetaData, Table, Sequence, or_, and_
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session
import difflib

db_username = os.environ.get('db_username')
db_password = os.environ.get('db_password')
db_host = os.environ.get('db_host')
db_port = os.environ.get('db_port')
db_name = os.environ.get('db_name')
db_table_name = os.environ.get('db_table_name')
similarity_threshold = os.environ.get('similarity_threshold', 0.4)

new_db_connection_string = f"mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
new_db_engine = create_engine(new_db_connection_string)

Base = declarative_base()
session = Session(bind=new_db_engine)


class Abbr_SQLAlchemy(Base):
    __tablename__ = db_table_name
    id = Column(Integer, primary_key=True, autoincrement=True)
    abbr = Column(String(64), nullable=True)
    definition = Column(String(64), nullable=True)

class Abbr_Pydantic(BaseModel):
    abbr: Optional[str] = None
    definition: Optional[str] = None
    
    @validator('abbr')
    def abbr_length_check(cls, v):
        if len(v) == 1:
            raise ValueError(f"abbr is too short, it's possible not a valid abbr")

        if len(v) > 10:
            raise ValueError(f"abbr is too long, it's possible not a valid abbr")

        return v
    
def lambda_handler(event, context):
    param = event.get('param')
    query = event.get('query', None)

    abbr_obj = None
    try:
        abbr_obj = Abbr_Pydantic(**param)
    except ValidationError as e:
        return {
            'statusCode': 500,
            'message': e.json()
        }
    
    abbr_sqlalchemy = Abbr_SQLAlchemy(**abbr_obj.dict())
    
    def format_results(results):
        converted_items = []

        for idx, item in enumerate(results):
            converted_items.append(f"The definition of {item.abbr}: {item.definition}")

        return converted_items

    def possible_candidates_by_diff(records, input_str, ret_cnt=3):
        sim_list = []
        for record in records:
            # print(f"input_str:{input_str}")
            # print(f"record:{record}")
            similarity = difflib.SequenceMatcher(None, input_str, record[0]).ratio()
            sim_list.append((record[0], similarity))
        
        sorted_sim_list = sorted(sim_list, key=lambda x: x[1], reverse=True)
        # print(f"sorted_sim_list:{sorted_sim_list}")
        return [ item[0] for item in sorted_sim_list[:ret_cnt] if item[1] > similarity_threshold ]

    message = ""
    suggested_question = ""
    code = 200
    if abbr_sqlalchemy.abbr is not None:
        results = session.query(Abbr_SQLAlchemy).filter(Abbr_SQLAlchemy.abbr.ilike(f'%{abbr_sqlalchemy.abbr}%')).all()
        if len(results) == 0:
            message = f"Can't find that abbr - {abbr_sqlalchemy.abbr}."
            all_possible_abbr_list = session.query(Abbr_SQLAlchemy.abbr).all()
            top_similar_abbr = possible_candidates_by_diff(all_possible_abbr_list, abbr_sqlalchemy.abbr)
            if len(top_similar_abbr) > 1 and query:
                code = 404
                suggested_question = query.replace(abbr_sqlalchemy.abbr, top_similar_abbr[0])
        else:
            message = format_results(results)
    else:
        message = "Can't find any relevant information."
    
    return {
        'statusCode': code,
        'message': message,
        'suggested_question' : suggested_question
    }
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

new_db_connection_string = f"mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
new_db_engine = create_engine(new_db_connection_string)

Base = declarative_base()
session = Session(bind=new_db_engine)

# 定义模型类
class Employee_SQLAlchemy(Base):
    __tablename__ = db_table_name
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee = Column(String(64), nullable=True)
    role = Column(String(64), nullable=True)
    domain = Column(String(64), nullable=True)
    scope = Column(String(64), nullable=True)

class Employee_Pydantic(BaseModel):
    employee: Optional[str] = None
    role: Optional[str] = None
    domain: Optional[str] = None
    scope: Optional[str] = None
    
    @validator('role')
    def role_check(cls, v):
        allowed_role = ['Sales', 'Tech', 'Product manager', 'Project manager', 'Leader']
        allowed_role_lowercase = [ item.lower() for item in allowed_role]
        allowed_role_str = ", ".join(allowed_role)
        if v.lower() not in allowed_role_lowercase:
            raise ValueError(f"role should be in [{allowed_role_str}]")
        return v
    
def lambda_handler(event, context):
    param = event.get('param')
    
    employee_obj = None
    try:
        employee_obj = Employee_Pydantic(**param)
    except ValidationError as e:
        return {
            'statusCode': 500,
            'body': e.json()
        }
    
    employee_sqlalchemy = Employee_SQLAlchemy(**employee_obj.dict())
    
    def format_results(results):
        converted_items = []
        
        # print("call format_results")
        # print("call format_results {}".format(len(results)))
        for idx, item in enumerate(results):
            if item.role.lower() == 'sales':
                converted_items.append(f"[{idx+1}] {item.employee}, as a {item.role} role, is responsible for {item.domain} business in the {item.scope} region.")
            else:
                converted_items.append(f"[{idx+1}] {item.employee}, as a {item.role} role, is responsible for {item.scope} related services in the {item.domain} field.")
        
        print(converted_items)
        return "\n".join(converted_items)

    def possible_candidates_by_diff(records, input_str, ret_cnt=3):
        sim_list = []
        for record in enumerate(records):
            similarity = difflib.SequenceMatcher(None, input_str, record).ratio()
            sim_list.append((record, similarity))
        
        sorted_sim_list = sorted(sim_list, key=lambda x: x[1], reverse=True)
        return [ item[0] for item in sorted_sim_list[:ret_cnt] if item[1] > 0.75 ]
    
    if employee_sqlalchemy.employee is not None:
        print("query by employee name")
        results = session.query(Employee_SQLAlchemy).filter(Employee_SQLAlchemy.employee.ilike(f'%{employee_sqlalchemy.employee}%')).all()
        if len(results) == 0:
            plain_result = f"Can't find that employee - {employee_sqlalchemy.employee}."
            all_possible_employees = session.query(Employee_SQLAlchemy.employee).all()
            top_similar_employees = possible_candidates_by_diff(all_possible_employees, employee_sqlalchemy.employee)
            if len(top_similar_employees) > 0:
                top_similar_employees_str = ", ".join(top_similar_employees)
                plain_result += " Are these employees - '{top_similar_employees_str}' you are looking for? "
        else:
            plain_result = format_results(results)
    elif employee_sqlalchemy.scope is not None:
        print("query by scope only")
        results = session.query(Employee_SQLAlchemy).filter(Employee_SQLAlchemy.scope.ilike(f'%{employee_sqlalchemy.scope}%')).all()
        if len(results) == 0:
            plain_result = f"Can't find relevant information by - {employee_sqlalchemy.scope}."
            all_possible_scopes = session.query(Employee_SQLAlchemy.scope).all()
            top_similar_scopes = possible_candidates_by_diff(all_possible_scopes, employee_sqlalchemy.scope)
            if len(top_similar_scopes) > 0:
                top_similar_scopes_str = ", ".join(top_similar_scopes)
                plain_result += " Are these scopes - '{top_similar_scopes_str}' you are looking for? "
        else:
            plain_result = format_results(results)
    elif employee_sqlalchemy.domain is not None:
        print("query by domain")
        results = session.query(Employee_SQLAlchemy).filter(Employee_SQLAlchemy.domain.ilike(f'%{employee_sqlalchemy.domain}%')).all()
        if len(results) == 0:
            plain_result = "Can't find relevant information by domain - {employee_sqlalchemy.domain}."
            all_possible_domains = session.query(Employee_SQLAlchemy.domain).all()
            top_similar_domains = possible_candidates_by_diff(all_possible_domains, employee_sqlalchemy.domain)
            
            if len(top_similar_domains) > 0:
                top_similar_domains_str = ", ".join(top_similar_domains)
                plain_result += " Are these domains - '{top_similar_domains_str}' you are looking for? "
        else:
            plain_result = format_results(results)
    else:
        plain_result = "Can't find relevant information."
    
    return {
        'statusCode': 200,
        'body': plain_result
    }
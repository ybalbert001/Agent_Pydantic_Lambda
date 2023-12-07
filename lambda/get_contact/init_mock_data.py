import argparse
from sqlalchemy import create_engine, text, Column, Integer, String, MetaData, Table, Sequence, or_, and_
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session
import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--host', help="database host")
    parser.add_argument(
        '--username', help="database user name")
    parser.add_argument(
        '--password', help="database password")
    parser.add_argument(
        '--db_name', help="database name")
    parser.add_argument(
        '--csv_file', help="csv data file")
    args = parser.parse_args()

    db_username = args.username
    db_password = args.password
    db_host = args.host
    db_name = args.db_name
    local_data_csv = args.csv_file
    db_port = 3306
    db_table_name = "employee"
    
    connection_string = f"mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}"
    engine = create_engine(connection_string)

    with engine.connect() as connection:
        result = connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
        
    new_db_connection_string = f"mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
    new_db_engine = create_engine(new_db_connection_string)

    print(new_db_connection_string)

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

    session.execute(text(f'TRUNCATE TABLE {db_table_name}'))
    session.commit()
    # 创建表
    Base.metadata.create_all(bind=new_db_engine)

    # 使用模型添加数据, 需要

    df = pd.read_csv(local_data_csv)
    for index, row in df.iterrows():
        user_instance = Employee_SQLAlchemy(employee=row["employee"], role=row["role"], domain=row["domain"], scope=row["scope"])
        session.add(user_instance)

    session.commit()
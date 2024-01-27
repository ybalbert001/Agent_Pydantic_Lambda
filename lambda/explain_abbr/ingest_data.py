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
        '--excel_file', help="excel data file")
    parser.add_argument(
        '--flag', help="flag for execute")
    args = parser.parse_args()

    db_username = args.username
    db_password = args.password
    db_host = args.host
    db_name = args.db_name
    local_data_csv = args.excel_file
    db_port = 3306
    db_table_name = "abbr"
    
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
    class Abbr_SQLAlchemy(Base):
        __tablename__ = db_table_name
        id = Column(Integer, primary_key=True, autoincrement=True)
        abbr = Column(String(64), nullable=True)
        definition = Column(String(64), nullable=True)

    if args.flag == "truncate":
        session.execute(text(f'TRUNCATE TABLE {db_table_name};'))
        session.commit()
    else:
        # 创建表
        Base.metadata.create_all(bind=new_db_engine)
        session.commit()
        # 使用模型添加数据, 需要

        df = pd.read_excel(local_data_csv)
        for index, row in df.iterrows():
            if row["abbr"] is None or row["definition"] is None:
                print(row)
            else:
                try:
                    item_instance = Abbr_SQLAlchemy(abbr=row["abbr"], definition=row["definition"])
                    session.add(item_instance)
                    session.commit()
                except Exception as e:
                    print(row)
                    print(str(e))
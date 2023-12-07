import argparse
import random
import pandas as pd
import mysql.connector

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--host', help="The URI for you CSV restaurant data, like an S3 bucket location.")
    parser.add_argument(
        '--username', help="The URI where output is saved, like an S3 bucket location.")
    parser.add_argument(
        '--password', help="The URI where output is saved, like an S3 bucket location.")
    parser.add_argument(
        '--db_name', help="The URI where output is saved, like an S3 bucket location.")
    args = parser.parse_args()

    conn = mysql.connector.connect(
        host=args.host,
        user=args.username,
        passwd=args.password,
        database=args.db_name
    )

    cursor = conn.cursor()

    create_table_query = """
    CREATE TABLE employee (
        id INT AUTO_INCREMENT PRIMARY KEY,
        employee VARCHAR(64) NULL,
        role VARCHAR(64) NULL,
        domain VARCHAR(64) NULL,
        scope VARCHAR(64) NULL
    );
    """

    cursor.execute(create_table_query)

    df = pd.read_csv('data.csv')

    df.to_sql('employee', conn, if_exists='append', index=False, method='multi')

    cursor.close()
    conn.close()
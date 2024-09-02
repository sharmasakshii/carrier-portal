import pyodbc
import os
import logging

def get_connection(username, password, db_name):
    try:
        MSSQL_SERVER    = f"{os.environ['SERVER_NAME']}.database.windows.net"
        driver          ='{ODBC Driver 17 for SQL Server}'
        MSSQL_USERNAME  = username
        MSSQL_PASSWORD  = password
        MSSQL_DATABASE  = db_name

        connection_string = f'DRIVER={driver};SERVER={MSSQL_SERVER};DATABASE={MSSQL_DATABASE};UID={MSSQL_USERNAME};PWD={MSSQL_PASSWORD}'
        connection = pyodbc.connect(connection_string)
        return connection
    except Exception as e:
        logging.error(f"error : {e}")
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from helper.database import create_new_db, create_users, monotring_alert
from helper.error_response import server_error, input_required
from helper.keyvault import get_secret
from helper.db_connection import get_connection
import logging
import os
import json
import asyncio

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
@app.route(route="create_db",  methods=['POST'])
def create_db(req: func.HttpRequest) -> func.HttpResponse:
    credential = DefaultAzureCredential()

    req_body = req.get_json()

    subscription_id     = os.getenv("SUBSCRIPTION_ID")
    resource_group      = os.getenv("CARRIER_DB_RG")
    server_name         = os.getenv("SERVER_NAME")
    env                 = os.getenv("ENV")

    try:
        scac = req_body.get("scac").lower()
        if env == "nonp":
            database_name = f"GS-sql-database-dev-{scac}"
        elif env == "prod":
            database_name = f"Carriers-sql-database-prod-{scac}"
    except Exception as e:
        logging.error(f"error : {e}")
        return input_required()
    
    sql_client = SqlManagementClient(credential, subscription_id)
    try:
        if env == "nonp":

            tags = {
                'Env': 'dev',
                'Application': 'carrier_portal',
                'AppSuite': scac,
                'EnvAcct':env
            }
        elif env == "prod":
            tags = {
                'Env': 'prod',
                'Application': 'carrier_portal',
                'AppSuite': scac,
                'EnvAcct':env
            }

        # Create a SqlManagementClient
        databases = sql_client.databases.list_by_server(resource_group, server_name)
        database_list = []

        for db in databases:
            database_list.append(db.name)
        
        logging.info(f"database list: {str(database_list)}")

        if database_name in database_list:
            logging.info(f"database for scac {scac} already exists")

            response = {
                "status":"abort",
                "message":f"database for scac {scac} already exists"
            }
            return func.HttpResponse(
                json.dumps(response),
                status_code=208
            )
        else:
            logging.info(f"creating new database with name : {database_name}")
            new_db, db_id = create_new_db("10737418240",database_name,sql_client,tags)

            monitor_client = MonitorManagementClient(credential, subscription_id)
            env = "dev" if env == "nonp" else env
            monotring_alert(scac, monitor_client, db_id,env)
            response = {
                "status":"success",
                "message":f"New database created", 
                "databasename":f"{new_db}"
            }
            return func.HttpResponse(
            json.dumps(response),
            status_code=201
        )
            
    except Exception as e:
        logging.error(f"Error creating database: {e}")
        server_error(e)

@app.route(route="import_db", auth_level=func.AuthLevel.FUNCTION,methods=['POST'])
def import_db(req: func.HttpRequest) -> func.HttpResponse:
    try:
        env                     = os.getenv("ENV")
        user_secret_key         = os.getenv("USER_SECRET_KEY")
        password_secret_key     = os.getenv("PASSWORD_SECRET_KEY")

        db_username             = get_secret(user_secret_key)
        db_password             = get_secret(password_secret_key)

        req_body = req.get_json()
        try:
            scac = req_body.get("scac").lower()
            if env == "nonp":
                database_name = f"GS-sql-database-dev-{scac}"
            elif env == "prod":
                database_name = f"Carriers-sql-database-prod-{scac}"
        except Exception as e:
            logging.error(f"error : {e}")
            return input_required()

        connection = get_connection(db_username, db_password, database_name)
        cursor = connection.cursor()
        create_users(cursor, scac, env)
        connection.close()

        response = {
                "status":"success",
                "message":f"Default schema imported successful",
            }
        return func.HttpResponse(
            json.dumps(response),
            status_code=200
        )
    except Exception as e:
        logging.error(f"error : {e}")
        server_error(e)

from azure.mgmt.sql.models import Database, LongTermRetentionPolicy
import os
import logging
import random
from helper.keyvault import create_secret
from azure.mgmt.monitor.models import (
    MetricAlertResource,
    MetricAlertSingleResourceMultipleMetricCriteria,
    MetricCriteria,
    DiagnosticSettingsResource
)

def ltrp(client, database_name, server_name, resource_group):
    try:
        ltr_policy_params = LongTermRetentionPolicy(
            weekly_retention="P12W",   # 12 week
            monthly_retention="P12M",  # 12 months
            yearly_retention="P10Y",  # 10 years
            week_of_year=1            # Week of the year to take the yearly backup
        )

        ltr_policy = client.long_term_retention_policies.begin_create_or_update(
            resource_group_name=resource_group,
            server_name=server_name,
            database_name=database_name,
            policy_name="default",
            parameters=ltr_policy_params
        ).result()

    except Exception as e:
        return e
    
def create_new_db (storage_size, database_name, client, tags):
    elastic_pool_id     = os.environ["ELASTIC_POOL_ID"]
    resource_group      = os.environ["CARRIER_DB_RG"]
    server_name         = os.environ["SERVER_NAME"]
    env                 = os.environ["ENV"]

    if env == "prod":
        database_params = Database(
            location="eastus",
            elastic_pool_id=elastic_pool_id,
            max_size_bytes=storage_size, #"10737418240" 10GB in bytes
            zone_redundant=True, 
            tags=tags
        )

        database = client.databases.begin_create_or_update(
                resource_group_name=resource_group,
                server_name=server_name,
                database_name=database_name,
                parameters=database_params
            ).result()
        
        ltrp(client, database_name, server_name, resource_group)
        
        return database.name
        
    elif env == "nonp":
        database_params = Database(
            location="eastus",
            elastic_pool_id=elastic_pool_id,
            max_size_bytes=storage_size, #"10737418240" 10GB in bytes
            zone_redundant=True, 
            storage_account_type = "ZRS",
            tags=tags
        )
            
        database = client.databases.begin_create_or_update(
            resource_group_name=resource_group,
            server_name=server_name,
            database_name=database_name,
            parameters=database_params
        ).result()
        return database.name, database.id

def gen_password(len):
	l='abcdefghijklmnopqrstuvwxyz'
	u='ABCDEFGHIJKLMNOPQRSTUVWXYZ'
	no='12345678901234567890'
	symbol='!@#$%^&*(){}:"<>;'
	virtual=l+u+no+symbol
	password=''.join(random.sample(virtual,len))
	return password

def create_users (cursor, scac, env):
    try:
        if env == "prod":
            user1 = f'carrier_sql_dbuser_prod_{scac}_appuser'
            user2 = f'carrier_sql_dbuser_prod_{scac}_teamuser'

            user1_key = f"sql-prod-{scac}-appuser-username"
            password1_key = f"sql-prod-{scac}-appuser-password"

            user2_key = f"sql-prod-{scac}-teamuser-username"
            password2_key = f"sql-prod-{scac}-appuser-password"
        else:
            user1 = f'carrier_sql_dbuser_dev_{scac}_appuser'
            user2 = f'carrier_sql_dbuser_dev_{scac}_teamuser'

            user1_key = f"sql-dev-{scac}-appuser-username"
            password1_key = f"sql-dev-{scac}-appuser-password"

            user2_key = f"sql-dev-{scac}-teamuser-username"
            password2_key = f"sql-dev-{scac}-teamuser-password"
        
        password1 = gen_password(16)
        password2 = gen_password(16)

        sql_command_app_user = f'''
                                CREATE USER {user1} WITH PASSWORD = '{password1}';
                                GRANT INSERT, UPDATE, SELECT TO {user1};
                                '''
        cursor.execute (sql_command_app_user)
        
        sql_command_team_user = f'''
                            CREATE USER {user2} WITH PASSWORD = '{password2}';
                            GRANT SELECT TO {user2};
                    '''
        cursor.execute(sql_command_team_user)

        create_secret(password1_key,password1)
        create_secret(user1_key,user1)

        create_secret(password2_key,password2)
        create_secret(user2_key,user2)

        with open('carrier.sql', 'r') as file:
            sql_script = file.read()

        for statement in sql_script.split(';'):
            if statement.strip():
                cursor.execute(statement)
                cursor.commit()

    except Exception as e:
        logging.error(f"error : {e}")

def monotring_alert (scac, client, database_id, env):
    try:
        resource_group      	= os.environ["CARRIER_DB_RG"]
        alert_rule_name 	= f"Carriers-alt-alerts-{env}-global-db-{scac}-001"
        threshold_value 	= os.environ["STORAGE_ALT_THRESHOLD"] 
        workspace_id 		= os.environ["LOG_ANAY_ID"]
        storage_account_id 	= os.environ["STORAGE_ACCOUNT_ID"]
        action_group_id 	= os.environ["ACTION_GROUP_ID"]

        criteria = MetricAlertSingleResourceMultipleMetricCriteria(
            all_of=[
                MetricCriteria(
                    criterion_type="StaticThresholdCriterion",
                    name="StorageUsageHigh",
                    metric_name="storage_percent",
                    operator="GreaterThan",
                    threshold=threshold_value,
                    time_aggregation="Average"
                )
            ]
        )

        alert_rule = MetricAlertResource(
            location="global",
            description=f"storage percentage is greater than 80% for {scac.upper()} database",
            enabled=True,
            severity=2,
            scopes=[database_id],
            criteria=criteria,
            actions=[{"action_group_id": action_group_id }],
            evaluation_frequency="PT5M",
            window_size="PT5M"
        )

        client.metric_alerts.create_or_update(
            resource_group_name=resource_group,
            rule_name=alert_rule_name,
            parameters=alert_rule
        )

        diagnostic_settings_name = f"Carriers-mds-diagnostic-{env}-eastus-001"
        diagnostic_settings = DiagnosticSettingsResource( 
            storage_account_id=storage_account_id,
            workspace_id=workspace_id,
            event_hub_authorization_rule_id=None,
            event_hub_name=None,
            metrics=[{"category": "AllMetrics","enabled": True}],
            logs=[{"category": "SQLSecurityAuditEvents","enabled": True,},
                {"category": "SQLInsights","enabled": True,},
                {"category": "AutomaticTuning","enabled": True,},
                {"category": "QueryStoreRuntimeStatistics","enabled": True,},
                {"category": "QueryStoreWaitStatistics","enabled": True,},
                {"category": "Errors","enabled": True,},
                {"category": "DatabaseWaitStatistics","enabled": True,},
                {"category": "Timeouts","enabled": True,},
                {"category": "Blocks","enabled": True,},
                {"category": "Deadlocks","enabled": True,},
            ]
        )

        client.diagnostic_settings.create_or_update(
            resource_uri=database_id,
            parameters=diagnostic_settings,
            name=diagnostic_settings_name
        )

        logging.info(f"Alert rule {alert_rule_name} and diagnostic settings {diagnostic_settings_name} created successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")

import logging
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

key_vault_name          = os.environ["VAULT_NAME"]
key_vault_uri           = f"https://{key_vault_name}.vault.azure.net"
credential              = DefaultAzureCredential()

def create_secret (secret_key, secret_value):
    try:
        secret_client = SecretClient(vault_url=key_vault_uri, credential=credential)
        secret = secret_client.set_secret(secret_key, secret_value)
    except Exception as e:
        logging.error(f"Error creating secret: {e}")

def get_secret (secret_key):
    try:
        client          = SecretClient(vault_url=key_vault_uri, credential=credential)
        secret          = client.get_secret(secret_key)
        return secret.value
    except Exception as e:
        logging.error(f"Error getting secret: {e}")
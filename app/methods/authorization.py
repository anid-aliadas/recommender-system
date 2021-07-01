import requests
from ..dependencies import config

def get_token():
  url = config('KEYCLOAK_TOKEN_URL')
  headers = {
    "Content-Type": "application/x-www-form-urlencoded"
  }
  params = {
      "grant_type": "client_credentials",
      "client_secret": config('OIDC_CLIENT_SECRET'),
      "client_id": config('OIDC_CLIENT_ID'),
  }
  token = requests.post(url, headers=headers, data=params).json()
  return 'bearer ' + token['access_token']
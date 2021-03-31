import requests

BASE = "http://127.0.0.1:5000/"
tokenSpree = 'dec9c83c0a355bc48df9b0d53916eadf2de1c8cd489603b7'

headers = {
  'Content-Type': 'application/json',
  'X-Spree-Token': tokenSpree,
}


response = requests.get(BASE + "predictItems/10")
#response = requests.get("https://ecommerce-api.lc-ip81.inf.utfsm.cl/api/v1/transaction_attempts", headers=headers)
print(response.json())

""" headers = {'user-agent': 'my-app/0.0.1'}
r = requests.get(url, headers=headers) """
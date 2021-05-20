import requests
from datetime import datetime

search_text = "chocolate"
response = requests.get(url='http://localhost:8000/products/search/' + search_text)
response = response.json()

body = {
  "query_text": search_text,
  "results_ids": response['results_ids']
}

asd = requests.put(url='http://localhost:8000/test', json=body)
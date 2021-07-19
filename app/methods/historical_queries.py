from app.methods.authorization import get_token
from ..dependencies import config
import requests

def search_historic_queries(text, days_ago = 1, months_ago = 0, years_ago = 0):
    url = config('ACTION_LOGS_URL') + "/logs_query/products/queries"
    headers = {
        "Authorization": get_token()
    }
    params = {
        "page": 0,
        "per_page": 100,
        "query_match": text,
        "years_ago": years_ago,
        "months_ago": months_ago,
        "days_age": days_ago
    }
    historical_data = []
    response = ""
    while( response != [] ):
        response = requests.get(url, headers=headers, params=params).json()
        if isinstance(response, str): return response
        historical_data += response
        params["page"] += 1
    return historical_data

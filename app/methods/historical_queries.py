from app.methods.authorization import get_token
from ..dependencies import config
import requests

def search_historic_queries(text, days_ago = 1, months_ago = 0, years_ago = 0):
    url = config('ACTION_LOGS_URL') + "/logs_query/products/queries"
    headers = {
        "Authorization": 'bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI5MkxickZhUW8tUm5zejY1djMydmt0VUdRbXVKejNSY0ptY3g5MURBZTBzIn0.eyJleHAiOjE2MzEwODU5NDUsImlhdCI6MTYzMTA3NTE0NSwianRpIjoiNzM4NDBkMDctZjdkOS00NTU5LWE2OTQtMDU1ZmJhMTNhOTBhIiwiaXNzIjoiaHR0cHM6Ly9rZXljbG9hay5hbGlhZC5hcy9hdXRoL3JlYWxtcy9hbGlhZGFzIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6ImI3NmJkODE5LTYyNmQtNDIwZC1hMGViLTc0YTFkMzk2NmI0MSIsInR5cCI6IkJlYXJlciIsImF6cCI6ImFsaWFkYXMtcmVjb21tZW5kZXItc3lzdGVtIiwiYWNyIjoiMSIsInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsImNvbXByYWRvciIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWxpYWRhcy1yZWNvbW1lbmRlci1zeXN0ZW0iOnsicm9sZXMiOlsidW1hX3Byb3RlY3Rpb24iXX0sImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoicGhvbmUgcHJvZmlsZSBydXQgYWRkcmVzcyBlbWFpbCB3ZWJzaXRlIiwiY2xpZW50SWQiOiJhbGlhZGFzLXJlY29tbWVuZGVyLXN5c3RlbSIsImNsaWVudEhvc3QiOiIxOTAuMjIuMTE1LjgxIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJhZGRyZXNzIjp7fSwicHJlZmVycmVkX3VzZXJuYW1lIjoic2VydmljZS1hY2NvdW50LWFsaWFkYXMtcmVjb21tZW5kZXItc3lzdGVtIiwiY2xpZW50QWRkcmVzcyI6IjE5MC4yMi4xMTUuODEifQ.Yw1xn0JSxYgxzFHcEUfBWB7o2i7jFyp-CrDkA7zE3QY-E5gTIq13PTj23rNt0gJtWF1P6aS-20sL1T6cVb4b-R3zgcBV2W4aCP_WK4YSn1-fQfKIgdygi6zjS_3ZVGoGE39cq5lz5d2RjRd20zjc9nOUCehwnGWIsLqOFS0eCBh4TdnbVKSreXvVer-4cfASlUCGFHAHu6yTGN6lrL37Fm-3PusB-XBapF5QiDETCcnT0jrXNi-Fifa0LZz_pKBaCsfDHgkxK5NFMPUnI24Kd5DaFyr2QVnipYYByFVmnS7AqPrDt3gyW3931d3hgma3nEy6go2l5nekY0zDDQDOgA'#get_token()
    }
    params = {
        "page": 0,
        "per_page": 100,
        "query_match": text,
        "years_ago": years_ago,
        "months_ago": months_ago,
        "days_ago": days_ago
    }
    historical_data = []
    response = ""
    while( response != [] ):
        response = requests.get(url, headers=headers, params=params).json()
        if isinstance(response, str): return response
        historical_data += response
        params["page"] += 1
    return historical_data

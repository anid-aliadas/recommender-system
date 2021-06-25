from app.methods.SOG import SOG_score_predictions, calc_SOG_prof_ui
from ..dependencies import config
from elasticsearch import Elasticsearch
from fastapi import APIRouter
from datetime import datetime
import numpy as np
import scipy.sparse as sp
from scipy.stats import logistic
import requests
import pickle
from ..CF_models.collaborative_filtering import Recommender, exec

es = Elasticsearch(
    [config('ELASTIC_DIR')],
    http_auth=(config('ELASTIC_USR'), config('ELASTIC_PWD')),
    scheme="http",
    port=config('ELASTIC_PORT')
)

def temporalRank(timestamp):
    days = (datetime.now() - datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")).days
    score = lambda x: max(round((1-logistic.cdf(x/3, loc=5, scale=1))*5, 0), 0.001)

    return int(score(days))

def searchProduct(product_name):
    search_dict = {
        'query': {
            'bool': {
                'should': [
                    {
                        'nested': {
                            'path': "taxons",
                            'query': {
                                'multi_match': {
                                    'query': product_name,
                                    'fields': ['*.name']
                                }
                            }
                        }
                    },
                    {
                        'multi_match': {
                            'query': product_name,
                            'fields': ['name', 'description', 'vendor.name']
                        }
                    }
                ]
            }
        },
        'size': 11,
    }
    response = es.search(index="spree-products",
                         body=search_dict)['hits']['hits']
    return response

router = APIRouter()

@router.get("/predictions/update")
def update_model():

    url = "https://kong.aliad.as/action-logs/actions/products"
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI5MkxickZhUW8tUm5zejY1djMydmt0VUdRbXVKejNSY0ptY3g5MURBZTBzIn0.eyJleHAiOjE2MjQ1MDM1MzcsImlhdCI6MTYyNDQ5MjczNywianRpIjoiN2YyYzRlNWMtNTE2Ni00YjgyLWI0MGMtYTI0OWRjZmViMDdlIiwiaXNzIjoiaHR0cHM6Ly9rZXljbG9hay5hbGlhZC5hcy9hdXRoL3JlYWxtcy9hbGlhZGFzIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjdlYzlmMmUwLTI4ZmYtNDBlZS04ZDg1LTliY2Q4OWVkMjM0MCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImFsaWFkYXMtbW9iaWxlIiwic2Vzc2lvbl9zdGF0ZSI6ImNmMTc0ZTY4LWQwYjgtNGM5OC1hNmMzLTNlMGZmZjRmZTZkYiIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJjb21wcmFkb3IiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIHBob25lIHByb2ZpbGUgcnV0IGFkZHJlc3MgYXZhdGFyIG9mZmxpbmVfYWNjZXNzIGVtYWlsIHdlYnNpdGUgZ2VuZGVyIiwicnV0IjoiIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImFkZHJlc3MiOnt9LCJnZW5kZXIiOiJIb21icmUiLCJuYW1lIjoiQ3Jpc3RpYW4gQnJhbnQgQ2hhbW9ycm8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJjaGFtb3Jyb2JyYW50IiwiYXZhdGFyIjoiaHR0cDovL2Vjb21tZXJjZS1hcGkubGMtaXA4MS5pbmYudXRmc20uY2wvcmFpbHMvYWN0aXZlX3N0b3JhZ2UvcmVwcmVzZW50YXRpb25zL2V5SmZjbUZwYkhNaU9uc2liV1Z6YzJGblpTSTZJa0pCYUhCQmJWbENJaXdpWlhod0lqcHVkV3hzTENKd2RYSWlPaUppYkc5aVgybGtJbjE5LS1lN2M0MjJlMDI5NzU1ZDQ0OWMyMDE4MjkyMGUxN2UxYjFjMWFjZmY2L2V5SmZjbUZwYkhNaU9uc2liV1Z6YzJGblpTSTZJa0pCYURkQ2FtOU1ZMjFXZW1GWWNHeFRVMGxPVG1wVmQyVkVaek5OUkRSSFQyZGFSbFpCUFQwaUxDSmxlSEFpT201MWJHd3NJbkIxY2lJNkluWmhjbWxoZEdsdmJpSjlmUT09LS1mZDU0OTNkNjBkMWYzYmFkODg3NDE3OWMyZGZlYTA1ZTk5MjRiYzdjLzgxNTMwOWZkLTk2NWEtNDdmNy1hNWIxLWYxYWQ2YmFlM2Q5MC5qcGciLCJnaXZlbl9uYW1lIjoiQ3Jpc3RpYW4iLCJmYW1pbHlfbmFtZSI6IkJyYW50IENoYW1vcnJvIiwiZW1haWwiOiJjaGFtb3Jyb2JyYW50QGdtYWlsLmNvbSJ9.AjsQa8VHlNu6x8uR4saBtqdqtocevJRcIKScBbgB84y41sKiBDWUSj9QwX9Mxt88lPPy37Z-guryCyxK4v6o7YKJaWzFvYorOgVBvsHmEdRLBDyICUiNKKan2f2md0P27-GoPQYFGVAhjUn4VJxRu7ZuQGNkVEgsqjvwdtKPYiZKK5nCLjSOoteahxikJRIP-KbXhIdQ-7FXkzBWbkHw0fZf-mutRjrsINZAP7zPYZgl6QWk0nBiKy45vTgc6LxvtM5oA8zb6TusIKuJ5s8ePy5yqI8GQ6Aoh4T7vSvPmVKn2W6NwCHloqGFyb7-NAiIQuqc4p7Jr-5HLtghWH1HwQ"
    headers = {
        "Authorization": "bearer " + token,
    }
    page = 0
    response = {'response': 'initial'}
    users_actions_dict = {}
    logged_items = set()

    with open("app/files/products/data.pkl", "rb") as file:
        products_dict = pickle.load(file)
        file.close()


    while( response != [] ):
        params = {
            "page": page,
            "per_page": 100,
        }
        response = requests.get(url, headers=headers,
                                params=params).json()

        if isinstance(response, str): return {'response' : response}

        for action in response:
            if action['action_product_id']['product_id'] not in products_dict: continue #Si el producto fue borrado
            if action['action_product_id']['user_id'] not in users_actions_dict:
                users_actions_dict[action['action_product_id']['user_id']] = {}
            if action['action_product_id']['product_id'] not in users_actions_dict[action['action_product_id']['user_id']]: 
                users_actions_dict[action['action_product_id']['user_id']][action['action_product_id']['product_id']] = temporalRank(action['updated_at'])
                logged_items.add(action['action_product_id']['product_id'])

        page+=1


    UNIQUE_USERS = sorted(list(users_actions_dict.keys()))
    UNIQUE_ITEMS = sorted(list(products_dict.keys())) 
    UNIQUE_ITEMS.remove(-1)
    

    row_ind = [UNIQUE_USERS.index(k) for k, v in users_actions_dict.items() for _ in range(len(v))]
    col_ind = []
    data = []
    for item in users_actions_dict.values():
        for item_id, temporal_rank in item.items():
            col_ind.append(UNIQUE_ITEMS.index(item_id))
            data.append(temporal_rank)

    print(users_actions_dict)

    X = sp.csr_matrix((data, (row_ind, col_ind)), shape=(len(UNIQUE_USERS), len(UNIQUE_ITEMS))).tolil() # sparse csr matrix

    print(X.todense())

    unlogged_items = set(UNIQUE_ITEMS) - logged_items
    ### NON-LOGGED ITEMS BOOST ###
    for item_id in unlogged_items:
        response = searchProduct(products_dict[item_id]['name'])
        similar_ids = []
        for doc in response:
            if int(doc['_id']) != item_id: similar_ids.append(UNIQUE_ITEMS.index(int(doc['_id'])))
        if similar_ids != []:
            centroid = sp.lil_matrix((X[:, similar_ids]).mean(axis=1))
            X[:, UNIQUE_ITEMS.index(item_id)] = centroid

    RS = Recommender(X.tocsr(), normalize=True)
    RS.users_data = users_actions_dict
    RS.unique_users = UNIQUE_USERS
    RS.unique_items = UNIQUE_ITEMS

    with open("app/files/RS/Recommender.pkl", "wb") as file:
        pickle.dump(RS, file)
        file.close()

    return {'response': 'success'}


@router.get("/recommender/{user_id}")
def recommend_to_user(user_id: int):
    with open("app/files/RS/Recommender.pkl", "rb") as file:
        RS = pickle.load(file)
        file.close()
    if 0 <= user_id <= len(RS.unique_users):#RS.unique_users:

        users_actions_dict = RS.users_data 
        UNIQUE_USERS = RS.unique_users
        UNIQUE_ITEMS = RS.unique_items
        user_id = UNIQUE_USERS[user_id]
        user_index = UNIQUE_USERS.index(user_id)

        with open("app/files/products/data.pkl", "rb") as file:
            products_dict = pickle.load(file)
            file.close()
        out = RS.recommend(user_index, top_users=2, top_items=10, alpha=1, limits=None)
        SOG_prof_ui = calc_SOG_prof_ui(out['r'], [UNIQUE_ITEMS.index(i) for i in users_actions_dict[user_id]], RS.items_similarity_matrix)

        #out = RS.recommend(UNIQUE_USERS.index(user_id), top_users=5, top_items=5, alpha=1, limits=None) VERSION PARA EL RELEASE

        ##### SOG #####
        original_response = out['r'][:]

        SOG_response = []
        SOG_response.append(out['r'].pop(0))
        for i in range(len(out['r'])):
            max_score = -1
            for item_data in out['r']:
                score = SOG_score_predictions(item_data, SOG_response, SOG_prof_ui[item_data[0]], RS.unpop[0, item_data[0]], RS.items_similarity_matrix)
                if score > max_score:
                    max_score = score
                    best_item = item_data
            SOG_response.append(out['r'].pop(out['r'].index(best_item)))
        
        return { 'original_order': original_response, 'SOG_order': SOG_response }

    else: return { 'response': 'user not in model' }

    # Al crear un nuevo producto (o en 'la noche') buscar su nombre en elastic, en base al resultado tomar los 10 productos que mas se parecen
    # Con este top de productos obtener sus vectores y calcular un centroide y lo insertamos en la matriz de CF
    

    # Variable temporal: elementos nuevos sean mas relevantes que los que buscamos en el pasado, con esto damos notas de 0 - 5
    # con una funcion exponencial decayente

    # juanca: cortar logs por cant por usuario
    # usar matriz mascara para calcular centroide
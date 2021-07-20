import requests
import pickle
from datetime import datetime
from scipy.stats import logistic
import scipy.sparse as sp
from ..dependencies import config
from elasticsearch import Elasticsearch
from ..methods.natural_languaje_processing import get_nouns
from ..CF_models.collaborative_filtering import Recommender

import time

es = Elasticsearch(
    [config('ELASTIC_DIR')],
    http_auth=(config('ELASTIC_USR'), config('ELASTIC_PWD')),
    scheme="http",
    port=config('ELASTIC_PORT')
)

def temporalRank(timestamp):
    days = (datetime.now() - datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")).days
    score = lambda x: max(round((1-logistic.cdf(x/3, loc=5, scale=1))*5, 0), 0.001)

    return score(days)

def searchProduct(search_text):
    search_text = get_nouns(search_text)
    search_dict = {
        'query': {
            'bool': {
                'should': [
                    {
                        'nested': {
                            'path': "taxons",
                            'query': {
                                'multi_match': {
                                    'query': search_text,
                                    'fields': ['*.name']
                                }
                            }
                        }
                    },
                    {
                        'multi_match': {
                            'query': search_text,
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

def update_model(user_token):
    url = config('ACTION_LOGS_URL') + '/logs_query/products'
    headers = {
        "Authorization": user_token,
    }
    params = {
        "page": 0,
        "per_page": 100,
    }
    response = ""
    users_actions_dict = {}
    logged_items = set()

    with open("app/files/products/data.pkl", "rb") as file:
        products_dict = pickle.load(file)
        file.close()

    print("Retrieving users actions")
    while( response != [] ):
        response = requests.get(url, headers=headers, params=params).json()

        if isinstance(response, str): return {'response' : response} #Para retornar error de autorizacion por ahora

        for action in response:
            if action['action_product_id']['product_id'] not in products_dict: continue #Si el producto fue borrado
            if action['action_product_id']['user_id'] not in users_actions_dict:
                users_actions_dict[action['action_product_id']['user_id']] = {}
            if action['action_product_id']['product_id'] not in users_actions_dict[action['action_product_id']['user_id']]: 
                users_actions_dict[action['action_product_id']['user_id']][action['action_product_id']['product_id']] = temporalRank(action['updated_at'])
                logged_items.add(action['action_product_id']['product_id'])

        params["page"] += 1


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

    #print(users_actions_dict)
    print("Building user-products matrix")
    X = sp.csr_matrix((data, (row_ind, col_ind)), shape=(len(UNIQUE_USERS), len(UNIQUE_ITEMS))).tolil() # sparse csr matrix
    unlogged_items = set(UNIQUE_ITEMS) - logged_items

    i = 0
    ### NON-LOGGED ITEMS BOOST ###
    print("Boosting non-logged products")

    for item_id in unlogged_items:
        response = searchProduct( str(products_dict[item_id]['name']) + ' ' + str(products_dict[item_id]['description']))
        similar_ids = []
        for doc in response:
            if int(doc['_id']) != item_id and int(doc['_id']) in UNIQUE_ITEMS: similar_ids.append(UNIQUE_ITEMS.index(int(doc['_id'])))
        if similar_ids != []:
            centroid = sp.lil_matrix((X[:, similar_ids]).mean(axis=1))
            X[:, UNIQUE_ITEMS.index(item_id)] = centroid
        i+=1
    RS = Recommender(X.tocsr(), normalize=True)
    RS.users_data = users_actions_dict
    RS.unique_users = UNIQUE_USERS
    RS.unique_items = UNIQUE_ITEMS
    print("Saving model")
    with open("app/files/RS/Recommender.pkl", "wb") as file:
        pickle.dump(RS, file)
        file.close()
    return "Recommender model updated"

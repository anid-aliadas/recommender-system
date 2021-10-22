import requests
import pickle
from datetime import datetime
from scipy.stats import logistic
import scipy.sparse as sp
from ..dependencies import config
from elasticsearch import Elasticsearch
from ..methods.natural_languaje_processing import get_nouns
from ..CF_models.collaborative_filtering import Recommender
from ..middlewares.keycloak import get_keycloak_users

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
                            'fields': ['name^3', 'description', 'vendor.name']
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

def searchVendor(search_text):
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
                            'fields': ['name', 'about_us^2']
                        }
                    }
                ]
            }
        },
        'size': 11,
    }
    response = es.search(index="spree-vendors",
                         body=search_dict)['hits']['hits']
    return response

def get_users_products_actions(products_data, user_token):
    url = config('ACTION_LOGS_URL') + '/logs_query/products'
    headers = {
        "Authorization": user_token,
    }
    params = {
        "page": 0,
        "per_page": 1000,
    }
    response = ""
    users_actions_dict = {}
    logged_items = set()
    while( response != [] ):
        response = requests.get(url, headers=headers, params=params).json()
        if isinstance(response, str): return {'response' : response} #Para retornar error de autorizacion por ahora
        for action in response:
            if action['action_product_id']['product_id'] not in products_data: continue #Si el producto fue borrado
            if action['action_product_id']['user_id'] not in users_actions_dict:
                users_actions_dict[action['action_product_id']['user_id']] = {}
            if action['action_product_id']['product_id'] not in users_actions_dict[action['action_product_id']['user_id']]: 
                users_actions_dict[action['action_product_id']['user_id']][action['action_product_id']['product_id']] = temporalRank(action['updated_at'])
                logged_items.add(action['action_product_id']['product_id'])
        params["page"] += 1
    return users_actions_dict, logged_items

def get_users_vendors_actions(vendors_data, user_token):
    url = config('ACTION_LOGS_URL') + '/logs_query/vendors'
    headers = {
        "Authorization": user_token,
    }
    params = {
        "page": 0,
        "per_page": 1000,
        "days_ago": 30
    }
    response = ""
    users_actions_dict = {}
    logged_items = set()
    while( response != [] ):
        response = requests.get(url, headers=headers, params=params).json()
        if isinstance(response, str): return {'response' : response} #Para retornar error de autorizacion por ahora
        for action in response:
            if action['vendor_id'] not in vendors_data: continue #Si el producto fue borrado
            if action['user_id'] not in users_actions_dict:
                users_actions_dict[action['user_id']] = {}
            if action['vendor_id'] not in users_actions_dict[action['user_id']]: 
                users_actions_dict[action['user_id']][action['vendor_id']] = temporalRank(action['created_at'])
                logged_items.add(action['vendor_id'])
        params["page"] += 1
    return users_actions_dict, logged_items

def build_matrix(users, items, actions):
    row_ind = [users.index(k) for k, v in actions.items() for _ in range(len(v))]
    col_ind = []
    data = []
    for item in actions.values():
        for item_id, temporal_rank in item.items():
            col_ind.append(items.index(item_id))
            data.append(temporal_rank)

    #print(actions)
    return sp.csr_matrix((data, (row_ind, col_ind)), shape=(len(users), len(items))).tolil() # sparse csr matrix

def load_file_data(path):
    with open(path, "rb") as file:
        data = pickle.load(file)
        file.close()
    return data

def save_file_data(path, data):
    with open(path, "wb") as file:
        pickle.dump(data, file)
        file.close()

def get_stores_data():
    url = config('SPREE_VENDORS_URL')
    headers = {
        "X-Spree-Token": config('SPREE_API_KEY')
    } 
    params = {
        "page": 0,
        "per_page": 1000,
        "excluded_taxon_ids[]": 305,
    }
    taxon_prueba = {
        "taxon_id": 305,
        "position": None,
        "taxon": {
            "name": "Prueba"
        }
    }
    all_stores = []
    response = requests.get(url, headers=headers, params=params).json()["vendors"]
    while( not isinstance(response, str) and response != [] ):
        all_stores += response
        params["page"] += 1
        response = requests.get(url, headers=headers, params=params).json()["vendors"]
    docs_dict = {}
    for num, doc in enumerate(all_stores):
        if not doc['deleted_at'] and taxon_prueba not in doc['vendor_taxons']:
            docs_dict[doc['id']] = {'local_index': num, 'name': doc['name'], 'description': doc['about_us']}
    return docs_dict

def get_users_interests_model():
    print("* Updating user interests model\n*")
    url = config('SPREE_USERS_URL')
    headers = {
        "X-Spree-Token": config('SPREE_API_KEY')
    } 
    params = {
        "page": 1,
        "per_page": 1000,
    }
    users_interests_dict = {}
    response = requests.get(url, headers=headers, params=params).json()["users"]
    UNIQUE_TAXONS = set()
    print("*    1/3 - retrieving interests data")
    while( not isinstance(response, str) and response != [] ):
        for user_data in response:
            if not user_data['keycloak_id']: continue
            user_taxons = []
            for taxon in user_data['user_taxons']:
                user_taxons.append(taxon['taxon_id'])
                UNIQUE_TAXONS.add(taxon['taxon_id'])
            users_interests_dict[user_data['keycloak_id']] = user_taxons 
        params["page"] += 1
        response = requests.get(url, headers=headers, params=params).json()["users"]

    UNIQUE_USERS = sorted(get_keycloak_users())
    UNIQUE_TAXONS = sorted(list(UNIQUE_TAXONS))
    
    print("*    2/3 - Building model matrix")
    row_ind = [UNIQUE_USERS.index(k) for k, v in users_interests_dict.items() for _ in range(len(v))]
    col_ind = []
    data = []
    for taxons_list in users_interests_dict.values():
        for taxon_id in taxons_list:
            col_ind.append(UNIQUE_TAXONS.index(taxon_id))
            data.append(1)
    X = sp.csr_matrix((data, (row_ind, col_ind)), shape=(len(UNIQUE_USERS), len(UNIQUE_TAXONS))).tolil() # sparse csr matrix
    data_object = (X, UNIQUE_USERS, UNIQUE_TAXONS)

    print("*    3/3 - Saving model")
    save_file_data("app/files/RS/interests_data.pkl", data_object)
    return "*\n* User interests model updated!"

def get_arrays_difference(a, b):
    return list(set(a + b) - set(a))

def expand_matrix_rows(X, n_new_rows):
    Y = sp.lil_matrix((n_new_rows, X.shape[1]))
    return sp.vstack([X.tocoo(), Y.tocoo()])

def update_model_products(user_token):
    print("* Updating products recommender model\n*")
    print("*    1/8 - Loading products data")
    products_dict = load_file_data("app/files/products/data.pkl")

    print("*    2/8 - Retrieving users actions")
    users_actions_dict, logged_items = get_users_products_actions(products_dict, user_token)
    ACTIONS_UNIQUE_USERS = list(users_actions_dict.keys())

    print("*    3/8 - Loading users interests model")
    Xi, UNIQUE_USERS, _ = load_file_data("app/files/RS/interests_data.pkl")

    print("*    4/8 - Adding deleted users to model")
    DELETED_USERS = get_arrays_difference(UNIQUE_USERS, ACTIONS_UNIQUE_USERS)
    UNIQUE_USERS += DELETED_USERS
    UNIQUE_ITEMS = sorted(list(products_dict.keys()))
    UNIQUE_ITEMS.remove(-1)
    Xi = expand_matrix_rows(Xi, len(DELETED_USERS))

    print("*    5/8 - Building user-products matrix")
    Xv = build_matrix(UNIQUE_USERS, UNIQUE_ITEMS, users_actions_dict)

    print("*    6/8 - Boosting non-logged products")
    unlogged_items = set(UNIQUE_ITEMS) - logged_items
    i = 0
    for item_id in unlogged_items:
        response = searchProduct( str(products_dict[item_id]['name']) + ' ' + str(products_dict[item_id]['description']))
        similar_ids = []
        for doc in response:
            if int(doc['_id']) != item_id and int(doc['_id']) in UNIQUE_ITEMS: similar_ids.append(UNIQUE_ITEMS.index(int(doc['_id'])))
        if similar_ids != []:
            centroid = sp.lil_matrix((Xv[:, similar_ids]).mean(axis=1))
            Xv[:, UNIQUE_ITEMS.index(item_id)] = centroid
        i+=1

    print("*    7/8 - Generating recommender model")
    RS = Recommender(Xv.tocsr(), Xi.tocsr(), normalize=True)
    RS.users_data = users_actions_dict
    RS.unique_users = UNIQUE_USERS
    RS.unique_items = UNIQUE_ITEMS

    print("*    8/8 - Saving model")
    save_file_data("app/files/RS/products_recommender.pkl", RS)
    return "*\n* Products recommender model updated!"

def update_model_stores(user_token):
    print("* Updating vendors recommender model\n*")
    print("*    1/8 - Loading products data")
    stores_dict = get_stores_data()

    print("*    2/8 - Retrieving users actions")
    users_actions_dict, logged_items = get_users_vendors_actions(stores_dict, user_token)
    ACTIONS_UNIQUE_USERS = list(users_actions_dict.keys())

    print("*    3/8 - Loading users interests model")
    Xi, UNIQUE_USERS, _ = load_file_data("app/files/RS/interests_data.pkl")

    print("*    4/8 - Adding deleted users to model")
    DELETED_USERS = get_arrays_difference(UNIQUE_USERS, ACTIONS_UNIQUE_USERS)
    UNIQUE_USERS += DELETED_USERS
    UNIQUE_ITEMS = sorted(list(stores_dict.keys()))
    Xi = expand_matrix_rows(Xi, len(DELETED_USERS))

    print("*    5/8 - Building user-vendors matrix")
    Xv = build_matrix(UNIQUE_USERS, UNIQUE_ITEMS, users_actions_dict)

    print("*    6/8 - Boosting non-logged vendors")
    unlogged_items = set(UNIQUE_ITEMS) - logged_items
    i = 0
    for item_id in unlogged_items:
        response = searchVendor( str(stores_dict[item_id]['description']))
        similar_ids = []
        for doc in response:
            if int(doc['_id']) != item_id and int(doc['_id']) in UNIQUE_ITEMS: similar_ids.append(UNIQUE_ITEMS.index(int(doc['_id'])))
        if similar_ids != []:
            centroid = sp.lil_matrix((Xv[:, similar_ids]).mean(axis=1))
            Xv[:, UNIQUE_ITEMS.index(item_id)] = centroid
        i+=1
    
    print("*    7/8 - Generating recommender model")
    RS = Recommender(Xv.tocsr(), Xi.tocsr(), normalize=True)
    RS.users_data = users_actions_dict
    RS.unique_users = UNIQUE_USERS
    RS.unique_items = UNIQUE_ITEMS

    print("*    8/8 - Saving model")
    save_file_data("app/files/RS/vendors_recommender.pkl", RS)

    return "*\n* Vendors recommender model updated!"


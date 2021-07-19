from app.methods.natural_languaje_processing import get_nouns
from app.methods.SOG import SOG_score_predictions, calc_SOG_prof_ui
from ..dependencies import config
from elasticsearch import Elasticsearch
from fastapi import APIRouter, Request
from datetime import datetime

import scipy.sparse as sp
from scipy.stats import logistic
import requests
import pickle
from ..CF_models.collaborative_filtering import Recommender

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
    response = es.search(index="spree-products", body=search_dict)['hits']['hits']
    return response

router = APIRouter()

@router.get("/recommender/update")
def update_model(req: Request):
    url = config('ACTION_LOGS_URL') + '/logs_query/products'
    headers = {
        "Authorization": req.headers["Authorization"],
    }
    params = {
        "page": 0,
        "per_page": 100,
    }
    response = {'response': 'initial'}
    users_actions_dict = {}
    logged_items = set()

    with open("app/files/products/data.pkl", "rb") as file:
        products_dict = pickle.load(file)
        file.close()

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

    print(users_actions_dict)

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

    X = sp.csr_matrix((data, (row_ind, col_ind)), shape=(len(UNIQUE_USERS), len(UNIQUE_ITEMS))).tolil() # sparse csr matrix
    unlogged_items = set(UNIQUE_ITEMS) - logged_items

    ### NON-LOGGED ITEMS BOOST ###
    for item_id in unlogged_items:
        response = searchProduct( str(products_dict[item_id]['name']) + ' ' + str(products_dict[item_id]['description']))
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


@router.get("/recommender")
def recommend_to_user(user_id: str):
    with open("app/files/RS/Recommender.pkl", "rb") as file:
        RS = pickle.load(file)
        file.close()
    if user_id in RS.unique_users:
        users_actions_dict = RS.users_data 
        UNIQUE_USERS = RS.unique_users
        UNIQUE_ITEMS = RS.unique_items
        user_index = UNIQUE_USERS.index(user_id)

        print(RS.X.todense())

        out = RS.recommend(user_index, top_users=2, top_items=10, alpha=1, limits=None)
        SOG_prof_ui = calc_SOG_prof_ui(out['r'], [UNIQUE_ITEMS.index(i) for i in users_actions_dict[user_id]], RS.items_similarity_matrix)

        #out = RS.recommend(UNIQUE_USERS.index(user_id), top_users=5, top_items=5, alpha=1, limits=None) VERSION PARA EL RELEASE

        ##### SOG #####
        #original_response = out['r'][:]

        response = []
        SOG_response = []
        response.append(UNIQUE_ITEMS[out['r'][0][0]])
        SOG_response.append(out['r'].pop(0))
        for i in range(len(out['r'])):
            max_score = -1
            for item_data in out['r']:
                score = SOG_score_predictions(item_data, SOG_response, SOG_prof_ui[item_data[0]], RS.unpop[0, item_data[0]], RS.items_similarity_matrix)
                if score > max_score:
                    max_score = score
                    best_item = item_data
            response.append(UNIQUE_ITEMS[out['r'][out['r'].index(best_item)][0]])
            SOG_response.append(out['r'].pop(out['r'].index(best_item)))
        
        return { 'response': response }

    else: return { 'response': [] }

    # Al crear un nuevo producto (o en 'la noche') buscar su nombre en elastic, en base al resultado tomar los 10 productos que mas se parecen
    # Con este top de productos obtener sus vectores y calcular un centroide y lo insertamos en la matriz de CF
    

    # Variable temporal: elementos nuevos sean mas relevantes que los que buscamos en el pasado, con esto damos notas de 0 - 5
    # con una funcion exponencial decayente

    # juanca: cortar logs por cant por usuario
    # usar matriz mascara para calcular centroide
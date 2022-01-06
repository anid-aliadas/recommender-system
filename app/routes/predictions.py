from app.methods.SOG import SOG_predictions, SOG_score_predictions, calc_SOG_prof_ui
from ..dependencies import config
from fastapi import APIRouter
import pickle
import numpy as np
import requests

router = APIRouter()

with open("app/files/RS/vendors_recommender.pkl", "rb") as file:
    V_RS = pickle.load(file)
    file.close()
with open("app/files/RS/products_recommender.pkl", "rb") as file:
    P_RS = pickle.load(file)
    file.close()

def validate_response(response, type):
    validated_response = []
    headers = {
        "X-Spree-Token": config('SPREE_API_KEY')
    } 
    params = {
        "page": 0,
        "per_page": 1000,
        "excluded_taxon_ids[]": 305,
    }
    if type == 'products':
        url = config('SPREE_PRODUCTS_URL')
        all_products = []
        r = requests.get(url, headers=headers, params=params).json()['response']
        while( not isinstance(r, str) and r != [] ):
            all_products += [product["_source"]["id"] for product in r]
            params["page"] += 1
            r = requests.get(url, headers=headers, params=params).json()['response']
        validated_response = [id for id in response if id in all_products]
    else:
        params['page'] = 1 #la primera pagina de tiendas es la 1, la 0 es igual a la 1 por default -.----
        url = config('SPREE_VENDORS_URL')
        all_stores = []
        r = requests.get(url, headers=headers, params=params).json()["vendors"]
        while( not isinstance(r, str) and r != [] ):
            all_stores += [vendor['id'] for vendor in r]
            params["page"] += 1
            r = requests.get(url, headers=headers, params=params).json()["vendors"]
        validated_response = [id for id in response if id in all_stores]
    return validated_response

@router.get("/recommender")
def recommend_products(user_id: str):
    if user_id in P_RS.unique_users:
        users_actions_dict = P_RS.users_data 
        UNIQUE_USERS = P_RS.unique_users
        UNIQUE_ITEMS = P_RS.unique_items
        user_index = UNIQUE_USERS.index(user_id)
        out = P_RS.recommend(
            user_index, 
            top_users = int(config('CF_N_TOP_USERS')), 
            top_items = int(config('CF_N_TOP_ITEMS')), 
            alpha = float(config('CF_SIMILARITY_AMPLIFICATION')), 
            beta = float(config('CF_COSINE_SIMILARITY_WEIGHT')), 
            limits = None
        )
        if user_id in users_actions_dict:
            user_data = [UNIQUE_ITEMS.index(i) for i in users_actions_dict[user_id]]
        SOG_prof_ui = calc_SOG_prof_ui(
            out['r'], 
            user_data, 
            P_RS.items_similarity_matrix
        )
        SOG_response = SOG_predictions(out, SOG_prof_ui, P_RS)
        return { 'response': validate_response([UNIQUE_ITEMS[id] for id, score in SOG_response], 'products') }
    else: return { 'response': [] }

@router.get("/recommender/products")
def recommend_products(user_id: str):
    if user_id in P_RS.unique_users:
        users_actions_dict = P_RS.users_data 
        UNIQUE_USERS = P_RS.unique_users
        UNIQUE_ITEMS = P_RS.unique_items
        user_index = UNIQUE_USERS.index(user_id)
        out = P_RS.recommend(
            user_index, 
            top_users = int(config('CF_N_TOP_USERS')), 
            top_items = int(config('CF_N_TOP_ITEMS')), 
            alpha = float(config('CF_SIMILARITY_AMPLIFICATION')), 
            beta = float(config('CF_COSINE_SIMILARITY_WEIGHT')), 
            limits = None
        )
        user_data = []
        if user_id in users_actions_dict:
            user_data = [UNIQUE_ITEMS.index(i) for i in users_actions_dict[user_id]]
        SOG_prof_ui = calc_SOG_prof_ui(
            out['r'], 
            user_data, 
            P_RS.items_similarity_matrix
        )

        SOG_response = SOG_predictions(out, SOG_prof_ui, P_RS)

        return { 'response': validate_response([UNIQUE_ITEMS[id] for id, score in SOG_response], 'products') }
    else: return { 'response': [] }

@router.get("/recommender/vendors")
def recommend_vendors(user_id: str):
    if user_id in V_RS.unique_users:
        users_actions_dict = V_RS.users_data 
        UNIQUE_USERS = V_RS.unique_users
        UNIQUE_ITEMS = V_RS.unique_items
        user_index = UNIQUE_USERS.index(user_id)
        out = V_RS.recommend(
            user_index, 
            top_users = int(config('CF_N_TOP_USERS')), 
            top_items = int(config('CF_N_TOP_ITEMS')), 
            alpha = float(config('CF_SIMILARITY_AMPLIFICATION')), 
            beta = float(config('CF_COSINE_SIMILARITY_WEIGHT')), 
            limits = None
        )
        user_data = []
        if user_id in users_actions_dict:
            user_data = [UNIQUE_ITEMS.index(i) for i in users_actions_dict[user_id]]
        SOG_prof_ui = calc_SOG_prof_ui(
            out['r'], 
            user_data, 
            V_RS.items_similarity_matrix
        )
        SOG_response = SOG_predictions(out, SOG_prof_ui, V_RS)
        return { 'response': validate_response([UNIQUE_ITEMS[id] for id, score in SOG_response], 'vendors') }
    else: return { 'response': [] }
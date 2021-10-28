from app.methods.SOG import SOG_predictions, SOG_score_predictions, calc_SOG_prof_ui
from ..dependencies import config
from fastapi import APIRouter
import pickle
import numpy as np

router = APIRouter()

with open("app/files/RS/vendors_recommender.pkl", "rb") as file:
    V_RS = pickle.load(file)
    file.close()
with open("app/files/RS/products_recommender.pkl", "rb") as file:
    P_RS = pickle.load(file)
    file.close()

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
        return { 'response': [UNIQUE_ITEMS[id] for id, score in SOG_response] }
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
        return { 'response': [UNIQUE_ITEMS[id] for id, score in SOG_response] }
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
        return { 'response': [UNIQUE_ITEMS[id] for id, score in SOG_response] }
    else: return { 'response': [] }
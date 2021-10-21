from app.methods.SOG import SOG_score_predictions, calc_SOG_prof_ui
from ..dependencies import config
from fastapi import APIRouter
import pickle

router = APIRouter()

@router.get("/recommender/")
def recommend_products(user_id: str):
    with open("app/files/RS/products_recommender.pkl", "rb") as file:
        RS = pickle.load(file)
        file.close()
    if user_id in RS.unique_users:
        users_actions_dict = RS.users_data 
        UNIQUE_USERS = RS.unique_users
        UNIQUE_ITEMS = RS.unique_items
        user_index = UNIQUE_USERS.index(user_id)
        out = RS.recommend(user_index, top_users=10, top_items=10, alpha=1, beta=0.7, limits=None)
        SOG_prof_ui = calc_SOG_prof_ui(out['r'], [UNIQUE_ITEMS.index(i) for i in users_actions_dict[user_id]], RS.items_similarity_matrix)
        ##### SOG #####
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

@router.get("/recommender/products")
def recommend_products(user_id: str):
    with open("app/files/RS/products_recommender.pkl", "rb") as file:
        RS = pickle.load(file)
        file.close()
    if user_id in RS.unique_users:
        users_actions_dict = RS.users_data 
        UNIQUE_USERS = RS.unique_users
        UNIQUE_ITEMS = RS.unique_items
        user_index = UNIQUE_USERS.index(user_id)
        out = RS.recommend(user_index, top_users=10, top_items=10, alpha=1, beta=0.7, limits=None)
        SOG_prof_ui = calc_SOG_prof_ui(out['r'], [UNIQUE_ITEMS.index(i) for i in users_actions_dict[user_id]], RS.items_similarity_matrix)
        ##### SOG #####
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

@router.get("/recommender/vendors")
def recommend_vendors(user_id: str):
    with open("app/files/RS/vendors_recommender.pkl", "rb") as file:
        RS = pickle.load(file)
        file.close()
    if user_id in RS.unique_users:
        users_actions_dict = RS.users_data 
        UNIQUE_USERS = RS.unique_users
        UNIQUE_ITEMS = RS.unique_items
        user_index = UNIQUE_USERS.index(user_id)
        out = RS.recommend(user_index, top_users=10, top_items=10, alpha=1, beta=0.7, limits=None)
        ##### SOG #####
        SOG_prof_ui = calc_SOG_prof_ui(out['r'], [UNIQUE_ITEMS.index(i) for i in users_actions_dict[user_id]], RS.items_similarity_matrix)
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
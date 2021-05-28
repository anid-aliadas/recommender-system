from fastapi import APIRouter
import numpy as np
import scipy.sparse as sp
import requests
import pickle
from ..CF_models.collaborative_filtering import Recommender, exec

router = APIRouter()

@router.get("/predictions/items/update/matrix")
def update_matrix():

    url = "https://kong.aliad.as/action-logs/actions/products"
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI5MkxickZhUW8tUm5zejY1djMydmt0VUdRbXVKejNSY0ptY3g5MURBZTBzIn0.eyJleHAiOjE2MjIyMjkwNjQsImlhdCI6MTYyMjIxODI2NCwianRpIjoiYTQyMzc5ZTYtMDZjMS00NDkzLTk4Y2YtNDgyODU3Zjk3NTI2IiwiaXNzIjoiaHR0cHM6Ly9rZXljbG9hay5hbGlhZC5hcy9hdXRoL3JlYWxtcy9hbGlhZGFzIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjdlYzlmMmUwLTI4ZmYtNDBlZS04ZDg1LTliY2Q4OWVkMjM0MCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImFsaWFkYXMtbW9iaWxlIiwic2Vzc2lvbl9zdGF0ZSI6IjlhMGEyMGM5LTcyNzUtNDA4Ny04ZDI3LTJiZmY0ZTIyYTM1NyIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJjb21wcmFkb3IiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIHBob25lIHByb2ZpbGUgcnV0IGFkZHJlc3MgYXZhdGFyIG9mZmxpbmVfYWNjZXNzIGVtYWlsIHdlYnNpdGUgZ2VuZGVyIiwicnV0IjoiIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImFkZHJlc3MiOnt9LCJnZW5kZXIiOiJIb21icmUiLCJuYW1lIjoiQ3Jpc3RpYW4gQnJhbnQgQ2hhbW9ycm8iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJjaGFtb3Jyb2JyYW50IiwiYXZhdGFyIjoiaHR0cDovL2Vjb21tZXJjZS1hcGkubGMtaXA4MS5pbmYudXRmc20uY2wvcmFpbHMvYWN0aXZlX3N0b3JhZ2UvcmVwcmVzZW50YXRpb25zL2V5SmZjbUZwYkhNaU9uc2liV1Z6YzJGblpTSTZJa0pCYUhCQmJWbENJaXdpWlhod0lqcHVkV3hzTENKd2RYSWlPaUppYkc5aVgybGtJbjE5LS1lN2M0MjJlMDI5NzU1ZDQ0OWMyMDE4MjkyMGUxN2UxYjFjMWFjZmY2L2V5SmZjbUZwYkhNaU9uc2liV1Z6YzJGblpTSTZJa0pCYURkQ2FtOU1ZMjFXZW1GWWNHeFRVMGxPVG1wVmQyVkVaek5OUkRSSFQyZGFSbFpCUFQwaUxDSmxlSEFpT201MWJHd3NJbkIxY2lJNkluWmhjbWxoZEdsdmJpSjlmUT09LS1mZDU0OTNkNjBkMWYzYmFkODg3NDE3OWMyZGZlYTA1ZTk5MjRiYzdjLzgxNTMwOWZkLTk2NWEtNDdmNy1hNWIxLWYxYWQ2YmFlM2Q5MC5qcGciLCJnaXZlbl9uYW1lIjoiQ3Jpc3RpYW4iLCJmYW1pbHlfbmFtZSI6IkJyYW50IENoYW1vcnJvIiwiZW1haWwiOiJjaGFtb3Jyb2JyYW50QGdtYWlsLmNvbSJ9.M0bJXyLsqGJlGZzqdl98OPzSp-3s8L-H0jFSD0eyAUUIPqA_uquKylVCsaxv9ZuD8kUdy087VdrNoFmtiuJyzLQei7bAE1Bu5C7NUYCl6-QidIm3edaOgIEl5hv9Fpu48nVM718LqX1jZvOpAtTTrtXjDpJNCGRnRe33cY7yV0pa5o2_tSLOpjNGs_3Ktm9o8FlBdbcojlZHCYajS4WsCZCLe4fbfT6JwIg_9LzODdhwHDy0ZHaun460fL_WI6_weDk5sQQo24qzQLGtzMJCUgoIl3yjsjGj-Ieak3kPFTq5epNIc3JiocxQtXvsmZEnRI1uEX_pbidOfhO0MteQbg"
    headers = {
        "Authorization": "bearer " + token,
    }
    page = 0
    response = {'response': 'initial'}
    users_actions_dict = {}
    users_actions_products = {}
    unique_items = set()

    with open("app/files/products/data.pkl", "rb") as file:
        products_dict = pickle.load(file)
        file.close()

    while( response != [] ):
        params = {
            "page": page,
        }
        response = requests.get(url, headers=headers,
                                params=params).json()
        if isinstance(response, str): return {'response' : response}

        for action in response:
            if action['product_id'] not in products_dict: continue
            if action['user_id'] not in users_actions_dict:
                users_actions_dict[action['user_id']] = []
                users_actions_products[action['user_id']] = []
            if action['product_id'] not in users_actions_dict[action['user_id']]: 
                users_actions_dict[action['user_id']].append(action['product_id'])
                users_actions_products[action['user_id']].append(products_dict[action['product_id']]['name'])
                unique_items.add(action['product_id'])
        page+=1

    with open("app/files/users/data.pkl", "wb") as file:
        pickle.dump(users_actions_dict, file)
        file.close()

    # ESTO IRIA EN LA RUTA UPDATE ^^^^^

    UNIQUE_USERS = sorted(list(users_actions_dict.keys()))
    UNIQUE_ITEMS = sorted(list(unique_items)) #Tengo que tener acceso a todos los ids de usuarios e itemes

    row_ind = [UNIQUE_USERS.index(k) for k, v in users_actions_dict.items() for _ in range(len(v))]
    col_ind = [UNIQUE_ITEMS.index(i) for ids in users_actions_dict.values() for i in ids]

    X = sp.csr_matrix(([1]*len(row_ind), (row_ind, col_ind))) # sparse csr matrix
    print(X.todense())
    RS = Recommender(X, normalize=True)

    with open("app/files/RS/unique_users.pkl", "wb") as file:
        pickle.dump(UNIQUE_USERS, file)
        file.close()

    with open("app/files/RS/unique_items.pkl", "wb") as file:
        pickle.dump(UNIQUE_ITEMS, file)
        file.close()

    with open("app/files/RS/Recommender.pkl", "wb") as file:
        pickle.dump(RS, file)
        file.close()

    for user in users_actions_products:
        users_actions_products[user].append("[local_index: {}]".format(UNIQUE_USERS.index(user)))
    return {'response': users_actions_products}


@router.get("/recommender/{user_id}")
def recommend_to_user(user_id: int):
    with open("app/files/RS/Recommender.pkl", "rb") as file:
        RS = pickle.load(file)
        file.close()
    with open("app/files/RS/unique_users.pkl", "rb") as file:
        UNIQUE_USERS = pickle.load(file)
        file.close()

    with open("app/files/RS/unique_items.pkl", "rb") as file:
        UNIQUE_ITEMS = pickle.load(file)
        file.close()
    with open("app/files/products/data.pkl", "rb") as file:
        products_dict = pickle.load(file)
        file.close()
    out = RS.recommend(user_id, top_users=2, top_items=10, alpha=1, limits=None)
    print(RS.X.todense())
    #out = RS.recommend(UNIQUE_USERS.index(user_id), top_users=5, top_items=5, alpha=1, limits=None) VERSION PARA EL RELEASE
    out_dict = { UNIQUE_USERS[user_id] : []}
    for i, j in out['r'].items():
        out_dict[UNIQUE_USERS[user_id]].append(str([UNIQUE_ITEMS[i]]) + ' -> ' + products_dict[UNIQUE_ITEMS[i]]['name'] + '; rating ' + str([j]))
        #print("Recommended: item {} with rating {}".format(UNIQUE_ITEMS[i], j))
    #exec()
    for key, value in out.items():
        if isinstance(value, (dict, list)): continue
        out[key] = value.tolist()
    return { 'out': out, 'products': out_dict }


    # Al crear un nuevo producto (o en 'la noche') buscar su nombre en elastic, en base al resultado tomar los 10 productos que mas se parecen
    # Con este top de productos obtener sus vectores y calcular un centroide y lo insertamos en la matriz de CF
    
    # juanca: cortar logs por cant por usuario
    # usar matriz mascara para calcular centroide
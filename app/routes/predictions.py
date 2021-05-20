from fastapi import APIRouter
import numpy as np
import scipy.sparse as sp
import requests
import pickle
from ..CF_models.collaborative_filtering import Recommender

router = APIRouter()

""" RS = Recommender(X, normalize=True, normalize_std=True)
row_i = 41102
out = RS.recommend(row_i, top_users=10, top_items=20, alpha=1, limits=None)
for i, j in out['r'].items():
    print("Recommended: item {} with rating {}".format(UNIQUE_MOVIES[i], j))
#142882,91658,2.5,1515209647000
#print(np.sign(out['similarity'])*np.abs(out['similarity'])**1.2)
print(out['similarity']) """

@router.get("/predictions/items/update/matrix")
def update_matrix():
    url = "https://kong.aliad.as/action-logs/actions/products"
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI5MkxickZhUW8tUm5zejY1djMydmt0VUdRbXVKejNSY0ptY3g5MURBZTBzIn0.eyJleHAiOjE2MjE1NTQ1NjIsImlhdCI6MTYyMTU0Mzc2MiwianRpIjoiODBlY2E3MzItMDEwNi00OWVlLWE1NjMtYTVkYTQ5NjliZGFmIiwiaXNzIjoiaHR0cHM6Ly9rZXljbG9hay5hbGlhZC5hcy9hdXRoL3JlYWxtcy9hbGlhZGFzIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjdlYzlmMmUwLTI4ZmYtNDBlZS04ZDg1LTliY2Q4OWVkMjM0MCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImFsaWFkYXMtbW9iaWxlIiwic2Vzc2lvbl9zdGF0ZSI6IjNlMjI2ODQ1LTY4NDktNGRkYS1hMGE3LWNkNjQ3YzM5NjQxMSIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJjb21wcmFkb3IiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIHBob25lIHByb2ZpbGUgcnV0IGFkZHJlc3MgYXZhdGFyIG9mZmxpbmVfYWNjZXNzIGVtYWlsIHdlYnNpdGUgZ2VuZGVyIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImFkZHJlc3MiOnt9LCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJjaGFtb3Jyb2JyYW50IiwiZW1haWwiOiJjaGFtb3Jyb2JyYW50QGdtYWlsLmNvbSJ9.NXYTKHX8vrrcc6Itd6T0rwi3Lkioz-OdxThSaShhgjY9F9L2mv1rDbnfOaCJUmVbLPrMAxQjEzChNwoo4xtbUwr55cYG5MPgq-IfdEJVzuUgHFc68F2COocdKViz2uGoW_MBLFN7AvBToZVM8ym5YNBS5ps-ZdoWflTIRqMoeUCBsvv3RKeJPmp-KKeuH2V4FIUMnjm2OiHRbr8kBAyAQmp-iU12-A4eJqtsIpJGwJDttgMZBaqxFR9fs0wcQ9B_rFDmQWjO461Wxwb2JOHKJ8taxlKCn2Nq8NJt8dOiks3qYnD7feffFjuPKs96iDcqcfuu4XZfd5Q9sq3HLZ-Nxw"
    headers = {
        "Authorization": "bearer " + token,
    }
    page = 0
    response = {'response': 'initial'}
    users_actions_dict = {}
    unique_items = set()
    while( response != [] ):
        params = {
            "page": page,
        }
        response = requests.get(url, headers=headers,
                                params=params).json()
        if isinstance(response, str): return {'response' : response}
        for action in response:
            if action['user_id'] not in users_actions_dict:
                users_actions_dict[action['user_id']] = []
            if action['product_id'] not in users_actions_dict[action['user_id']]: 
                users_actions_dict[action['user_id']].append(action['product_id'])
                unique_items.add(action['product_id'])
        page+=1
    users_actions_dict['asd'] = [56, 3, 79 ,9]

    with open("app/files/users/data.pkl", "wb") as file:
        pickle.dump(users_actions_dict, file)
        file.close()

    # ESTO IRIA EN LA RUTA UPDATE

    UNIQUE_USERS = sorted(list(users_actions_dict.keys()))
    UNIQUE_ITEMS = sorted(list(unique_items)) #Tengo que tener acceso a todos los ids de usuarios e itemes

    row_ind = [UNIQUE_USERS.index(k) for k, v in users_actions_dict.items() for _ in range(len(v))]
    col_ind = [UNIQUE_ITEMS.index(i) for ids in users_actions_dict.values() for i in ids]

    X = sp.csr_matrix(([1]*len(row_ind), (row_ind, col_ind))) # sparse csr matrix
    print(X.todense())
    RS = Recommender(X, normalize=True, normalize_std=True)

    with open("app/files/RS/unique_users.pkl", "wb") as file:
        pickle.dump(UNIQUE_USERS, file)
        file.close()

    with open("app/files/RS/unique_items.pkl", "wb") as file:
        pickle.dump(UNIQUE_ITEMS, file)
        file.close()

    with open("app/files/RS/Recommender.pkl", "wb") as file:
        pickle.dump(RS, file)
        file.close()
    return {'response': users_actions_dict}


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
    out = RS.recommend(user_id, top_users=10, top_items=20, alpha=1, limits=None)
    #out = RS.recommend(UNIQUE_USERS.index(user_id), top_users=10, top_items=20, alpha=1, limits=None) VERSION PARA EL RELEASE
    for i, j in out['r'].items():
        print("Recommended: item {} with rating {}".format(UNIQUE_ITEMS[i], j))
    print(out)
    return {"items": out['r']}
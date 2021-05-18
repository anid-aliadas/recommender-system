from fastapi import APIRouter
import requests
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


@router.get("/predictions/items/update")
async def updateMatrix():
    url = "https://kong.aliad.as/action-logs/actions/products"
    token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI5MkxickZhUW8tUm5zejY1djMydmt0VUdRbXVKejNSY0ptY3g5MURBZTBzIn0.eyJleHAiOjE2MjEzMjM2ODAsImlhdCI6MTYyMTMxMjg4MCwianRpIjoiMmQwZDgwYzItOGU2MS00ZDkzLThlMjQtMWVlNWI3ZmI3NTZhIiwiaXNzIjoiaHR0cHM6Ly9rZXljbG9hay5hbGlhZC5hcy9hdXRoL3JlYWxtcy9hbGlhZGFzIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjdlYzlmMmUwLTI4ZmYtNDBlZS04ZDg1LTliY2Q4OWVkMjM0MCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImFsaWFkYXMtbW9iaWxlIiwic2Vzc2lvbl9zdGF0ZSI6ImVmNzc1MTA3LTc3MzAtNDViZS1hMTVkLTY1NjZjZjgwZDI3MyIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJjb21wcmFkb3IiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIHBob25lIHByb2ZpbGUgcnV0IGFkZHJlc3MgYXZhdGFyIG9mZmxpbmVfYWNjZXNzIGVtYWlsIHdlYnNpdGUgZ2VuZGVyIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImFkZHJlc3MiOnt9LCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJjaGFtb3Jyb2JyYW50IiwiZW1haWwiOiJjaGFtb3Jyb2JyYW50QGdtYWlsLmNvbSJ9.kJLkorEhdhUS2Pza9Z7jPl5q-HwGUyRWa-GBNKlEMouKjIyrxZsVwuVW36XcqlW7jLYWhGbDPikVIAmSbKljRrN4TRp-wsH81oM9avpu2uOt-VmOKtk3mzZkfTcOwrd-tlfXXf5_soQe2t_fPyPabzmKFH4XP2OwGeTkFhQKflKGFT3UPpt937iCe0_p36yLfoPAq-JRflO-M0W7QcY96qgAienla11KQWFEDbhaN7sjQE_2i1-RGAJCr3ij-Wp-hWK9DoaZLCcvZyvzAVhb7HQBJj5xeQJ7IOcYiyUd2KJ33oDpATHEwZEYGPYBuOY_-ryb6qbaxwsW6esyMhKoJA"
    headers = {
        "Authorization": "bearer " + token,
    }
    page = 0
    response = {'response': 'initial'}
    users_actions_dict = {}
    while( response != [] ):
        params = {
            "page": page,
        }
        response = await requests.get(url, headers=headers,
                                params=params).json()
        if isinstance(response, str): return {'response' : response}
        for action in response:
            if action['user_id'] not in users_actions_dict:
                users_actions_dict[action['user_id']] = []
            if action['product_id'] not in users_actions_dict[action['user_id']]: users_actions_dict[action['user_id']].append(action['product_id'])
        page+=1


    return {'response': users_actions_dict}


@router.get("/itemsPredictions/{user_id}")
def get_items_predictions(user_id: int):
    return {"items": user_id}
from app.updating_methods.update_CF_model import update_model_products, update_model_stores, get_users_interests_model
from app.methods.authorization import get_token

token = get_token()

print('-'*40)
print(get_users_interests_model())
print('-'*40)
print(update_model_stores( token ))
print('-'*40)
print(update_model_products( token ))
print('-'*40)
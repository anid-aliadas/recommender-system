from app.updating_methods.update_CF_model import update_model
from app.methods.authorization import get_token

token = get_token()
print(update_model( token ))
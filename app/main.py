from .dependencies import config
from .middlewares.keycloak import ValidateUserToken
from fastapi import FastAPI
from .routes import elastic, predictions
from .database import engine
from .models.actions import *
import pickle
# FastAPI initialization

app = FastAPI()

# Middlewares

if config('APP_ENVIRONMENT') == 'production':
    app.add_middleware(ValidateUserToken)


@app.get("/")
def root():
    return {"status: working!"}

app.include_router(elastic.router)
app.include_router(predictions.router)

# TESTING ZONE

@app.get("/test")
async def test():
    with open("app/files/products/data.pkl", "rb") as file:
        docs_dict = pickle.load(file)

    print(docs_dict)
    return {'test': 'success'}

# RUN COMMAND: $ uvicorn app.main:app --reload


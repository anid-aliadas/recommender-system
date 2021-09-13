from app.methods.SOG import filter_products_ids
from .dependencies import config
from .middlewares.keycloak import ValidateUserToken
from fastapi import FastAPI
from .routes import elastic, predictions
from .models.actions import *
from .methods.natural_languaje_processing import *
import pickle
import os

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

@app.get("/test1")
def test():
    test = config("TOP_N_VOCAB_WORDS_PERCENTAGE")
    with open(".env", "a") as file:
        file.write("\nASD=69")
        file.close()
    return test


# RUN COMMAND: $ uvicorn app.main:app --reload
# $ python update_products_script.py
# $ python update_recommender_script.py


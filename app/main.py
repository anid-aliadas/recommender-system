from .dependencies import config
from .middlewares.keycloak import ValidateUserToken
from fastapi import FastAPI
from .routes import elastic, predictions
from .database import engine
from .models.actions import *
from .methods.natural_languaje_processing import *
import pickle
from nltk.corpus import cess_esp
import spacy

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
    efficiency = spacy.load('es_core_news_sm')
    doc1 = efficiency("yo leo, tu lees, ellos leen")
    print([(w.text, w.pos_) for w in doc1])

    print()

    accuracy = spacy.load('es_dep_news_trf')
    doc2 = accuracy("yo leo, tu lees, ellos leen")
    print([(w.text, w.pos_) for w in doc2])

    return {'test': 1}

# RUN COMMAND: $ uvicorn app.main:app --reload


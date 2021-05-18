from .dependencies import config
from .middlewares.keycloak import ValidateUserToken
from fastapi import FastAPI
from .routes import elastic, predictions
from .database import engine
from .models.actions import *
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

@app.put("/test")
async def test( queryData: ActionOverQuery ):
    await engine.save(queryData)
    return {'test': 'success'}

# RUN COMMAND: $ uvicorn app.main:app --reload


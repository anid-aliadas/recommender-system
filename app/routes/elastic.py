from app.methods.historical_queries import search_historic_queries
from ..dependencies import config
from ..methods.SOG import SOG_score_elastic
from ..methods.natural_languaje_processing import *
from elasticsearch import Elasticsearch
import pickle
from ..models.actions import *
import numpy as np
import random
from fastapi import APIRouter
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from scipy.sparse import vstack
router = APIRouter()

# ElasticSearch initialization

es = Elasticsearch(
    [config('ELASTIC_DIR')],
    http_auth=(config('ELASTIC_USR'), config('ELASTIC_PWD')),
    scheme="http",
    port=config('ELASTIC_PORT')
)

@router.get("/products/search/{search_text}")
def get_products_search(search_text):
    search_dict = {
        'query': {
            'bool': {
                'should': [
                    {
                        'nested': {
                            'path': "taxons",
                            'query': {
                                'multi_match': {
                                    'query': search_text,
                                    'fields': ['*.name']
                                }
                            }
                        }
                    },
                    {
                        'multi_match': {
                            'query': search_text,
                            'fields': ['name', 'description', 'vendor.name']
                        }
                    },
                ],
                'must_not': {
                    'nested': {
                        'path': "taxons",
                        'query':{
                            'match': {
                                "taxons.id": 305
                            }
                        }
                    }
                }
            }
        },
        'size': 100,
    }

    historical_search = search_historic_queries(text= search_text, days_ago=1)
    response = es.search(index="spree-products", body=search_dict)['hits']['hits']

    #Checking if elastic result has data, if it's the case, we extract it
    if len(response) == 0: return { 'results_ids': [], 'historical': False, 'error': False }
    elastic_result = []
    for doc in response: elastic_result.append(doc['_source']['id'])

    #Checking for errors in historical search and returning just the elastic result
    if isinstance(historical_search, str): return { 'results_ids': elastic_result, 'historical': False, 'error': historical_search } 
    
    #If the historical search and the elastic one are the same we do not run SOG
    if len(historical_search) > 0 and set(historical_search['results_ids']) == set(elastic_result): return { 'results_ids': historical_search['results_ids'], 'historical': True, 'error': False }
    
    #If there's new data we run SOG
    results_ids = []
    SOG_response = []
    SOG_response.append(response.pop(0))
    results_ids.append(int(SOG_response[-1]['_id']))
    with open('app/files/products/data.pkl', 'rb') as f:
        docs_dict = pickle.load(f)
    with open('app/files/products/similarities_matrix.pkl', 'rb') as f:
        sim_matrix = pickle.load(f)
    for _ in range(len(response)):  # iterate through top docs ---- SOG
        max_score = -1
        for doc in response:
            score = SOG_score_elastic(doc, SOG_response, docs_dict, sim_matrix)
            if score > max_score:
                max_score = score
                best_doc = doc
        SOG_response.append(response.pop(response.index(best_doc)))
        results_ids.append(int(SOG_response[-1]['_id']))
    return { 'results_ids': results_ids, 'historical': False, 'error': False }
    

@router.get("/vendors/new")
def get_new_vendors(sample_size:int = 3, n_newest:int = 10):
    search_dict = {
        'sort': [
            { "created_at" : "desc" }
        ],
        'query': {
            'match_all': {},
        },
        'size': n_newest,
    }
    response = es.search(index="spree-vendors", body=search_dict)["hits"]["hits"]
    return random.sample(response, sample_size)
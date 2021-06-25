from ..dependencies import config
from ..methods.SOG import SOG_score_elastic
from ..methods.natural_languaje_processing import *
from elasticsearch import Elasticsearch
import pickle
from ..database import engine
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

# ROUTES FOR DATA UPDATE

@router.get("/products/vectorize")
def vectorize_products():
    corpus = []
    vectorizer = CountVectorizer()
    search_dict = {
        'query': {
            'match_all': {}
        },
        'size': 10000,  # máximo admisible actualmente
    }
    response = es.search(index="spree-products", body=search_dict)
    response_hits = response['hits']['hits']
    docs_dict = {}
    for num, doc in enumerate(response_hits):
        doc_id = doc['_source']['id']
        doc_name = doc['_source']['name']
        doc_description = doc['_source']['description']
        docs_dict[doc_id] = {'local_index': num, 'name': doc_name, 'description': doc_description}
        # print(num,' ', doc_name, ': ', doc_description)
        cleaned_text = accent_mark_removal(clean_text_round2(clean_text_round1(doc_name + ' ' + str(doc_description))))
        docs_dict[doc_id]['cleaned_vocabulary'] = list(set(cleaned_text.split(' ')))
        corpus.append(cleaned_text)

    vec = vectorizer.fit(corpus)  # dense matrix - bert para español
    X = vec.transform(corpus) #corpus vecs

    top_vocabulary = get_top_vocabulary(X, vec, 25)
    centroid = X.mean(axis=0) #vecs means
    X = vstack([X, centroid]) #add centroid to position -1
    for doc_id in docs_dict:
        docs_dict[doc_id]['unpop'] = len(np.intersect1d(docs_dict[doc_id]['cleaned_vocabulary'], top_vocabulary))/len(top_vocabulary)
    docs_dict.update({ -1 : { 'unpop' : 0 } })

    X = cosine_similarity(X) # The value in the i-th row and j-th column of the result is the cosine similarity between the i-th and j-th row of array.
    with open('app/files/products/data.pkl', 'wb') as f:
        pickle.dump(docs_dict, f)
    with open('app/files/products/similarities_matrix.pkl', 'wb') as f:
        pickle.dump(X, f)
    return {"Products vectorization": "success!"}

# SEARCHING ROUTES


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
                    }
                ]
            }
        },
        'size': 100,
    }
    response = es.search(index="spree-products",
                         body=search_dict)['hits']['hits']
    if len(response) > 0:
        #for num, doc in enumerate(response): print(num, "--", doc['_source']['name'], "--", doc['_source']['vendor']['name'])
        results_ids = []
        SOG_response = []
        SOG_response.append(response.pop(0))
        results_ids.append(int(SOG_response[-1]['_id']))
        with open('app/files/products/data.pkl', 'rb') as f:
            docs_dict = pickle.load(f)
        with open('app/files/products/similarities_matrix.pkl', 'rb') as f:
            sim_matrix = pickle.load(f)
        for i in range(len(response)):  # iterate through top docs ---- SOG
            print(i)
            max_score = -1
            for doc in response:
                score = SOG_score_elastic(doc, SOG_response, docs_dict, sim_matrix)
                if score > max_score:
                    max_score = score
                    best_doc = doc
            SOG_response.append(response.pop(response.index(best_doc)))
            results_ids.append(int(SOG_response[-1]['_id']))
        #print("*"*50)
        #for num, doc in enumerate(SOG_response): print(num, "--", doc['_source']['name'], "--", doc['_source']['vendor']['name'])
        return {'response': SOG_response, 'results_ids' : results_ids}
    return {'response': response}

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


@router.post("/products/search/historic")
async def save_search_history(body: ActionOverQuery):
    await engine.save(body) #quizá encerrar en un try catch?
    return {'response': 'success'}
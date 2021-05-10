import logging
import pickle
import requests
import numpy as np

from .dependencies import config
from .middlewares.keycloak import ValidateUserToken
from fastapi import APIRouter, FastAPI, Request
from elasticsearch import Elasticsearch
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from .textCleaning import clean_text_round1, clean_text_round2, stemmer
from .database import engine
from app.models.actions import *
from app.CF_models.collaborative_filtering import Recommender

def SOG_score(doc, candidate_set, docs_dict, sim_matrix):
    score = 0
    div_iB = 0
    n = 0
    product_index = docs_dict[int(doc['_id'])]['local_index']
    product_vendor = doc['_source']['vendor']['name']
    unpop_i = docs_dict[int(doc['_id'])]['unpop']
    for candidate_doc in candidate_set:
        candidate_vendor = candidate_doc['_source']['vendor']['name']
        candidate_index = docs_dict[int(candidate_doc['_id'])]['local_index']
        div_iB += (1 - sim_matrix[product_index][candidate_index])
        if product_vendor == candidate_vendor: n += 1
    product_score = doc['_score']
    div_vendor_iB = 1/(n+1)

    #comparar doc_vendor contra todos los vendors del candidate_Set
    #Si no lo encontramos (doc_vendor) se el asigna prob V.import
    #Si lo encontramos se le asigna prov V/n+1 donde n es la cantidad de apariciones en candidate_Set
    score += 0.2 * product_score + 0.4 * (div_iB/len(candidate_set)) + 0.2 * unpop_i + 0.2 * div_vendor_iB
    return score

def get_top_vocabulary(X, vec, top_n):
    sum_corpus_words = X.sum(axis=0)
    words_freq = [(word, sum_corpus_words[0, idx]) for word, idx in vec.vocabulary_.items()]
    words_freq = sorted(words_freq, key = lambda x: x[1], reverse=True)
    return [word for word, freq in words_freq[:top_n]]

# ElasticSearch initialization


es = Elasticsearch(
    [config('ELASTIC_DIR')],
    http_auth=(config('ELASTIC_USR'), config('ELASTIC_PWD')),
    scheme="http",
    port=config('ELASTIC_PORT')
)

# FastAPI initialization

app = FastAPI()

# Middlewares

if config('APP_ENVIRONMENT') == 'production':
    app.add_middleware(ValidateUserToken)

# Routes

@app.get("/")
def root():
    return {"status: working!"}

@app.get("/products/vectorize")
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
        cleaned_text = stemmer(clean_text_round2(clean_text_round1(doc_name + ' ' + str(doc_description))))
        docs_dict[doc_id]['cleaned_vocabulary'] = list(set(cleaned_text.split(' ')))
        corpus.append(cleaned_text)
    # print(len(corpus))
    vec = vectorizer.fit(corpus)  # dense matrix - bert para español
    X = vec.transform(corpus)
    top_vocabulary = get_top_vocabulary(X, vec, 25)
    for doc_id in docs_dict:
        docs_dict[doc_id]['unpop'] = len(np.intersect1d(docs_dict[doc_id]['cleaned_vocabulary'], top_vocabulary))/len(top_vocabulary)

    X = cosine_similarity(X) # The value in the i-th row and j-th column of the result is the cosine similarity between the i-th and j-th row of array.
    with open('app/products_data.pkl', 'wb') as f:
        pickle.dump(docs_dict, f)
    with open('app/products_similarities_matrix.pkl', 'wb') as f:
        pickle.dump(X, f)
    return {"Products vectorization": "success!"}

@app.get("/vendors/vectorize")
def vectorize_vendors():
    corpus = []
    vectorizer = CountVectorizer()
    search_dict = {
        'query': {
            'match_all': {}
        },
        'size': 10000,  # máximo admisible actualmente
    }
    response = es.search(index="spree-vendors", body=search_dict)
    response_hits = response['hits']['hits']
    docs_dict = {}
    for num, doc in enumerate(response_hits):
        doc_id = doc['_source']['id']
        doc_name = doc['_source']['name']
        doc_description = doc['_source']['about_us']
        # { product_id: { local_index: product_name }}
        # print(num,' ', doc_name, ': ', doc_description)
        docs_dict[doc_id] = {'local_index': num, 'name': doc_name, 'description': doc_description}
        cleaned_text = stemmer(clean_text_round2(clean_text_round1(doc_name + ' ' + str(doc_description))))
        docs_dict[doc_id]['cleaned_vocabulary'] = list(set(cleaned_text.split(' ')))
        corpus.append(cleaned_text)
    # print(len(corpus))
    vec = vectorizer.fit(corpus)  # dense matrix - bert para español
    X = vec.transform(corpus)
    top_vocabulary = get_top_vocabulary(X, vec, 25)
    for doc_id in docs_dict:
        docs_dict[doc_id]['unpop'] = len(np.intersect1d(docs_dict[doc_id]['cleaned_vocabulary'], top_vocabulary))/len(top_vocabulary)

    # The value in the i-th row and j-th column of the result is the cosine similarity between the i-th and j-th row of array.
    X = cosine_similarity(X)

    with open('app/vendors_data.pkl', 'wb') as f:
        pickle.dump(docs_dict, f)
    with open('app/vendors_similarities_matrix.pkl', 'wb') as f:
        pickle.dump(X, f)
    return {"Vendors vectorization": "success!"}

@app.get("/products/search/{search_text}")
def get_products_search(search_text):
    tokenSpree = 'dec9c83c0a355bc48df9b0d53916eadf2de1c8cd489603b7'
    # ?page=0&query=${keyword}&per_page=33
    url = "https://kong.aliad.as/ecommerce/api/search/products"
    headers = {
        "Content-Type": "application/json",
        "X-Spree-Token": tokenSpree,
    }
    params = {
        "page": 0,
        "query": search_text,
        "per_page": 100,
    }
    # quizás debamos tener la consulta en este mismo script, no?
    response = requests.get(url, headers=headers,
                            params=params).json()['response']
    if len(response) > 0:
        for num, doc in enumerate(response):
            print(num, "--", doc['_source']['name'])

        SOG_response = []
        SOG_response.append(response.pop(0))
        with open('app/products_data.pkl', 'rb') as f:
            docs_dict = pickle.load(f)
        with open('app/products_similarities_matrix.pkl', 'rb') as f:
            sim_matrix = pickle.load(f)
        for i in range(len(response)):  # iterate through top docs ---- SOG
            max_score = -1
            for doc in response:
                score = SOG_score(doc, SOG_response, docs_dict, sim_matrix)
                if score > max_score:
                    max_score = score
                    best_doc = doc
            SOG_response.append(response.pop(response.index(best_doc)))

        print()
        for num, doc in enumerate(SOG_response):
            print(num, "--", doc['_source']['name'], "--", doc['_source']['vendor']['name'])
        return {'response': SOG_response}
    return {'response': response}

@app.get("/vendors/search/{search_text}")
def get_vendors_search(search_text):
    tokenSpree = 'dec9c83c0a355bc48df9b0d53916eadf2de1c8cd489603b7'
    # ?page=0&query=${keyword}&per_page=33
    url = "https://kong.aliad.as/ecommerce/api/search/vendors"
    headers = {
        "Content-Type": "application/json",
        "X-Spree-Token": tokenSpree,
    }
    params = {
        "page": 0,
        "query": search_text,
        "per_page": 20,
    }
    # quizás debamos tener la consulta en este mismo script, no?
    response = requests.get(url, headers=headers,
                            params=params).json()['response']
    if len(response) > 0:
        for num, doc in enumerate(response):
            print(num, "--", doc['_source']['name'])

        SOG_response = []
        SOG_response.append(response.pop(0))
        with open('app/vendors_data.pkl', 'rb') as f:
            docs_dict = pickle.load(f)
        with open('app/vendors_similarities_matrix.pkl', 'rb') as f:
            sim_matrix = pickle.load(f)
        for i in range(len(response)):  # iterate through top docs ---- SOG
            max_score = -1
            for doc in response:
                score = SOG_score(doc, SOG_response, docs_dict, sim_matrix)
                if score > max_score:
                    max_score = score
                    best_doc = doc
            SOG_response.append(response.pop(response.index(best_doc)))

        print()
        for num, doc in enumerate(SOG_response):
            print(num, "--", doc['_source']['name'])
        return {'response': SOG_response}
    return {'response': response}


""" RS = Recommender(X, normalize=True, normalize_std=True)
row_i = 41102
out = RS.recommend(row_i, top_users=10, top_items=20, alpha=1, limits=None)
for i, j in out['r'].items():
    print("Recommended: item {} with rating {}".format(UNIQUE_MOVIES[i], j))
#142882,91658,2.5,1515209647000
#print(np.sign(out['similarity'])*np.abs(out['similarity'])**1.2)
print(out['similarity']) """

@app.get("/itemsPredictions/{user_id}")
def get_items_predictions(user_id: int):
    return {"items": user_id}

@app.put("/test")
async def test():
    test = ActionOverQuery(
        query_text = "test",
        results_id = [0, 1, 2, 3]
    )
    await engine.save(test)
    return {'state':'success'}

# RUN COMMAND: $ uvicorn app.main:app --reload

""" query: {
              bool: {
                should: [
                  {
                    nested: {
                      path: 'taxons',
                      query:{
                        multi_match: {
                          query: params[:query],
                          fields: ['*.name']
                        }
                      }
                    }
                  },
                  {
                    multi_match: {
                      query: params[:query],
                      fields: ['name', 'description', 'vendor.name']
                    }
                  }
                ]
              }
            }
          ).results """
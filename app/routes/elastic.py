from ..dependencies import config
from ..methods.SOG import *
from ..methods.natural_languaje_processing import *
from elasticsearch import Elasticsearch
import pickle
from ..database import engine

import numpy as np
from fastapi import APIRouter
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer


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
    with open('app/files/products/data.pkl', 'wb') as f:
        pickle.dump(docs_dict, f)
    with open('app/files/products/similarities_matrix.pkl', 'wb') as f:
        pickle.dump(X, f)
    return {"Products vectorization": "success!"}

@router.get("/vendors/vectorize")
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

    with open('app/files/vendors/data.pkl', 'wb') as f:
        pickle.dump(docs_dict, f)
    with open('app/files/vendors/similarities_matrix.pkl', 'wb') as f:
        pickle.dump(X, f)
    return {"Vendors vectorization": "success!"}


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
        for num, doc in enumerate(response):
            print(num, "--", doc['_source']['name'], "--", doc['_source']['vendor']['name'])

        SOG_response = []
        SOG_response.append(response.pop(0))
        with open('app/files/products/data.pkl', 'rb') as f:
            docs_dict = pickle.load(f)
        with open('app/files/products/similarities_matrix.pkl', 'rb') as f:
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

@router.get("/vendors/search/{search_text}")
def get_vendors_search(search_text):
    search_dict = {
        'query': {
              'bool': {
                'should': [
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
    response = es.search(index="spree-vendors", body=search_dict)['hits']['hits']
    if len(response) > 0:
        for num, doc in enumerate(response):
            print(num, "--", doc['_source']['name'])

        SOG_response = []
        SOG_response.append(response.pop(0))
        with open('app/files/vendors/data.pkl', 'rb') as f:
            docs_dict = pickle.load(f)
        with open('app/files/vendors/similarities_matrix.pkl', 'rb') as f:
            sim_matrix = pickle.load(f)
        for i in range(len(response)):  # iterate through top docs ---- SOG
            max_score = -1
            for doc in response:
                score = SOG_score_vendors(doc, SOG_response, docs_dict, sim_matrix)
                if score > max_score:
                    max_score = score
                    best_doc = doc
            SOG_response.append(response.pop(response.index(best_doc)))

        print()
        for num, doc in enumerate(SOG_response):
            print(num, "--", doc['_source']['name'])
        return {'response': SOG_response}
    return {'response': response}
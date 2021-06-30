from ..dependencies import config
from ..methods.natural_languaje_processing import *
from elasticsearch import Elasticsearch
import pickle
from ..models.actions import *
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from scipy.sparse import vstack

# ElasticSearch initialization

es = Elasticsearch(
    [config('ELASTIC_DIR')],
    http_auth=(config('ELASTIC_USR'), config('ELASTIC_PWD')),
    scheme="http",
    port=config('ELASTIC_PORT')
)

def vectorize_products():
    corpus = []
    vectorizer = CountVectorizer()
    """ 
            "query": {
            "filtered": {
                "query": {
                    "match_all": {}
                },
                "filter": {
                    "bool": {
                        "must_not": [
                            {
                                "term": {
                                    "_source.taxons.id": "305"
                                }
                            }
                        ]
                    }
                }
            }
        }
    
     """
    search_dict = {
        'query': {
            'match_all': {}
        },
        'size': 10000,  # máximo admisible actualmente
    }

    response = es.search(index="spree-products", body=search_dict)
    response_hits = response['hits']['hits']

    print(response_hits[0])

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

    vec = vectorizer.fit(corpus)  
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
    return "Products model updated"
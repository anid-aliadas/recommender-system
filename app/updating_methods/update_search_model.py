from ..dependencies import config
from ..methods.natural_languaje_processing import *
import pickle
from ..models.actions import *
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from scipy.sparse import vstack
import requests

def vectorize_products():
    url = config('SPREE_PRODUCTS_URL')
    headers = {
        "X-Spree-Token": config('SPREE_API_KEY')
    } 
    params = {
        "page": 0,
        "per_page": 1000,
        "excluded_taxon_ids[]": 305,
    }
    all_products = []
    response = ""
    while( response != [] ):
        response = requests.get(url, headers=headers, params=params).json()['response']

        #condicion de error en response
        
        all_products += response
        params["page"] += 1
    corpus = []
    vectorizer = CountVectorizer()

    docs_dict = {}
    for num, doc in enumerate(all_products):
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
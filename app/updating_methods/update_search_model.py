from ..dependencies import config
from ..methods.natural_languaje_processing import *
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from scipy.sparse import vstack
import requests

def vectorize_products():
    print("* Updating products search model\n*")
    url = config('SPREE_PRODUCTS_URL')
    headers = {
        "X-Spree-Token": config('SPREE_API_KEY')
    } 
    params = {
        "page": 0,
        "per_page": 1000,
        "excluded_taxon_ids[]": 305,
    }
    print("*    1/8 - Retrieving products data from spree")
    all_products = []
    response = requests.get(url, headers=headers, params=params).json()['response']
    while( not isinstance(response, str) and response != [] ):
        all_products += response
        params["page"] += 1
        response = requests.get(url, headers=headers, params=params).json()['response']
    if all_products == []: return "*\n* PRODUCTS SEARCH MODEL NOT UPDATED, SPREE DATA RETURNED NULL"
    corpus = []
    vectorizer = CountVectorizer()

    print("*    2/8 - Obtaining cleaned corpus from all products words")
    docs_dict = {}
    for num, doc in enumerate(all_products):
        doc_id = doc['_source']['id']
        doc_name = doc['_source']['name']
        doc_description = doc['_source']['description']
        docs_dict[doc_id] = {'local_index': num, 'name': doc_name, 'description': doc_description}

        cleaned_text = accent_mark_removal(clean_text_round2(clean_text_round1(doc_name + ' ' + str(doc_description))))
        docs_dict[doc_id]['cleaned_vocabulary'] = list(set(cleaned_text.split(' ')))
        corpus.append(cleaned_text)

    print("*    3/8 - Vectorizing corpus")
    vec = vectorizer.fit(corpus)  
    X = vec.transform(corpus) #corpus vecs

    print("*    4/8 - Obtaining top n frequents meaningfull words from vocabulary")
    top_vocabulary = get_top_vocabulary(X, vec, float(config('TOP_N_VOCAB_WORDS_PERCENTAGE')))

    print("*    5/8 - Calculating vectorization matrix centroid for future use")
    centroid = X.mean(axis=0) #vecs means
    X = vstack([X, centroid]) #add centroid to position -1

    print("*    6/8 - Calculating SOG 'unpop' parameter for the vectorization matrix")
    for doc_id in docs_dict:
        docs_dict[doc_id]['unpop'] = 1 - len(np.intersect1d(docs_dict[doc_id]['cleaned_vocabulary'], top_vocabulary))/len(top_vocabulary)
    docs_dict.update({ -1 : { 'unpop' : 0 } })

    print("*    7/8 - Calculating cosine similarity for the vectorization matrix")
    X = cosine_similarity(X) # The value in the i-th row and j-th column of the result is the cosine similarity between the i-th and j-th row of array.

    print("*    8/8 - Saving data")
    with open('app/files/products/data.pkl', 'wb') as f:
        pickle.dump(docs_dict, f)
        f.close()
    with open('app/files/products/top_vocabulary.pkl', 'wb') as f:
        pickle.dump(top_vocabulary, f)
        f.close()
    with open('app/files/products/similarities_matrix.pkl', 'wb') as f:
        pickle.dump(X, f)
        f.close()
    return "*\n* Products search model updated!"
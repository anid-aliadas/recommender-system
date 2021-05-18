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

def SOG_score_vendors(doc, candidate_set, docs_dict, sim_matrix):
    score = 0
    div_iB = 0
    product_index = docs_dict[int(doc['_id'])]['local_index']
    unpop_i = docs_dict[int(doc['_id'])]['unpop']
    for candidate_doc in candidate_set:
        candidate_index = docs_dict[int(candidate_doc['_id'])]['local_index']
        div_iB += (1 - sim_matrix[product_index][candidate_index])
    product_score = doc['_score']

    score += 0.3 * product_score + 0.5 * (div_iB/len(candidate_set)) + 0.2 * unpop_i
    return score


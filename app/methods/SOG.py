def SOG_score_elastic(doc, candidate_set, docs_dict, sim_matrix):
    score = 0
    div_iB = 0
    n = 0
    product_index = docs_dict.get(int(doc['_id']), { 'local_index': -1 } ).get('local_index') #si no esta en el modelo toma el centroide
    product_vendor = doc['_source']['vendor']['name']
    unpop_i = docs_dict.get(int(doc['_id']), { 'unpop': 0 } ).get('unpop') #si no esta en el modelo, unpop = 0
    for candidate_doc in candidate_set:
        candidate_vendor = candidate_doc['_source']['vendor']['name']
        candidate_index = docs_dict.get(int(candidate_doc['_id']), { 'local_index': -1 } ).get('local_index')
        div_iB += (1 - sim_matrix[product_index][candidate_index])
        if product_vendor == candidate_vendor: n += 1
    product_score = doc['_score']
    div_vendor_iB = 1/(n+1)

    #comparar doc_vendor contra todos los vendors del candidate_Set
    #Si no lo encontramos (doc_vendor) se el asigna prob V.import
    #Si lo encontramos se le asigna prov V/n+1 donde n es la cantidad de apariciones en candidate_Set
    score += 0.2 * product_score + 0.4 * (div_iB/len(candidate_set)) + 0.2 * unpop_i + 0.2 * div_vendor_iB
    return score

def calc_SOG_prof_ui(top_items, user_data, items_similarity_matrix):
    SOG_prof_ui = {}
    n = len(user_data)
    for i_item, _ in top_items:
        prof_ui = 0
        for u_item in user_data:
            prof_ui += (1 - items_similarity_matrix[i_item][u_item])
        SOG_prof_ui[i_item] = prof_ui/n
    return SOG_prof_ui


def SOG_score_predictions(item_data, candidate_set, prof_ui, unpop_i, items_similarity_matrix):
    score = 0
    div_iB = 0
    i_item_index, i_item_relevance = item_data
    for c_item_index, _ in candidate_set:
        div_iB += (1 - items_similarity_matrix[i_item_index][c_item_index])
    score += 0.1 * i_item_relevance + 0.5 * (div_iB/len(candidate_set)) + 0.2 * prof_ui + 0.2 * unpop_i 
    return score
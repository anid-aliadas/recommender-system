from ..dependencies import config

def SOG_score_elastic(doc, candidate_set, docs_dict, sim_matrix, prof_ui, SOG_params_weights):
    if SOG_params_weights:
        ES_SOG_REL_PARAM_W = SOG_params_weights[0]
        ES_SOG_DIV_PARAM_W = SOG_params_weights[1]
        ES_SOG_PROF_UI_PARAM_W = SOG_params_weights[2]
        ES_SOG_UNPOP_I_PARAM_W = SOG_params_weights[3]
        ES_SOG_DIV_VEN_PARAM_W = SOG_params_weights[4]
    else:
        ES_SOG_REL_PARAM_W = float(config('ES_SOG_REL_PARAM_W'))
        ES_SOG_DIV_PARAM_W = float(config('ES_SOG_DIV_PARAM_W'))
        ES_SOG_PROF_UI_PARAM_W = float(config('ES_SOG_PROF_UI_PARAM_W'))
        ES_SOG_UNPOP_I_PARAM_W = float(config('ES_SOG_UNPOP_I_PARAM_W'))
        ES_SOG_DIV_VEN_PARAM_W = float(config('ES_SOG_DIV_VEN_PARAM_W'))
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
    #Si no lo encontramos (doc_vendor) se le asigna prob V.import
    #Si lo encontramos se le asigna prob V/n+1 donde n es la cantidad de apariciones en candidate_Set
    score += ES_SOG_REL_PARAM_W     * product_score                     \
          +  ES_SOG_DIV_PARAM_W     * (div_iB/len(candidate_set))       \
          +  ES_SOG_PROF_UI_PARAM_W * prof_ui.get(int(doc['_id']), 0)   \
          +  ES_SOG_UNPOP_I_PARAM_W * unpop_i                           \
          +  ES_SOG_DIV_VEN_PARAM_W * div_vendor_iB
    return score

def filter_products_ids(ids_array, products_data):
    return [products_data[i]['local_index'] if i in products_data else -1 for i in ids_array]

def calc_SOG_prof_ui_search(historical_items_ids, search_items_ids, items_similarity_matrix, products_data):
    SOG_prof_ui = {}
    for item_id in search_items_ids:
        if item_id not in products_data: SOG_prof_ui[item_id] = 1 - items_similarity_matrix[-1, historical_items_ids].mean()
        else: SOG_prof_ui[item_id] = 1 - items_similarity_matrix[[products_data[item_id]['local_index']], historical_items_ids].mean()
    return SOG_prof_ui

def calc_SOG_prof_ui(top_items, user_data, items_similarity_matrix):
    n = len(user_data)
    SOG_prof_ui = {}
    if n > 0:
        for i_item, _ in top_items:
            prof_ui = 0
            for u_item in user_data:
                prof_ui += (1 - items_similarity_matrix[i_item][u_item])
            SOG_prof_ui[i_item] = prof_ui/n
    return SOG_prof_ui

def SOG_score_predictions(item_data, candidate_set, prof_ui, unpop_i, items_similarity_matrix):
    RS_SOG_REL_PARAM_W = float(config('RS_SOG_REL_PARAM_W'))
    RS_SOG_DIV_PARAM_W = float(config('RS_SOG_DIV_PARAM_W'))
    RS_SOG_PROF_UI_PARAM_W = float(config('RS_SOG_PROF_UI_PARAM_W'))
    RS_SOG_UNPOP_I_PARAM_W = float(config('RS_SOG_UNPOP_I_PARAM_W'))
    score = 0
    div_iB = 0
    i_item_index, i_item_relevance = item_data
    for c_item_index, _ in candidate_set:
        div_iB += (1 - items_similarity_matrix[i_item_index][c_item_index])
    score += RS_SOG_REL_PARAM_W     * i_item_relevance \
          +  RS_SOG_DIV_PARAM_W     * (div_iB/len(candidate_set)) \
          +  RS_SOG_PROF_UI_PARAM_W * prof_ui \
          +  RS_SOG_UNPOP_I_PARAM_W * unpop_i 
    return score

def SOG_predictions(out, SOG_prof_ui, RS):
    SOG_response = []
    SOG_response.append(out['r'].pop(0))
    for i in range(len(out['r'])):
        max_score = -1
        for item_data in out['r']:
            score = SOG_score_predictions(
                item_data, 
                SOG_response, 
                SOG_prof_ui.get(item_data[0], 0), 
                RS.unpop[0, item_data[0]], 
                RS.items_similarity_matrix
            )
            if score > max_score:
                max_score = score
                best_item = item_data
        SOG_response.append(out['r'].pop(out['r'].index(best_item)))
    return SOG_response
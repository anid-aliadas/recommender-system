'''
COLLABORATIVE FILTERING
Implements a basic CR algorithm with:
    - Mean normalization (centering mean at 0)
    - STD normalization (setting STD at 1)
    - Alpha amplication (amplifying user similarity, use an exponentiation of alpha to increase
        the influence of most similar users to the target user in the calculation of the predicted value)

Given a target user, recommendations are calculated considering the set of the most similar users
in the collection to the target user (let us call this set S).
The cardinality of S  is passed as a parameter.  
The predicted value for the target user and a given item is the weighted sum over the ratings
of users in S.
Weights in the sum corresponds to the cosine similarity between the target user and a user in S.

Additionally, ratings can be normalized to have an average of 0 and a standard deviation of 1 (for all users).

The Recommender class makes the prediction as follows:
Constructor:
1. Receives sparse matrix X with m rows (users) and n columns (items).
    -> Calculates sparse matrix mask that contains 1 where ratings should be
2. Calculates vector Xmeans with the mean value for each row in X.
3. Calculates vector Xmeans2 with the mean of squared values for each row in X.
4. Calculates vector std with the standard deviation calculated as \sqrt(Xmeans2 - Xmeans^2)
5. Normalizes X
6. Calcualtes the Frobenious norm for each row vector in X in row_norms
Prediction:
7. Calculates vector Y as the matrix multiplication of X with X[target_user]^T
8. Calculates vector Z as the scalar multiplication between vector row_norms and the scalar row_norms[target_user]
9. Calculates vector W as the element-wise division between values in Y and Z
    -> W is the vector of cosine similarity between all users in the collection and the target user
10. Choose from W the set of most similar users w.r.t. the target user for a given threshold top_users
    -> the target user is the most similar to itself so we have to remove him
11. Calculate subvector subW from W containing only the similarities of the most similar users to the target user
12. Calculate submatrix subX containing only those rows in X that corresponds to the most similar users to the target user
    -> Calculate submatrix submask similarly
13. Calculate vector N as the matrix multiplication of subX^T (transposed) with vector subW.
    - N has one value per item calculated as the weighted sum between the rating of a user (in subX) 
        and the similarity of that user to the target user (in subW)
14. Calculate vector D as the matrix multiplication of submask^T with vector subW.
    - D has one value per item calculates as the sum of similarities of users in subW that rated that item
15. Calculate vector R as the element-wise division between elements in N and elements in D
    - R has one value per item corresponding to the normalized predicted rating value given to that item by the target user
16. Denormalize values in R by multiplying by the standard deviation (if necessary) and summing the average rating for the target user (if necessary)
17. Either choose the largest predicted values as the recommendation or retrieve R
'''


import heapq
import numpy as np
from collections import defaultdict
from scipy.spatial import distance
from scipy.sparse import csr_matrix, diags
from sklearn.metrics.pairwise import cosine_similarity

class RecommenderUserModel(object):
    def __init__(self, RS, W, row_i):
        self.RS = RS
        self.W = W
        self.row_i = row_i

    def predict(self, item_j, top_users=0.1, alpha=1, limits=(0,5)):
        if top_users < 1:
            top_users = int(self.RS.X.shape[0])

        # Choose top users to recommend (plus 1, the target user is always selected)
        top_user_indices = heapq.nlargest(top_users+1, range(len(self.W)), self.W.take)
        # Remove target user from recommenders
        top_user_indices.remove(self.row_i)
        
        subX = self.RS.X[top_user_indices,item_j] # Submatrix with recommenders
        subW = self.W[top_user_indices] # Submatrix with similarities to recommenders
        submask = self.RS.mask[top_user_indices, item_j] # Submask with recommenders
        
        # Recalibrate with alpha
        subW = np.sign(subW) * np.abs(subW)**alpha

        # Calculate recommended ratings
        N = subX.T @ subW
        D = submask.T @ np.abs(subW)
        R = np.true_divide(N, D, out=np.zeros(N.shape), where=D!=0)

        # Denormalize predicted ratings
        if self.normalized:
            if self.normalized_std:
                R *= self.std[self.row_i]  
            R  += self.Xmean[self.row_i]
        
        out = {}
        out['std'] = self.std[self.row_i]
        if limits is None:
            out['r'] = {item_j:R[item_j]}
        else:
            out['r'] = {item_j:max(min(R[item_j], limits[1]),limits[0])}
        out['similarity'] = subW
        out['mean'] = self.Xmean[self.row_i]
        out['users'] = top_user_indices
        return out


class Recommender(object):
    '''
    Collaborative filtering recommender
    '''
    def __init__(self, X, XI, normalize=False, normalize_std=False):
        '''
        X: np.array where rows are users and columns are items
        normalize: bool whether to normalize the matrix or not
        '''
        self.X = X # dataset
        self.XI = XI # users interests
        self.users_similarity_matrix = cosine_similarity(X)
        self.items_similarity_matrix = cosine_similarity(X.T)
        self.unpop = X.sum(axis=0)/X.shape[0]

        self.users_data = {}
        self.unique_users = []
        self.unique_items = []

        self.Xmean = np.squeeze(np.asarray(np.true_divide( X.sum(1), (X!=0).sum(1), out=np.zeros((X.shape[0], 1)), where=(X!=0).sum(1) != 0 ))) # mean rating for all users
        self.Xmean2 = np.squeeze(np.asarray(np.true_divide( X.power(2).sum(1),(X!=0).sum(1), out=np.zeros((X.shape[0], 1)), where=(X!=0).sum(1) != 0 ))) # mean of squared values for all users
        self.std = np.sqrt(self.Xmean2 - self.Xmean**2)# [1/i if i != 0 else float('inf') for i in np.sqrt(self.Xmean2 - self.Xmean**2)] # sqrt(E[X**2] - E[X]**2) ; inverted as they will be used for normalizing 
        
        self.normalized = False
        self.normalized_std = normalize_std
        # The mask is a matrix with the same shape to the dataset
        # however it has ones where a value exists
        self.mask = X.copy()
        self.mask.data = np.ones_like(self.mask.data)

        # Normalize
        if normalize:
            #print(np.std(self.X, axis=0))
            self.normalized = True
            diagonal_means = diags(self.Xmean, 0)
            self.X =  X - diagonal_means*self.mask
            if normalize_std:
                self.X = diags([1/i if i != 0 else float('inf') for i in self.std]) @ self.X

        # Calculate row Frobenius' norms
        self.row_norms = np.sqrt(np.squeeze(np.asarray(self.X.power(2).sum(1))))
        
    
    def recommend(self, row_i, top_users=3, top_items=3, alpha=1, beta=0.7, limits=(0,5)):
        '''
        Calculates recommended items for user row_i in matrix X
        
        row_i: int row number for the target user
        top_users: int number of users to consider similar to target user
        top_items: int number items to recommend
        alpha: float similarity amplification. Values over 1 amplify most similar users.
        limits: tuple of values - limits to truncate the predicted value

        returns dictionary where keys are items and values are predicted ratings
        '''
        # Calculate cosine distance to all users in the dataset
        Y = np.squeeze(np.asarray((self.X * self.X[row_i].T).todense()))
        Z = self.row_norms * self.row_norms[row_i]
        cos_sim = np.true_divide(Y, Z, out=np.zeros(Y.shape), where=Z!=0)

        # Calculate Jaccard similarity to all users in the interests matrix
        A = np.squeeze(np.asarray((self.XI * self.XI[row_i].T).todense()))
        B = np.squeeze(np.asarray(self.XI.sum(1) + self.XI[row_i].sum(1))) - A
        jacc_sim = np.true_divide(A, B, out=np.zeros(A.shape), where=B!=0)

        W =  beta * cos_sim + (1 - beta) * jacc_sim
        # Choose top users to recommend (plus 1, the target user is always selected)
        top_user_indices = heapq.nlargest(top_users+1, range(len(W)), W.take)

        # Remove target user from recommenders
        if row_i in top_user_indices: top_user_indices.remove(row_i)
        
        subX = self.X[top_user_indices,:] # Submatrix with recommenders
        subW = W[top_user_indices] # Submatrix with similarities to recommenders
        submask = self.mask[top_user_indices] # Submask with recommenders
        
        # Recalibrate with alpha
        subW = np.sign(subW) * np.abs(subW)**alpha

        # Calculate recommended ratings
        N = subX.T @ subW
        D = submask.T @ np.abs(subW)
        R = np.true_divide(N, D, out=np.zeros(N.shape), where=D!=0)
        
        # Denormalize predicted ratings
        if self.normalized:
            if self.normalized_std:
                R *= self.std[row_i]  
            R  += self.Xmean[row_i]
        
        # Remove items already rated by user
        excluded_items = self.X[row_i].nonzero()[1]
        R[excluded_items] = float('-inf')
        
        # Choose top items for recommendation
        top_item_indices = heapq.nlargest(top_items, range(len(R)), R.take)
        out = {}

        out['std'] = self.std[row_i]
        if limits is None:
            out['r'] = [(i, R[i]) for i in top_item_indices]
        else:
            out['r'] = {i:max(min(R[i], limits[1]),limits[0]) for i in top_item_indices}
        
        out['similarity'] = subW
        out['mean'] = self.Xmean[row_i]
        out['users'] = top_user_indices
        return out
    

    def check_recommendations(self, row_i, recs, top_users=3, alpha=1, limits=(0,5)):
        '''
        Returns the recommended value of target user (row_i) for items in recs
        '''
        # Numeradores
        Y = np.squeeze(np.asarray((self.X * self.X[row_i].T).todense()))
        # Divisores
        Z = self.row_norms * self.row_norms[row_i]
        # Similaridades
        W = np.true_divide(Y, Z, out=np.zeros(Y.shape), where=Z!=0)
        
        top_user_indices = heapq.nlargest(top_users+1, range(len(W)), W.take)
        top_user_indices.remove(row_i)

        subX = self.X[top_user_indices,:]
        subW = W[top_user_indices]
        submask = self.mask[top_user_indices]

        # Recalibrate with alpha
        subW = np.sign(subW) * np.abs(subW)**alpha

        N = subX.T @ subW
        D = submask.T @ subW
        R = np.true_divide(N, D, out=np.zeros(N.shape), where=D!=0)

        
        # Denormalize predicted ratings
        if self.normalized:
            if self.normalized_std:
                R *= self.std[row_i]  
            R  += self.Xmean[row_i]
        
        out = {}
        out['std'] = self.std[row_i]
        if limits is None:
            out['r'] = {i:R[i] for i in recs}
        else:
            out['r'] = {i:max(min(R[i], limits[1]),limits[0]) for i in recs}
        out['similarity'] = subW
        out['mean'] = self.Xmean[row_i]
        out['users'] = top_user_indices
        return out
        

def exec():
    '''
    Executes a test on a toy example and verifies predictions by the Recommender class
    '''
    TOP_USERS = 2
    TOP_ITEMS = 2
    ALPHA = 1.3

    data = [1,1,1,1,1,1,1,1,1,1,1,1,1]
    row_ind = [0,0,0,1,1,1,1,2,2,2,2,3,3]
    col_ind = [0,3,4,0,1,2,5,3,4,5,6,1,6]
    
    X = csr_matrix((data, (row_ind, col_ind)))
    print('*'*100)
    print("Original Matrix")
    print(X.todense())
    print('*'*100)
    print("Normalized Matrix")
    row_i = 1
    RS = Recommender(X, normalize=True, normalize_std=True)
    print(RS.X.todense())
    out = RS.recommend(row_i, top_users=TOP_USERS, top_items=TOP_ITEMS, alpha=ALPHA)
    print('*'*100)
    print("Recommendations for user {}:".format(row_i))
    for i, j in out['r'].items():
        print("\t -> Recommended: item {} with rating {:.5g}".format(i, j))
    print("Target user average rating:", out['mean'])
    print("Target user standard deviation rating: {:.5g}".format(out['std']))
    print("Chosen recommenders (users):", out['users'])
    print("Chosen similarities (users):", out['similarity'])
    print('*'*100)
    print("Validation: ")
    
    s = [((1-(distance.cosine(RS.X[row_i].todense(), RS.X[i].todense()) if RS.row_norms[i] != 0 else 1)), i) for i in range(RS.X.shape[0]) if i != row_i]
    # Recalibrate with ALPHA
    s = [(np.sign(i) * np.abs(i)**ALPHA, j) for i,j in s]
    
    s.sort(reverse=True)
    print("\tTop users:")
    for i, j in s[:TOP_USERS]:
        print("\t\t -> User {}: {:.5g}".format(j, i))
    

    print('\tPredicted Ratings:')
    pred_items = []
    for item in range(RS.X.shape[1]):
        if item not in RS.X[row_i].nonzero()[1]:
            print("\t\t->Predicted rating for item {}".format(item))
            o = []
            p = 0
            d = 0
            for sim, user in s[:TOP_USERS]:
                if RS.X.todense()[user,item] != 0:
                    o.append("({:.5g} * {:.5g})".format(sim, RS.X.todense()[user,item]))
                    p+= sim * RS.X.todense()[user,item]
                    d+=sim
            
            pred_rat = (out['std']*p)/d + out['mean']
            print('\t\t\t-> {} + ({:.5g}*({}))/{:.5g} = {:.5g}'.format(out['mean'], out['std'], " + ".join(o), d,  pred_rat))
            pred_items.append((pred_rat, item))
                    
    pred_items.sort(reverse=True)
    print("\tTop Items:")
    for i, j in pred_items[:TOP_ITEMS]:
        print("\t\t -> Item {}: {:.5g}".format(j, i))
    print("Test Selected Users and Similarities:", all(i==k[1] and round(j,5)==round(k[0],5) for i, j, k in zip(out['users'],out['similarity'], s)) )
    print("Test Predicted Ratings:", all(i[0]==j[1] and round(i[1], 5)==round(j[0],5) for i, j in zip(out['r'].items(),  pred_items[:TOP_ITEMS])) )


if __name__ == "__main__":
    exec()
    
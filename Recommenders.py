# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 19:08:46 2020

@author: shris
"""
# contains the class for popularity recommender system and item similarity (collaborative filtering ) recommender
import numpy as np
import pandas

#Class for Popularity based Recommender System model
class popularity_recommender_py():
    def __init__(self):
        self.train_data = None
        self.uid = None
        self.title = None
        self.popularity_recommendations = None
        
    #Create the popularity based recommender system model
    def create(self, train_data, uid, title):
        self.train_data = train_data
        self.uid = uid
        self.title = title

        #Get a count of uids for each unique book as recommendation score
        train_data_grouped = train_data.groupby([self.title]).agg({self.uid: 'count'}).reset_index()
        train_data_grouped.rename(columns = {'uid': 'score'},inplace=True)
    
        #Sort the books based upon recommendation score
        train_data_sort = train_data_grouped.sort_values(['score', self.title], ascending = [0,1])
    
        #Generate a recommendation rank based upon score
        train_data_sort['Rank'] = train_data_sort['score'].rank(ascending=0, method='first')
        
        #Get the top 10 recommendations
        self.popularity_recommendations = train_data_sort.head(10)

    #Use the popularity based recommender system model to
    #make recommendations
    def recommend(self, uid):    
        user_recommendations = self.popularity_recommendations
        
        #Add uid column for which the recommendations are being generated
        user_recommendations['uid'] = uid
    
        #Bring uid column to the front
        cols = user_recommendations.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        user_recommendations = user_recommendations[cols]
        
        return user_recommendations
    

#Class for Item similarity based Recommender System model
class item_similarity_recommender_py():
    def __init__(self):
        self.train_data = None
        self.uid = None
        self.title = None
        self.cooccurence_matrix = None
        self.books_dict = None
        self.rev_books_dict = None
        self.item_similarity_recommendations = None
        
    #Get unique items (books) corresponding to a given user
    def get_user_items(self, user):
        user_data = self.train_data[self.train_data[self.uid] == user]
        user_items = list(user_data[self.title].unique())
        return user_items
        
    #Get unique users for a given item (book)
    def get_item_users(self, item):
        item_data = self.train_data[self.train_data[self.title] == item]
        item_users = set(item_data[self.uid].unique())
        return item_users
        
    #Get unique items (books) in the training data
    def get_all_items_train_data(self):
        all_items = list(self.train_data[self.title].unique())          
        return all_items
        
    #Construct cooccurence matrix
    def construct_cooccurence_matrix(self, user_books, all_books):
            
        ####################################
        #Get users for all books in user_books.
        ####################################
        user_books_users = []        
        for i in range(0, len(user_books)):
            user_books_users.append(self.get_item_users(user_books[i]))
            
        ###############################################
        #Initialize the item cooccurence matrix of size 
        #len(user_books) X len(books)
        ###############################################
        cooccurence_matrix = np.matrix(np.zeros(shape=(len(user_books), len(all_books))), float)
           
        #############################################################
        #Calculate similarity between user books and all unique books
        #in the training data
        #############################################################
        for i in range(0,len(all_books)):
            #Calculate unique listeners (users) of book (item) i
            books_i_data = self.train_data[self.train_data[self.title] == all_books[i]]
            users_i = set(books_i_data[self.uid].unique())
            
            for j in range(0,len(user_books)):       
                    
                #Get unique listeners (users) of book (item) j
                users_j = user_books_users[j]

                    
                #Calculate intersection of listeners of books i and j
                users_intersection = users_i.intersection(users_j)

                
                
                #Calculate cooccurence_matrix[i,j] as Jaccard Index
                if len(users_intersection) != 0:
                    #Calculate union of listeners of books i and j
                    users_union = users_i.union(users_j)
                    
                    cooccurence_matrix[j,i] = float(len(users_intersection))/float(len(users_union))
                else:
                    cooccurence_matrix[j,i] = 0
        return cooccurence_matrix

    
    #Use the cooccurence matrix to make top recommendations
    def generate_top_recommendations(self, user, cooccurence_matrix, all_books, user_books):
        print("Non zero values in cooccurence_matrix :%d" % np.count_nonzero(cooccurence_matrix))
        
        #Calculate a weighted average of the scores in cooccurence matrix for all user books.
        user_sim_scores = cooccurence_matrix.sum(axis=0)/float(cooccurence_matrix.shape[0])
        user_sim_scores = np.array(user_sim_scores)[0].tolist()
 
        #Sort the indices of user_sim_scores based upon their value
        #Also maintain the corresponding score
        sort_index = sorted(((e,i) for i,e in enumerate(list(user_sim_scores))), reverse=True)
    
        #Create a dataframe from the following
        columns = ['uid', 'book', 'score', 'rank']
        #index = np.arange(1) # array of numbers for the number of samples
        df = pandas.DataFrame(columns=columns)
         
        #Fill the dataframe with top 10 item based recommendations
        rank = 1 
        for i in range(0,len(sort_index)):
            if ~np.isnan(sort_index[i][0]) and all_books[sort_index[i][1]] not in user_books and rank <= 10:
                df.loc[len(df)]=[user,all_books[sort_index[i][1]],sort_index[i][0],rank]
                rank = rank+1
        
        #Handle the case where there are no recommendations
        if df.shape[0] == 0:
            print("The current user has no books for training the item similarity based recommendation model.")
            return -1
        else:
            return df
 
    #Create the item similarity based recommender system model
    def create(self, train_data, uid, title):
        self.train_data = train_data
        self.uid = uid
        self.title = title

    #Use the item similarity based recommender system model to
    #make recommendations
    def recommend(self, user):
        
        ########################################
        #A. Get all unique books for this user
        ########################################
        user_books = self.get_user_items(user)    
            
        print("No. of unique books for the user: %d" % len(user_books))
        
        ######################################################
        #B. Get all unique items (books) in the training data
        ######################################################
        all_books = self.get_all_items_train_data()
        
        print("no. of unique books in the training set: %d" % len(all_books))
         
        ###############################################
        #C. Construct item cooccurence matrix of size 
        #len(user_books) X len(books)
        ###############################################
        cooccurence_matrix = self.construct_cooccurence_matrix(user_books, all_books)
        
        #######################################################
        #D. Use the cooccurence matrix to make recommendations
        #######################################################
        df_recommendations = self.generate_top_recommendations(user, cooccurence_matrix, all_books, user_books)
                
        return df_recommendations
    
    #Get similar items to given items
    def get_similar_items(self, item_list):
        
        user_books = item_list
        
        ######################################################
        #B. Get all unique items (books) in the training data
        ######################################################
        all_books = self.get_all_items_train_data()
        
        print("no. of unique books in the training set: %d" % len(all_books))
         
        ###############################################
        #C. Construct item cooccurence matrix of size 
        #len(user_books) X len(books)
        ###############################################
        cooccurence_matrix = self.construct_cooccurence_matrix(user_books, all_books)
        
        #######################################################
        #D. Use the cooccurence matrix to make recommendations
        #######################################################
        user = ""
        df_recommendations = self.generate_top_recommendations(user, cooccurence_matrix, all_books, user_books)
         
        return df_recommendations
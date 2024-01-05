# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 18:02:28 2020
Updated on Thu Feb 20 18:18:37 2020
@author: shris
"""
# Importing libraries
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pandas as pd
from sklearn.model_selection import train_test_split
import Recommenders as Recommenders

# Initialize Firebase Admin SDK
cred = credentials.Certificate('')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Delete old data from 'popular_books' collection
popular_collection_ref = db.collection('popular_books')
old_popular_books = popular_collection_ref.get()
for book in old_popular_books:
    book.reference.delete()

# Delete old data from 'recommended_books' collection
recommended_collection_ref = db.collection('recommended_books')
old_recommended_books = recommended_colleserviceAccountKey.jsonction_ref.get()
for book in old_recommended_books:
    book.reference.delete()

# Delete old data from 'similar_books' collection
similar_collection_ref = db.collection('similar_books')
old_similar_books = similar_collection_ref.get()
for book in old_similar_books:
    book.reference.delete()

# Fetch book metadata from the 'eBook' collection
book_metadata_collection = db.collection('eBook').get()
book_metadata_file = [doc.to_dict() for doc in book_metadata_collection]
book_df_2 = pd.DataFrame(book_metadata_file)

# Fetch book triplets from the 'ratings' collection
triplets_collection = db.collection('ratings').get()
triplets_file = [doc.to_dict() for doc in triplets_collection]
book_df_1 = pd.DataFrame(triplets_file)

# Merging both and removing duplicates using book ID which is unique
book_df = pd.merge(book_df_1, book_df_2.drop_duplicates(['title']), on="title", how="left")

# Combining book with its author name 
book_df['book'] = book_df['title'].map(str) + ""

# Calculating the most popular book by calculating the listen count from all users in the dataset
# and also calculating its percentage with respect to other unique books.
book_grouped = book_df.groupby(['book']).agg({'readingCount': 'count'}).reset_index()
grouped_sum = book_grouped['readingCount'].sum()
book_grouped['percentage']  = book_grouped['readingCount'].div(grouped_sum)*100
book_grouped.sort_values(['readingCount', 'book'], ascending=[0, 1])

users = book_df['uid'].unique()
books = book_df['book'].unique()

# Split the dataset into test and train data
train_data, test_data = train_test_split(book_df, test_size=0.20, random_state=0)

# Popularity-based Recommender
pm = Recommenders.popularity_recommender_py()
pm.create(train_data, 'uid', 'book')

# Store the most popular books in the 'popular_books' collection
popular_collection_ref = db.collection('popular_books')
for idx, row in pm.popularity_recommendations.iterrows():
    book_details = book_df.loc[book_df['book'] == row['book']]
    doc_data = {
        'title': book_details['title'].values[0],
        'author': book_details['author'].values[0],
        'image': book_details['image'].values[0],
        'id': book_details['id'].values[0],
        'year': book_details['year'].values[0],
        'link': book_details['link'].values[0],
        'page': book_details['page'].values[0],
        'description': book_details['description'].values[0],
        'genres': book_details['genres'].values[0],
        'readingCount': row['score'],
        
    }
    popular_collection_ref.add(doc_data)

# Show the popular books (only once)
print("------------------------------------------------------------------------------------")
print("Most Popular Books (Popularity-based Recommender)")
print("------------------------------------------------------------------------------------")
print(pm.popularity_recommendations)

# Item Similarity-based Recommender
is_model = Recommenders.item_similarity_recommender_py()
is_model.create(train_data, 'uid', 'book')

# Iterate over each user and get recommendations
# Store recommended books in the 'recommended_books' collection for each user
# recommended_collection_ref = db.collection('recommended_books')
# for uid in users:
#     print("------------------------------------------------------------------------------------")
#     print(f"Recommendations for user with uid: {uid} (Item Similarity-based Recommender)")
#     print("------------------------------------------------------------------------------------")
#     recommend = is_model.recommend(uid)
#     print(recommend)
#     for idx, row in recommend.iterrows():
#         book_details = book_df.loc[book_df['book'] == row['book']]
#         doc_data = {
#             'uid': uid,
#             'title': book_details['title'].values[0],
#             'author': book_details['author'].values[0],
#             'image': book_details['image'].values[0],
#             'id': book_details['id'].values[0],
#             'year': book_details['year'].values[0],
#             'link': book_details['link'].values[0],
#             'page': book_details['page'].values[0],
#             'description': book_details['description'].values[0],
#             'genres': book_details['genres'].values[0],
#             'rank': idx + 1,
#             'score': row['score'],
#         }
#         recommended_collection_ref.add(doc_data)

# Iterate over each book and get similar books
# Store similar books in the 'similar_books' collection for each book
similar_collection_ref = db.collection('similar_books')
for book in books:
    print("------------------------------------------------------------------------------------")
    print(f"Similar books for the book: {book}")
    print("------------------------------------------------------------------------------------")
    similar_books = is_model.get_similar_items([book])
    print(similar_books)
    for idx, row in similar_books.iterrows():
        book_details = book_df.loc[book_df['book'] == row['book']]
        doc_data = {
            'book': book,
            'title': book_details['title'].values[0],
            'author': book_details['author'].values[0],
            'image': book_details['image'].values[0],
            'id': book_details['id'].values[0],
            'year': book_details['year'].values[0],
            'link': book_details['link'].values[0],
            'page': book_details['page'].values[0],
            'description': book_details['description'].values[0],
            'genres': book_details['genres'].values[0],
            'rank': idx + 1,
            'score': row['score'],
        }
        similar_collection_ref.add(doc_data)
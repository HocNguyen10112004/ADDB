from pymongo import MongoClient

def connectToMongoDB():
    # Kết nối đến MongoDB Atlas
    client = MongoClient('')
    db = client['social_data']  # Kết nối đến database 'social_data'
    return client, db  # Trả về cả client và db

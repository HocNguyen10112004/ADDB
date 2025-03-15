from flask import Blueprint, render_template
from connect import connectToMongoDB
from pyspark.sql import SparkSession
from spark import init_spark
home_bp = Blueprint('home', __name__)
import pandas as pd
# Kết nối MongoDB
client, db = connectToMongoDB()

@home_bp.route('/')
def home():
    # Lấy tất cả các bài đăng từ collection 'posts'
    posts = db.posts.find()

    # # Lấy các bình luận tương ứng với từng bài đăng từ collection 'comments'
    # # Mỗi bình luận có trường 'post_id' để liên kết với bài đăng
    posts_with_comments = []
    for post in posts:
        comments = db.comments.find({'post_id': post['_id']})
        post['comments'] = list(comments)  # Thêm danh sách bình luận vào bài đăng
        posts_with_comments.append(post)

    return render_template('index.html', posts=posts_with_comments)
# Route hiển thị danh sách bài viết trong home

# @home_bp.route('/')
# def home():
#     # Khởi tạo SparkSession
#     spark = init_spark()

#     # Lấy tất cả các bình luận từ MongoDB
#     comments_cursor = comments.find()
#     comments_df = pd.DataFrame(list(comments_cursor))  # Chuyển đổi dữ liệu thành Pandas DataFrame

#     # Chuyển Pandas DataFrame thành Spark DataFrame
#     comments_spark_df = spark.createDataFrame(comments_df)

#     # Tiến hành phân tích dữ liệu với Spark
#     result = comments_spark_df.groupBy("sentiment").count().collect()  # Phân loại và đếm số lượng bình luận theo cảm xúc

#     return render_template("index.html", result=result)  # Trả kết quả về template Flask
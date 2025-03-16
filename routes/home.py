from flask import Blueprint, render_template
from connect import connectToMongoDB
from bson import ObjectId  
from pyspark.sql import SparkSession
from spark import init_spark
home_bp = Blueprint('home', __name__)
import pandas as pd

# Kết nối MongoDB
client, db = connectToMongoDB()

@home_bp.route('/')
def home():
    # Lấy tất cả các bài đăng từ collection 'posts', sắp xếp theo ngày tạo (created_at) giảm dần
    posts = db.posts.find().sort('created_at', -1)  # -1 là sắp xếp giảm dần (mới nhất lên trên)

    posts_with_comments = []
    for post in posts:
        comments = db.comments.find({'post_id': post['_id']})
        comments_list = list(comments)  # Chuyển đổi comments thành danh sách

        # Đếm số lượng bình luận loại 'negative'
        negative_count = sum(1 for comment in comments_list if comment['sentiment'] == 'Negative')
        
        # Nếu số lượng bình luận negative > 50% tổng số bình luận thì đánh dấu bài đăng là tiêu cực
        if len(comments_list) > 0 and (negative_count / len(comments_list)) > 0.5:
            post['is_negative'] = True
        else:
            post['is_negative'] = False

        # Lấy thông tin người dùng từ collection 'users' dựa trên user_id
        user = db.users.find_one({"_id": ObjectId(post['user_id'])})  # Lấy thông tin người dùng theo _id
        if user:
            post['user_full_name'] = user.get('full_name', 'Unknown')  # Lưu tên người dùng
        else:
            post['user_full_name'] = 'Unknown'  # Nếu không tìm thấy user, gán 'Unknown'

        # Thêm danh sách bình luận vào bài đăng
        post['comments'] = comments_list
        posts_with_comments.append(post)

    return render_template('index.html', posts=posts_with_comments)

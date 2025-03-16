from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from connect import connectToMongoDB
from datetime import datetime
from bson import ObjectId  
from model import loadModel, sentimentAnalysisOneComment  
post_bp = Blueprint('post', __name__)

# Kết nối MongoDB
client, db = connectToMongoDB()

@post_bp.route('/post', methods=['GET', 'POST'])
def create_post():
    # Kiểm tra xem người dùng đã đăng nhập chưa
    if 'user_id' not in session:
        flash("Bạn cần đăng nhập để đăng bài!", 'error')
        return redirect(url_for('auth.auth'))  # Nếu chưa đăng nhập, chuyển hướng đến trang đăng nhập

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        user_id = session['user_id']

        # Lưu bài viết vào MongoDB
        post = {
            'title': title,
            'content': content,
            'user_id': user_id,
            'created_at': datetime.now() 
        }

        db.posts.insert_one(post)
        flash("Bài viết đã được đăng thành công!", 'success')
        return redirect(url_for('home.home'))  # Chuyển hướng đến trang chủ

    return render_template("post.html")  # Hiển thị form đăng bài


# Tải mô hình phân loại
model, tokenizer = loadModel()

@post_bp.route('/post_detail/<post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    # Lấy bài viết từ database
    try:
        post = db.posts.find_one({"_id": ObjectId(post_id)})  
    except Exception as e:
        flash(f"Error fetching post: {str(e)}", 'error')
        return redirect(url_for('home.home'))  # Nếu không thể chuyển đổi ID, redirect về trang chủ

    if not post:
        flash("Bài viết không tồn tại.", 'error')
        return redirect(url_for('home.home'))  # Nếu bài viết không tồn tại, trả về trang chủ

    # Lấy các tham số lọc từ URL (nếu có)
    sentiment_filter = request.args.get('sentiment', None)  # lấy giá trị 'sentiment' từ query string

    # Lấy các bình luận của bài viết
    if sentiment_filter:
        # Nếu có filter, tìm các bình luận theo cảm xúc
        comments = db.comments.find({"post_id": ObjectId(post_id), "sentiment": sentiment_filter})
    else:
        # Nếu không có filter, lấy tất cả bình luận
        comments = db.comments.find({"post_id": ObjectId(post_id)})
    comments = list(comments)
    # Thêm thông tin full_name của người dùng vào mỗi bình luận
    for comment in comments:
        user = db.users.find_one({"_id": ObjectId(comment['user_id'])})  # Lấy thông tin người dùng từ _id
        if user:
            comment['full_name'] = user.get('full_name', 'Unknown')  # Thêm full_name vào comment
        else:
            comment['full_name'] = 'Unknown'  # Nếu không tìm thấy user, gán 'Unknown'

    # Đếm số lượng bình luận cho mỗi loại cảm xúc
    total_comments = db.comments.count_documents({"post_id": ObjectId(post_id)})
    positive_count = db.comments.count_documents({"post_id": ObjectId(post_id), "sentiment": "Positive"})
    neutral_count = db.comments.count_documents({"post_id": ObjectId(post_id), "sentiment": "Neutral"})
    negative_count = db.comments.count_documents({"post_id": ObjectId(post_id), "sentiment": "Negative"})

    if request.method == 'POST':
        if 'user_id' not in session:
            flash("Bạn cần đăng nhập để bình luận!", 'error')
            return redirect(url_for('auth.auth'))  # Nếu chưa đăng nhập, chuyển hướng đến trang đăng nhập
        
        comment_content = request.form['content']  

        if not comment_content:
            flash("Bình luận không thể trống.", 'error')
            return redirect(url_for('post.post_detail', post_id=post_id))  # Nếu nội dung bình luận trống, redirect lại trang bài viết

        try:
            # Phân loại cảm xúc của bình luận
            sentiment = sentimentAnalysisOneComment(model, tokenizer, comment_content)

            # Thêm bình luận vào MongoDB
            comment = {
                'post_id': ObjectId(post_id),
                'user_id': session['user_id'],
                'content': comment_content,
                'sentiment': sentiment,  
                'created_at': datetime.now()
            }

            db.comments.insert_one(comment) 
            flash("Bình luận đã được đăng thành công!", 'success')
            return redirect(url_for('post.post_detail', post_id=post_id))  # Chuyển hướng lại về trang chi tiết bài viết
        except Exception as e:
            flash(f"Không thể lưu bình luận: {str(e)}", 'error')  
            return redirect(url_for('post.post_detail', post_id=post_id))  # Nếu có lỗi, quay lại trang bài viết

    return render_template('post_detail.html', post=post, comments=comments,
                           sentiment_filter=sentiment_filter, total_comments=total_comments,
                           positive_count=positive_count, neutral_count=neutral_count, negative_count=negative_count)

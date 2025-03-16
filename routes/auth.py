from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from connect import connectToMongoDB
from bson import ObjectId  
auth_bp = Blueprint('auth', __name__, template_folder='templates')
client, db = connectToMongoDB()

# Route đăng ký và đăng nhập
@auth_bp.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        gmail = request.form['gmail']
        password = request.form['password']
        full_name = request.form.get('full_name')  # Chỉ dùng cho đăng ký

        # Kiểm tra xem người dùng muốn đăng ký hay đăng nhập
        if 'register' in request.form:
            hashed_password = generate_password_hash(password)
            # Kiểm tra xem người dùng đã tồn tại chưa
            if db.users.find_one({'gmail': gmail}):
                flash('Email đã được sử dụng, vui lòng thử email khác!', 'error')
                return redirect(url_for('auth.auth'))

            # Thêm người dùng mới vào collection 'users'
            new_user = {
                'gmail': gmail,
                'full_name': full_name,
                'password': hashed_password
            }
            db.users.insert_one(new_user)
            flash('Đăng ký thành công! Bạn có thể đăng nhập ngay.', 'success')
            return redirect(url_for('auth.auth'))

        elif 'login' in request.form:
            # Xử lý đăng nhập
            user = db.users.find_one({'gmail': gmail})

            if user and check_password_hash(user['password'], password):
                # Lưu thông tin người dùng vào session
                session['user_id'] = str(user['_id'])  
                session['gmail'] = user['gmail']  
                session['full_name'] = user['full_name']  

                flash('Đăng nhập thành công!', 'success')
                return redirect(url_for('home.home')) 
            else:
                flash('Thông tin đăng nhập không chính xác!', 'error')
                return redirect(url_for('auth.auth'))

    return render_template('auth.html')
@auth_bp.route('/logout')
def logout():
    session.clear()  # Xóa toàn bộ session khi đăng xuất
    flash('Đăng xuất thành công!', 'success')
    return redirect(url_for('auth.auth'))  # Chuyển hướng về trang đăng nhập

@auth_bp.route('/profile')
def profile():
    # Kiểm tra xem người dùng đã đăng nhập chưa
    if 'user_id' not in session:
        flash("Bạn cần đăng nhập để xem trang profile", 'error')
        return redirect(url_for('auth.auth'))  # Nếu chưa đăng nhập, chuyển đến trang đăng nhập

    user_id = session['user_id']
    user = db.users.find_one({"_id": ObjectId(user_id)})  # Lấy thông tin người dùng từ database

    if not user:
        flash("Người dùng không tồn tại.", 'error')
        return redirect(url_for('home.home'))  # Nếu không tìm thấy người dùng, quay lại trang chủ

    # Lấy số lượng bình luận theo mỗi loại cảm xúc của người dùng
    positive_comments = db.comments.count_documents({"user_id": user_id, "sentiment": "Positive"})
    neutral_comments = db.comments.count_documents({"user_id": user_id, "sentiment": "Neutral"})
    negative_comments = db.comments.count_documents({"user_id": user_id, "sentiment": "Negative"})

    # Lấy tổng số lượng bài đăng của người dùng
    total_posts = db.posts.count_documents({"user_id": user_id})

    # Lấy số lượng bài đăng tiêu cực của người dùng
    negative_posts_count = 0
    post_details = []  # Lưu trữ chi tiết số lượng bình luận từng loại của mỗi bài đăng

    posts = db.posts.find({"user_id": user_id})  # Lấy tất cả bài đăng của người dùng
    for post in posts:
        comments = db.comments.find({"post_id": post['_id']})  # Lấy các bình luận của bài đăng
        comments_list = list(comments)

        # Đếm số lượng bình luận loại 'Positive', 'Neutral', 'Negative'
        positive_count = sum(1 for comment in comments_list if comment['sentiment'] == 'Positive')
        neutral_count = sum(1 for comment in comments_list if comment['sentiment'] == 'Neutral')
        negative_count = sum(1 for comment in comments_list if comment['sentiment'] == 'Negative')

        # Tính tỷ lệ phần trăm của mỗi loại cảm xúc trong tổng số bình luận của bài đăng
        if len(comments_list) > 0:
            positive_percentage = (positive_count / len(comments_list)) * 100
            neutral_percentage = (neutral_count / len(comments_list)) * 100
            negative_percentage = (negative_count / len(comments_list)) * 100
        else:
            positive_percentage = neutral_percentage = negative_percentage = 0

        # Lưu thông tin chi tiết bình luận cho mỗi bài đăng
        post_details.append({
            'title': post['title'],
            'positive_count': positive_count,
            'neutral_count': neutral_count,
            'negative_count': negative_count,
            'total_comments': len(comments_list),  # Tổng số bình luận của bài đăng
            'positive_percentage': positive_percentage,
            'neutral_percentage': neutral_percentage,
            'negative_percentage': negative_percentage,
        })
        
        # Nếu số lượng bình luận negative > 50% tổng số bình luận, bài đăng được đánh dấu là tiêu cực
        if len(comments_list) > 0 and (negative_count / len(comments_list)) > 0.5:
            negative_posts_count += 1

    return render_template('profile.html', user=user, positive_comments=positive_comments,
                           neutral_comments=neutral_comments, negative_comments=negative_comments,
                           negative_posts_count=negative_posts_count, total_posts=total_posts,
                           post_details=post_details)


@auth_bp.route('/profile/<user_id>')
def profile1(user_id):
    # Lấy thông tin người dùng từ database
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        flash("Người dùng không tồn tại.", 'error')
        return redirect(url_for('home.home'))

    # Lấy số lượng bình luận theo mỗi loại cảm xúc của người dùng
    positive_comments = db.comments.count_documents({"user_id": user_id, "sentiment": "Positive"})
    neutral_comments = db.comments.count_documents({"user_id": user_id, "sentiment": "Neutral"})
    negative_comments = db.comments.count_documents({"user_id": user_id, "sentiment": "Negative"})

    # Lấy tổng số lượng bài đăng của người dùng
    total_posts = db.posts.count_documents({"user_id": user_id})

    # Lấy số lượng bài đăng tiêu cực của người dùng
    negative_posts_count = 0
    post_details = []  # Lưu trữ chi tiết số lượng bình luận từng loại của mỗi bài đăng

    posts = db.posts.find({"user_id": user_id})  # Lấy tất cả bài đăng của người dùng
    for post in posts:
        comments = db.comments.find({"post_id": post['_id']})  # Lấy các bình luận của bài đăng
        comments_list = list(comments)

        # Đếm số lượng bình luận loại 'Positive', 'Neutral', 'Negative'
        positive_count = sum(1 for comment in comments_list if comment['sentiment'] == 'Positive')
        neutral_count = sum(1 for comment in comments_list if comment['sentiment'] == 'Neutral')
        negative_count = sum(1 for comment in comments_list if comment['sentiment'] == 'Negative')

        # Tính tỷ lệ phần trăm của mỗi loại cảm xúc trong tổng số bình luận của bài đăng
        if len(comments_list) > 0:
            positive_percentage = (positive_count / len(comments_list)) * 100
            neutral_percentage = (neutral_count / len(comments_list)) * 100
            negative_percentage = (negative_count / len(comments_list)) * 100
        else:
            positive_percentage = neutral_percentage = negative_percentage = 0

        # Lưu thông tin chi tiết bình luận cho mỗi bài đăng
        post_details.append({
            'title': post['title'],
            'positive_count': positive_count,
            'neutral_count': neutral_count,
            'negative_count': negative_count,
            'total_comments': len(comments_list),  # Tổng số bình luận của bài đăng
            'positive_percentage': positive_percentage,
            'neutral_percentage': neutral_percentage,
            'negative_percentage': negative_percentage,
        })
        
        # Nếu số lượng bình luận negative > 50% tổng số bình luận, bài đăng được đánh dấu là tiêu cực
        if len(comments_list) > 0 and (negative_count / len(comments_list)) > 0.5:
            negative_posts_count += 1

    return render_template('profile.html', user=user, positive_comments=positive_comments,
                           neutral_comments=neutral_comments, negative_comments=negative_comments,
                           negative_posts_count=negative_posts_count, total_posts=total_posts,
                           post_details=post_details)
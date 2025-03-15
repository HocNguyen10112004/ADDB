from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from connect import connectToMongoDB

# Đảm bảo khai báo Blueprint đúng tên
auth_bp = Blueprint('auth', __name__, template_folder='templates')

# Kết nối MongoDB
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
            # Xử lý đăng ký
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
                session['user_id'] = str(user['_id'])  # Lưu ID người dùng trong session
                session['gmail'] = user['gmail']  # Lưu gmail người dùng vào session
                session['full_name'] = user['full_name']  # Lưu tên đầy đủ vào session

                flash('Đăng nhập thành công!', 'success')
                return redirect(url_for('home.home'))  # Chuyển hướng đến trang chủ hoặc trang khác bạn muốn
            else:
                flash('Thông tin đăng nhập không chính xác!', 'error')
                return redirect(url_for('auth.auth'))

    return render_template('auth.html')
@auth_bp.route('/logout')
def logout():
    session.clear()  # Xóa toàn bộ session khi đăng xuất
    flash('Đăng xuất thành công!', 'success')
    return redirect(url_for('auth.auth'))  # Chuyển hướng về trang đăng nhập
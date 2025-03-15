from flask import Flask
from routes.auth import auth_bp  
from routes.home import home_bp  
from routes.post import post_bp 
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Đăng ký các blueprint
app.register_blueprint(auth_bp)  
app.register_blueprint(home_bp)
app.register_blueprint(post_bp)
if __name__ == '__main__':
    app.run(debug=True)

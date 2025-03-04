from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from functools import wraps

# Initialize Flask app
app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Josrub123@localhost/stox'  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  
app.config['SECRET_KEY'] = 'your-secret-key'  

# Initialize Database and Bcrypt for password hashing
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  
bcrypt = Bcrypt(app)

# Unified User Model (table name: users)
class Users(UserMixin, db.Model):
    __tablename__ = 'users'  
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)  
    password = db.Column(db.String(250), nullable=False)  # Hashed passwords stored securely
    role = db.Column(db.String(50), default="user", nullable=False)  # "user" or "admin"

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Unauthorized access!", "danger")
            return redirect(url_for("home"))  
        return f(*args, **kwargs)
    return decorated_function

# ========== ROUTES ==========

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)
            flash("Login successful!", "success")

            # Redirect based on role
            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("home"))

        flash("Invalid username or password!", "danger")

    return render_template("user_login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        role = request.form.get("role", "user")  # Defaults to "user" unless specified

        if Users.query.filter_by(username=username).first():
            flash('This username is already taken. Please choose another one.', 'danger')
            return redirect(url_for('signup'))

        user = Users(username=username, password=password, role=role)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('sign_up.html')

@app.route('/admin-dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin-register', methods=["GET", "POST"])
@admin_required
def admin_register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if Users.query.filter_by(username=username).first():
            flash("Admin username already exists!", "danger")
            return redirect(url_for("admin_register"))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        admin = Users(username=username, password=hashed_password, role="admin")
        db.session.add(admin)
        db.session.commit()

        flash("Admin account created successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_sign_up.html")

@app.route('/admin-login', methods=["GET", "POST"])
def admin_login():
    return render_template('admin_login.html')


if __name__ == '__main__':
    app.run(debug=True)

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

# Initialize Database, Login Manager, and Bcrypt
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" 
bcrypt = Bcrypt(app)

# User Model (table name: users)
class Users(UserMixin, db.Model):
    __tablename__ = 'users'  # explicitly set table name to "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)  
    role = db.Column(db.String(50), default="user", nullable=False)  

# Admin Model (table name: admin)
class Admins(UserMixin, db.Model):
    __tablename__ = 'admin'  # explicitly set table name to "admin"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)  
    role = db.Column(db.String(50), default="admin", nullable=False)  

# Flask-Login User Loader (Prioritize loading admins first)
@login_manager.user_loader
def load_user(user_id):
    admin = Admins.query.get(int(user_id))
    if admin:
        return admin  # Ensure admins are recognized correctly
    return Users.query.get(int(user_id))  # Otherwise, check Users table

# Role-Based Decorator for Admins
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Admins):
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

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Users.query.filter_by(username=request.form.get("username")).first()
        admin = Admins.query.filter_by(username=request.form.get("username")).first()

        if user and bcrypt.check_password_hash(user.password, request.form.get("password")):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("home"))  

        if admin and bcrypt.check_password_hash(admin.password, request.form.get("password")):
            login_user(admin)
            flash("Admin login successful!", "success")
            return redirect(url_for("admin_dashboard"))  # Redirect admins correctly
        
        flash("Invalid username or password!", "danger")
    
    return render_template("user_login.html")  # Ensure function always returns something

# User Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

# User Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        # Check if username already exists in either table
        if Users.query.filter_by(username=username).first() or Admins.query.filter_by(username=username).first():
            flash('This username is already taken. Please choose another one.', 'danger')
            return redirect(url_for('signup'))

        # Add user to the Users table
        user = Users(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('sign_up.html')

# Admin Dashboard
@app.route('/admin-dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

# Admin Registration
@app.route('/admin-register', methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if admin username already exists
        if Admins.query.filter_by(username=username).first():
            flash("Admin username already exists!", "danger")
            return redirect(url_for("admin_register"))

        # Hash password and store admin in database
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        admin = Admins(username=username, password=hashed_password)
        db.session.add(admin)
        db.session.commit()

        flash("Admin account created successfully!", "success")
        return redirect(url_for("admin_login"))

    return render_template("admin_sign_up.html")


#/admin-register to register admin

# Admin Login
@app.route('/login/admin', methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        admin = Admins.query.filter_by(username=username).first()
        if admin and bcrypt.check_password_hash(admin.password, password):
            login_user(admin)
            flash("Admin login successful!", "success")
            return redirect(url_for("admin_dashboard"))
        
        flash("Invalid admin credentials", "danger")
    
    return render_template('admin_login.html', user_type="Admin")

# Auto-create an Admin User If Not Exists (For demo purposes)
with app.app_context():
    db.create_all()
    
    if not Admins.query.filter_by(username="admin").first():
        hashed_password = bcrypt.generate_password_hash("admin123").decode('utf-8')
        admin = Admins(username="admin", password=hashed_password)
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)

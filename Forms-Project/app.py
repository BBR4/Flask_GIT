from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# Initialize Flask app
app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Josrub123@localhost/stox'  # Using 'stox' for everything
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a strong secret key

# Initialize Database & Login Manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User Model
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    role = db.Column(db.String(50), default="user", nullable=False)  # Default role is "user"

# Create database tables
with app.app_context():
    db.create_all()

# Flask-Login User Loader
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# ========== ROUTES ==========

# Home Page
@app.route('/')
def home():
    return render_template('homepage.html')

# Portfolio Page
@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

# About Page
@app.route('/about')
def about():
    return render_template('about.html')

# Contact Page
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Admin Panel (Protected)
@app.route('/admin')
@login_required
def admin():
    if current_user.role != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))
    return render_template('admin.html')

# User Login
@app.route('/login/user', methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        user = Users.query.filter_by(username=request.form.get("username")).first()
        if user and user.password == request.form.get("password"):
            login_user(user)
            flash("Login successful!", "success")  # Success message
            return redirect(url_for("home"))
        flash("Invalid credentials", "danger")  # Error message
    return render_template('user_login.html', user_type="User")
    
# Admin Login
@app.route('/login/admin', methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin = Users.query.filter_by(username=request.form.get("username"), role="admin").first()
        if admin and admin.password == request.form.get("password"):
            login_user(admin)
            flash("Admin login successful!", "success")  # Success message
            return redirect(url_for("admin"))
        flash("Invalid admin credentials", "danger")  # Error message
    return render_template('admin_login.html', user_type="Admin")

# User Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

# sign up Route (For Testing)
@app.route('/signup', methods=["GET", "POST"])
def signup():

    if request.method == "POST":
        user = Users(
            username=request.form.get("username"),
            password=request.form.get("password"),
            role="user"
        )
        db.session.add(user)
        db.session.commit()
        flash("Signup successful!", "success")
        return redirect(url_for("user_login"))
    return render_template("sign_up.html")



if __name__ == '__main__':
    app.run(debug=True)

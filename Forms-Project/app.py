from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize
app = Flask(__name__)

# database going ot my stuff
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Josrub123@localhost/stox'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  
app.config['SECRET_KEY'] = 'your-secret-key'  # Use a strong key

# fromk login lab
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "user_login"

# user stuff with the hashed passwords
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)  # Store hashed passwords
    role = db.Column(db.String(50), default="user", nullable=False)  


# Flask-Login User Loader
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

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

# admin litness
@app.route('/admin')
@login_required
def admin():
    if current_user.role != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))
    return render_template('admin.html')

# User Login
@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Users.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):  # Verify password
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!', 'danger')

    return render_template('user_login.html')

# Admin Login
@app.route('/login/admin', methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password) and user.role == 'admin':
            login_user(user)
            flash("Admin login successful!", "success")
            return redirect(url_for("admin"))
        
        flash("Invalid admin credentials", "danger")
    
    return render_template('admin_login.html', user_type="Admin")

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
        password = request.form['password']

        # Check if username already exists
        if Users.query.filter_by(username=username).first():
            flash('This username is already taken. Please choose another one.', 'danger')
            return redirect(url_for('signup'))

        # Hash password before storing
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Add user to the database
        user = Users(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('user_login'))

    return render_template('sign_up.html')

if __name__ == '__main__':
    app.run(debug=True)

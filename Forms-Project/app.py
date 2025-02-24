from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)

# Configure the database settings
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Josrub123@localhost/stox'  # MySQL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  
app.config['SECRET_KEY'] = 'your-secret-key' 


# Route for the home page.
@app.route('/')
def home():
    return render_template('homepage.html')

# Route for the portfolio page.
@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

# Route for the about page.
@app.route('/about')
def about():
    return render_template('about.html')

# Route for the contact page.
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Route for the admin panel.
@app.route('/admin')
def admin():
    return render_template('admin.html')

#route for user login
@app.route('/login/user')
def user_login():
    return render_template('user_login.html')

#route for admin login
@app.route('/login/admin')
def admin_login():
    return render_template('admin_login.html')


if __name__ == '__main__':
    app.run(debug=True)
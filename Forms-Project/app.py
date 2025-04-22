from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from functools import wraps
from flask_apscheduler import APScheduler
from datetime import datetime, time 
import random
import holidays
#cgage
# Initialize Flask app
app = Flask(__name__)
#password for dah ting
#lQYK4bfoqwWJovLSYfF8
# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:lQYK4bfoqwWJovLSYfF8@my-rds-instance-1.clk62ieqgy2z.us-east-2.rds.amazonaws.com:3306/sample_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  
app.config['SECRET_KEY'] = 'your-secret-key'  

# Initialize Database and Bcrypt for password hashing
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  
bcrypt = Bcrypt(app)

# ✅ Initialize APScheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

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

class Stocks(db.Model):
    __tablename__ = 'stocks'
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), unique=True, nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    volume = db.Column(db.Integer, nullable=False)  # Total shares available
    current_price = db.Column(db.Float, nullable=False)
    opening_price = db.Column(db.Float, nullable=False)
    high_price = db.Column(db.Float, nullable=False)
    low_price = db.Column(db.Float, nullable=False)
    market_cap = db.Column(db.Float, nullable=False)

    def update_market_cap(self):
        self.market_cap = self.volume * self.current_price

    def fluctuate_price(self):
        #Simulate random stock price movement within ±2% 
        change_percentage = random.uniform(-2, 2) / 100  # Price changes within ±2%
        new_price = round(self.current_price * (1 + change_percentage), 2)

        # Ensure new price stays within a reasonable range
        if new_price < (self.opening_price * 0.5):  
            new_price = round(self.opening_price * 0.5, 2)
        elif new_price > (self.opening_price * 1.5):  
            new_price = round(self.opening_price * 1.5, 2)

        self.current_price = new_price
        self.update_market_cap()

class MarketSettings(db.Model):
    __tablename__ = 'market_settings'
    id = db.Column(db.Integer, primary_key=True)
    open_time = db.Column(db.Time, default=time(9, 30))
    close_time = db.Column(db.Time, default=time(16, 0))
    holidays = db.Column(db.Text, default='')  # Comma-separated YYYY-MM-DD format
    weekend_closed = db.Column(db.Boolean, default=True)
    holiday_closed = db.Column(db.Boolean, default=True)


def update_stock_prices():
    #Update stock prices randomly every 10 seconds
    with app.app_context():
        stocks = Stocks.query.all()
        for stock in stocks:
            stock.fluctuate_price()
        db.session.commit()
        print("✅ Stock prices updated.")

# Schedule the price update function to run every 10 seconds
scheduler.add_job(id='Stock Price Update', func=update_stock_prices, trigger='interval', seconds=10)


def create_default_market_settings():
    if not MarketSettings.query.first():
        default = MarketSettings()
        db.session.add(default)
        db.session.commit()
        
with app.app_context():
    db.create_all()
    create_default_market_settings()
    if not Users.query.filter_by(username="admin").first():
        hashed_password = bcrypt.generate_password_hash("admin123").decode('utf-8')
        admin = Users(username="admin", password=hashed_password, role="admin")
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin account created: Username: admin | Password: admin123")



class Transactions(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_trade = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # "buy" or "sell"
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('Users', backref='transactions')
    stock = db.relationship('Stocks', backref='transactions')

class CashAccounts(db.Model):
    __tablename__ = 'cash_accounts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)

    user = db.relationship('Users', backref='cash_account')

@app.route('/admin/market-settings', methods=["GET", "POST"])
@login_required
@admin_required
def market_settings():
    settings = MarketSettings.query.first()

    # If no settings exist yet, create a default one
    if not settings:
        settings = MarketSettings(open_time=time(9, 30), close_time=time(16, 0), holidays="")
        db.session.add(settings)
        db.session.commit()

    if request.method == "POST":
        try:
            open_time_str = request.form.get('open_time')
            close_time_str = request.form.get('close_time')
            holidays_input = request.form.get('holidays', '')

            if not open_time_str or not close_time_str:
                flash("Please fill in both open and close times.", "danger")
                return redirect(url_for("market_settings"))

            open_time = datetime.strptime(open_time_str, "%H:%M").time()
            close_time = datetime.strptime(close_time_str, "%H:%M").time()

            settings.open_time = open_time
            settings.close_time = close_time
            settings.holidays = holidays_input

            db.session.commit()
            flash("✅ Market settings updated!", "success")
        except Exception as e:
            print("Error updating settings:", e)
            flash("❌ Something went wrong. Please check your input format.", "danger")

        return redirect(url_for("market_settings"))

    return render_template("admin_market_settings.html", settings=settings)

def is_market_open():
    settings = MarketSettings.query.first()
    now = datetime.now()

    # Check for weekend closure
    if settings and settings.weekend_closed and now.weekday() >= 5:
        return False

    # Check for holiday closure
    if settings and settings.holiday_closed:
        holiday_list = settings.holidays.split(',') if settings.holidays else []
        today = now.strftime('%Y-%m-%d')
        if today in holiday_list:
            return False

    # Check market hours
    return settings.open_time <= now.time() <= settings.close_time




# ========================== TRANSACTION HISTORY ROUTE ===========================

@app.route('/transactions')
@login_required
def transactions():
    user_transactions = Transactions.query.filter_by(user_id=current_user.id).all()
    return render_template("transactions.html", transactions=user_transactions)


@app.route('/market-settings')
def market_settings():
    return render_template('admin_market_settings.html')

# ========================== USER WALLET MANAGEMENT ==========================

@app.route('/wallet', methods=['GET', 'POST'])
@login_required
def wallet():
    # Check if the user has a cash account, if not, create one with $10,000
    cash_account = CashAccounts.query.filter_by(user_id=current_user.id).first()
    
    if not cash_account:
        cash_account = CashAccounts(user_id=current_user.id, balance=10000.0)  # Start with $10,000
        db.session.add(cash_account)
        db.session.commit()
        flash("New wallet created with $10,000 starting balance!", "success")

    if request.method == 'POST':
        action = request.form.get('action')  # "deposit" or "withdraw"
        amount = float(request.form.get('amount'))

        if action == "deposit":
            cash_account.balance += amount
            flash(f"Successfully deposited ${amount}!", "success")

        elif action == "withdraw":
            if cash_account.balance >= amount:
                cash_account.balance -= amount
                flash(f"Successfully withdrew ${amount}!", "success")
            else:
                flash("Insufficient funds for withdrawal!", "danger")

        db.session.commit()
        return redirect(url_for("wallet"))

    return render_template("wallet.html", balance=cash_account.balance)


# ========== ROUTES ==========

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/portfolio')
@login_required
def portfolio():
    # Calculate user's net owned shares (Buy - Sell)
    user_transactions = db.session.query(
        Stocks.ticker, Stocks.company_name,
        db.func.sum(Transactions.quantity).label('total_shares'),
        Stocks.current_price
    ).join(Transactions).filter(
        Transactions.user_id == current_user.id
    ).group_by(Stocks.id).having(db.func.sum(Transactions.quantity) > 0).all()

    return render_template("portfolio.html", stocks=user_transactions)

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

# ========================== ADMIN STOCK MANAGEMENT ==========================

# 🔹 Create Stock (Admin Only)
@app.route('/admin/stocks/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_stock():
    if request.method == 'POST':
        ticker = request.form.get('ticker').upper()
        company_name = request.form.get('company_name')
        volume = int(request.form.get('volume'))
        current_price = float(request.form.get('current_price'))

        # Ensure stock doesn't already exist
        if Stocks.query.filter_by(ticker=ticker).first():
            flash("Stock already exists!", "danger")
            return redirect(url_for("create_stock"))

        stock = Stocks(
            ticker=ticker,
            company_name=company_name,
            volume=volume,
            current_price=current_price,
            opening_price=current_price,
            high_price=current_price,
            low_price=current_price
        )
        stock.update_market_cap()

        db.session.add(stock)
        db.session.commit()
        flash(f"Stock {ticker} created successfully!", "success")
        return redirect(url_for("view_stocks"))

    return render_template("create_stock.html")


# 🔹 View All Stocks (Admin Only)
@app.route('/admin/stocks')
@login_required
@admin_required
def view_stocks():
    stocks = Stocks.query.all()
    return render_template("view_stocks.html", stocks=stocks)


# 🔹 Update Stock Price & Volume (Admin Only)
@app.route('/admin/stocks/update/<int:stock_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def update_stock(stock_id):
    stock = Stocks.query.get_or_404(stock_id)

    if request.method == 'POST':
        stock.current_price = float(request.form.get('current_price'))
        stock.volume = int(request.form.get('volume'))
        stock.update_market_cap()

        db.session.commit()
        flash(f"Stock {stock.ticker} updated successfully!", "success")
        return redirect(url_for("view_stocks"))

    return render_template("update_stock.html", stock=stock)


# 🔹 Delete Stock (Admin Only)
@app.route('/admin/stocks/delete/<int:stock_id>', methods=['POST'])
@login_required
@admin_required
def delete_stock(stock_id):
    stock = Stocks.query.get_or_404(stock_id)
    db.session.delete(stock)
    db.session.commit()
    flash(f"Stock {stock.ticker} deleted successfully!", "danger")
    return redirect(url_for("view_stocks"))


@app.route('/buy-stock', methods=['GET', 'POST'])
@login_required
def buy_stock():
    # Check if market is open before proceeding
    if not is_market_open():
        flash("The market is closed. You can only buy stocks during market hours.", "danger")
        return redirect(url_for("portfolio"))
    
    stocks = Stocks.query.all()  # Get all available stocks

    if request.method == 'POST':
        stock_id = int(request.form.get('stock_id'))
        quantity = int(request.form.get('quantity'))

        # Look up stock
        stock = Stocks.query.get(stock_id)
        if not stock:
            flash("Stock not found!", "danger")
            return redirect(url_for("buy_stock"))

        total_cost = stock.current_price * quantity

        # Check if user has enough cash
        cash_account = CashAccounts.query.filter_by(user_id=current_user.id).first()
        if not cash_account or cash_account.balance < total_cost:
            flash("Insufficient funds!", "danger")
            return redirect(url_for("buy_stock"))

        # Check if stock has enough volume available
        if stock.volume < quantity:
            flash("Not enough stock available!", "danger")
            return redirect(url_for("buy_stock"))

        # Perform transaction
        cash_account.balance -= total_cost  # Deduct from user's cash balance
        stock.volume -= quantity  # Reduce available stock volume
        stock.update_market_cap()  # Update stock market cap

        # Record transaction
        transaction = Transactions(
            user_id=current_user.id,
            stock_id=stock.id,
            quantity=quantity,
            price_at_trade=stock.current_price,
            transaction_type="buy"
        )
        db.session.add(transaction)
        db.session.commit()

        flash(f"Successfully bought {quantity} shares of {stock.ticker}!", "success")
        return redirect(url_for("portfolio"))

    return render_template("buy_stock.html", stocks=stocks)


@app.route('/sell-stock', methods=['GET', 'POST'])
@login_required
def sell_stock():
    # Check if market is open before proceeding
    if not is_market_open():
        flash("The market is closed. You can only sell stocks during market hours.", "danger")
        return redirect(url_for("portfolio"))
    
    # Get user's owned stocks (net quantity: buy - sell)
    owned_stocks = db.session.query(
        Stocks.id, Stocks.ticker, Stocks.company_name,
        db.func.sum(Transactions.quantity).label('total_shares')
    ).join(Transactions).filter(
        Transactions.user_id == current_user.id
    ).group_by(Stocks.id).having(db.func.sum(Transactions.quantity) > 0).all()

    if request.method == 'POST':
        stock_id = int(request.form.get('stock_id'))
        quantity = int(request.form.get('quantity'))

        # Get stock info
        stock = Stocks.query.get(stock_id)
        if not stock:
            flash("Stock not found!", "danger")
            return redirect(url_for("sell_stock"))

        # Get user's available shares for the selected stock
        user_shares = db.session.query(
            db.func.sum(Transactions.quantity)
        ).filter(
            Transactions.user_id == current_user.id,
            Transactions.stock_id == stock_id
        ).scalar() or 0  # Default to 0 if no shares

        if user_shares < quantity:
            flash("You don't have enough shares to sell!", "danger")
            return redirect(url_for("sell_stock"))

        # Perform sale
        cash_account = CashAccounts.query.filter_by(user_id=current_user.id).first()
        cash_account.balance += stock.current_price * quantity  # Add money to user balance
        stock.volume += quantity  # Return stock volume to the market
        stock.update_market_cap()

        # Record transaction
        transaction = Transactions(
            user_id=current_user.id,
            stock_id=stock.id,
            quantity=-quantity,  # Negative quantity to represent selling
            price_at_trade=stock.current_price,
            transaction_type="sell"
        )
        db.session.add(transaction)
        db.session.commit()

        flash(f"Successfully sold {quantity} shares of {stock.ticker}!", "success")
        return redirect(url_for("portfolio"))

    return render_template("sell_stock.html", owned_stocks=owned_stocks)

@app.route('/')
def index():
    market_status = "Open" if is_market_open() else "Closed"
    return render_template('index.html', market_status=market_status)

@app.route('/trade', methods=['POST'])
def trade():
    if not is_market_open():
        flash("Market is closed. Trading is only allowed during market hours.", "warning")
        return redirect(url_for('index'))

    # Example trading logic (replace with your actual logic)
    flash("Trade executed successfully!", "success")
    return redirect(url_for('index'))

@app.context_processor
def inject_market_status():
    now = datetime.now().strftime("%H:%M:%S")
    return {
        "current_time": now,
        "market_status": is_market_open()
    }


with app.app_context():
    db.create_all()
    
    # Ensure an admin user exists
    if not Users.query.filter_by(username="admin").first():
        hashed_password = bcrypt.generate_password_hash("admin123").decode('utf-8')
        admin = Users(username="admin", password=hashed_password, role="admin")
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin account created: Username: admin | Password: admin123")


if __name__ == '__main__':
    app.run(debug=True)

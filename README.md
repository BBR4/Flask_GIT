# StoX – Stock Trading Simulation Platform

A full-stack stock trading simulation platform built with Flask, SQLAlchemy, and AWS. StoX allows users to create accounts, buy/sell stocks with simulated real-time pricing, and track their portfolios. Includes role-based access for administrators and customers, with comprehensive backend logging and live market controls.

## 🔧 Features

- 🔐 **Secure User Authentication** (Flask-Login)
- 🧑‍💼 **Role-Based Access** for Admins and Customers
- 📈 **Live Stock Price Simulation** using APScheduler (10-second intervals)
- 🗓️ **Market Hours Management** with timezone awareness (MST)
- 💼 **Portfolio Management** and Cash Wallet
- 📊 **Transaction History** and Validation Checks
- 🛠️ **Admin Controls** to add/edit/delete stocks, control market status
- ☁️ **AWS Deployment** (EC2, RDS with MySQL)

## 🚀 Tech Stack

- **Backend:** Python (Flask, SQLAlchemy)
- **Frontend:** HTML/CSS, Jinja2
- **Database:** MySQL on AWS RDS
- **Scheduler:** APScheduler (for simulating live price updates)
- **Hosting:** AWS EC2
- **Other Tools:** Git, GitHub, Flask-WTF, Flask-Login

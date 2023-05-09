#imports
from flask import Flask,Blueprint,request,render_template,abort,flash,redirect,session,url_for,make_response
import hashlib
import pickle
import numpy as np
import pandas as pd
import csv
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import LinearRegression
import sqlite3
import matplotlib.pyplot as plt
import os

#flask application
app = Flask(__name__)
app.secret_key = 'test_secret_key'
logout_bp = Blueprint('logout', __name__)


def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS USERS(ID INTEGER PRIMARY KEY AUTOINCREMENT,USERNAME TEXT NOT NULL,PASSWORD TEXT NOT NULL);''')
    conn.commit()
    conn.close()

init_db()

@app.route('/',methods= ['GET','POST'])
def index():
    username = session.get('username')
    response = make_response(render_template('index.html',username = username))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

#LOGIN PAGE
@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = sqlite3.connect('database.db')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        query = "SELECT * FROM USERS WHERE USERNAME = ? AND PASSWORD = ?"
        result = conn.execute(query, (username, hashed_password)).fetchone()
        conn.close()
        if result:
           session['username'] = username
           return redirect('/main_page')
        else:
            # The username and/or password are incorrect
            return redirect('/invalid')
    return render_template('login.html')


@app.route('/invalid', methods = ['GET','POST'])
def invalid():
    conn = sqlite3.connect('database.db')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        query = "SELECT * FROM USERS WHERE USERNAME = ? AND PASSWORD = ?"
        result = conn.execute(query, (username, hashed_password)).fetchone()
        conn.close()
        if result:
           return redirect('/main_page')
        else:
            # The username and/or password are incorrect
            return redirect('/invalid')
    return render_template('invalid.html')
  
#SIGNUP PAGE
@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    conn = sqlite3.connect('database.db')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        conn.execute("INSERT INTO USERS(USERNAME, PASSWORD) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return redirect('/login')
    return render_template('sign_up.html')



@app.route('/main_page', methods=['GET', 'POST'])
def main_page():
    conn = sqlite3.connect('database.db')
    username = session.get('username')
    if username:
        if request.method == 'POST':
            file = request.files['file']
            data = pd.read_csv(file)
            data = data.dropna()  # Remove missing values
            y = data['Close']  # Target variable
            X = np.arange(len(y)).reshape(-1, 1)  # Feature variable

            # Fit linear regression model
            model = LinearRegression()
            model.fit(X, y)

            # Predict future prices
            future_X = np.arange(len(y), len(y) + 50).reshape(-1, 1)
            future_y = model.predict(future_X)

            # Evaluate model
            y_test = y[-50:]
            mse = mean_squared_error(y_test, future_y)
            plt.plot(y, label='Actual Stock Prices')
            plt.plot(future_X, future_y, label='Predicted Future Prices')
            plt.legend()
            plot_folder = os.path.join(app.root_path, 'static', 'images')
            plot_path = os.path.join(plot_folder, 'plot.png')
            plt.savefig(plot_path)

            return render_template('main.html', username=username, plot_filename='plot.png')
        else:
            return render_template('main.html', username=username)
    else:
        return redirect('/login')

if __name__ == '__main__':
  app.run(host = '0.0.0.0',port=81)
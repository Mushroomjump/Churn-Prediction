import bcrypt
import joblib
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

from WebApp.churn_model import train_model, preprocess_data, predict_churn

# Initialize the Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Define the User model for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

# Function to create a new user with a hashed password
def create_user(username, password):
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        raise ValueError('Username already exists. Please choose a different username.')

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    new_user = User(username=username, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()
'''''
#Default Password
def create_admin():
    with app.app_context():
        # Check if the admin account already exists in the database
        existing_user = User.query.filter_by(username='admin').first()
        if not existing_user:
            create_user('admin', 'password')

create_admin()
'''
def get_user(username):
    return User.query.filter_by(username=username).first()

# Load the XGBoost model from the file
xgb_model = joblib.load('xgboost_model.pkl')

# Fitting the OneHotEncoder on the training data for selected features
training_data_file = 'Telco-Customer-Churn.csv'
data = pd.read_csv(training_data_file)
X_train, y_train, preprocessor = preprocess_data(data)

# Train the model using the preprocessed data
xgb_model = train_model(X_train, y_train)

# Save the trained model
joblib.dump(xgb_model, 'xgboost_model.pkl')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        user = get_user(username)

        if user and bcrypt.checkpw(password, user.password_hash):
            # Check if the user is an admin
            if username == 'admin':
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('index'))
        else:
            error_message = 'Invalid username or password. Please try again.'
            return render_template('login.html', error_message=error_message)

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists in the database
        existing_user = get_user(username)
        if existing_user:
            error_message = 'Username already exists. Please choose a different username.'
            return render_template('signup.html', error_message=error_message)

        create_user(username, password)
        return redirect(url_for('login.html'))

    return render_template('signup.html')

@app.route('/admin_panel')
def admin_panel():
    return render_template('admin_panel.html')

@app.route('/add_user', methods=['POST'])
def add_user():
    # Code for adding a new user, accessible only to admin
    username = request.form['username']
    password = request.form['password']
    create_user(username, password)
    return redirect(url_for('manage_users'))

@app.route('/remove_user/<int:user_id>')
def remove_user(user_id):
    # Code for removing a user, accessible only to admin
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('manage_users'))

@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'csv_file' in request.files:
        csv_file = request.files['csv_file']
        data = pd.read_csv(csv_file)
    else:
        # Parse the form data and create a DataFrame
        data = pd.DataFrame({
            'SeniorCitizen': [int(request.form['SeniorCitizen'])],
            'Partner': [request.form['Partner']],
            'Dependents': [request.form['Dependents']],
            'tenure': [int(request.form['tenure'])],
            'MultipleLines': [request.form['MultipleLines']],
            'InternetService': [request.form['InternetService']],
            'OnlineSecurity': [request.form['OnlineSecurity']]
        })

    predictions = predict_churn(xgb_model, data, preprocessor)

    # Convert predictions to human-readable format
    churn_predictions = ['Customer Will Churn' if p == 1 else 'Customer Will Not Churn' for p in predictions]

    # Count churned and non-churned customers
    churned_count = churn_predictions.count('Customer Will Churn')
    non_churned_count = churn_predictions.count('Customer Will Not Churn')

    return render_template('result.html',
                           churned_count=churned_count,
                           non_churned_count=non_churned_count)

if __name__ == '__main__':
    app.run(debug=True)

import joblib
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
from xgboost import XGBClassifier

def preprocess_data(data):
    # Drop unused fields (use only the required fields)
    data = data[['SeniorCitizen', 'Partner', 'Dependents', 'tenure', 'MultipleLines',
                 'InternetService', 'OnlineSecurity', 'Churn']]
    X = data.drop('Churn', axis=1)
    y = data['Churn']

    # Convert the target variable 'Churn' to binary (0 and 1)
    y = y.map({'No': 0, 'Yes': 1})

    # Convert categorical features to numeric using OneHotEncoder
    cat_features = ['Partner', 'Dependents', 'MultipleLines', 'InternetService', 'OnlineSecurity']
    preprocessor = ColumnTransformer([('cat', OneHotEncoder(), cat_features)], remainder='passthrough')
    X_encoded = preprocessor.fit_transform(X)

    return X_encoded, y, preprocessor

def train_model(X_train, y_train):
    # Initialize and fit the XGBoost model
    xgb_model = XGBClassifier()
    xgb_model.fit(X_train, y_train)
    return xgb_model

def save_model(model, filename):
    # Save the fitted model to a file
    joblib.dump(model, filename)

def load_model(filename):
    # Load the XGBoost model from the file
    model = joblib.load(filename)
    return model

def predict_churn(model, sample_data, preprocessor):
    # Convert categorical features to numeric using the preprocessor
    sample_data_encoded = preprocessor.transform(sample_data)

    # Make predictions using the loaded model
    predictions = model.predict(sample_data_encoded)
    return predictions

import pandas as pd
import numpy as np
import os
import joblib
from utils.data_loader import read_historical_data

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix

# ---------------------------------------------------
# Create models folder
# ---------------------------------------------------

os.makedirs("models", exist_ok=True)

# ---------------------------------------------------
# Load Dataset
# ---------------------------------------------------

print("Loading GTD Dataset...")

df = read_historical_data()

print(df.shape)

# ---------------------------------------------------
# Select Features
# ---------------------------------------------------

features = [

    "country_txt",
    "region_txt",
    "weaptype1_txt",
    "targtype1_txt",
    "gname",
    "success",
    "suicide",
    "nkill",
    "nwound"

]

target = "attacktype1_txt"

df = df[features + [target]]

# ---------------------------------------------------
# Remove Missing Values
# ---------------------------------------------------

df = df.dropna()

print("After Cleaning:", df.shape)

# ---------------------------------------------------
# Encode Features
# ---------------------------------------------------

encoders = {}

for col in [

    "country_txt",
    "region_txt",
    "weaptype1_txt",
    "targtype1_txt",
    "gname"

]:

    encoder = LabelEncoder()

    df[col] = encoder.fit_transform(df[col])

    encoders[col] = encoder

# ---------------------------------------------------
# Encode Target
# ---------------------------------------------------

target_encoder = LabelEncoder()

df[target] = target_encoder.fit_transform(df[target])

# ---------------------------------------------------
# Features / Labels
# ---------------------------------------------------

X = df[features]

y = df[target]

# ---------------------------------------------------
# Train/Test Split
# ---------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,
    test_size=0.20,
    random_state=42

)

# ---------------------------------------------------
# Train Random Forest
# ---------------------------------------------------

print("Training Model...")

model = RandomForestClassifier(

    n_estimators=30,
    max_depth=12,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1

)

model.fit(

    X_train,
    y_train

)

# ---------------------------------------------------
# Prediction
# ---------------------------------------------------

pred = model.predict(X_test)

# ---------------------------------------------------
# Accuracy
# ---------------------------------------------------

accuracy = accuracy_score(

    y_test,
    pred

)

print()

print("=" * 50)

print("Accuracy")

print("=" * 50)

print(accuracy)

print()

print("=" * 50)

print("Classification Report")

print("=" * 50)

print(

    classification_report(

        y_test,
        pred

    )

)

print("=" * 50)

print("Confusion Matrix")

print("=" * 50)

print(

    confusion_matrix(

        y_test,
        pred

    )

)

# ---------------------------------------------------
# Save Model
# ---------------------------------------------------

joblib.dump(

    model,
    "models/attack_prediction_model.pkl"

)

joblib.dump(

    target_encoder,
    "models/target_encoder.pkl"

)

joblib.dump(

    encoders,
    "models/feature_encoders.pkl"

)

print()

print("=" * 50)

print("Model Saved Successfully")

print("=" * 50)

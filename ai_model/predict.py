import pickle
import pandas as pd
import os

# Determine absolute path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load Model & Vectorizer
model = pickle.load(open(os.path.join(BASE_DIR, "cpt_model.pkl"), "rb"))
vectorizer = pickle.load(open(os.path.join(BASE_DIR, "vectorizer.pkl"), "rb"))

def predict_cpt(description):
    """Predict CPT code based on medical description."""
    transformed_desc = vectorizer.transform([description])
    predicted_cpt = model.predict(transformed_desc)
    return predicted_cpt[0]

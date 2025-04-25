import pandas as pd
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report


DATA_PATH = r"C:\Users\AbiReddy\OneDrive\Desktop\Autocoding\medical_coding_ai\dataset\labeled_data.csv"
MODEL_PATH = os.path.join("ai_model", "cpt_model.pkl")
VEC_PATH = os.path.join("ai_model", "vectorizer.pkl")


df = pd.read_csv(DATA_PATH)


if "Report Description" not in df.columns or "CPT Code" not in df.columns:
    raise ValueError("CSV must contain 'Report Description' and 'CPT Code' columns.")


X = df["Report Description"].astype(str)
y = df["CPT Code"].astype(str)


vectorizer = TfidfVectorizer(ngram_range=(1, 3), max_features=5000)
X_vec = vectorizer.fit_transform(X)


X_train, X_test, y_train, y_test = train_test_split(
    X_vec, y, test_size=0.2, random_state=42
)


model = RandomForestClassifier(
    n_estimators=200,
    class_weight='balanced',
    random_state=42
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n✅ Model trained successfully! Accuracy: {accuracy:.2f}\n")
print("📊 Classification Report:\n")
print(classification_report(y_test, y_pred))

# Save model and vectorizer
joblib.dump(model, MODEL_PATH)
joblib.dump(vectorizer, VEC_PATH)

print(f"\n💾 Model saved to: {MODEL_PATH}")
print(f"💾 Vectorizer saved to: {VEC_PATH}")

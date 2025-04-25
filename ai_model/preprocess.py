import pandas as pd
import re

# Load datasets
cpt_df = pd.read_csv("dataset/cpt_codes.csv")
medical_df = pd.read_csv("dataset/medical_reports.csv")

# Preprocessing function
def clean_text(text):
    text = str(text).lower()  # Convert to lowercase
    text = re.sub(r"[^a-z0-9\s]", "", text)  # Remove special characters
    return text

# Apply preprocessing
cpt_df["Description"] = cpt_df["Description"].apply(clean_text)
medical_df["Report Description"] = medical_df["Report Description"].apply(clean_text)

# Save preprocessed data
cpt_df.to_csv("dataset/cpt_codes_clean.csv", index=False)
medical_df.to_csv("dataset/medical_reports_clean.csv", index=False)

print("✅ CPT & Medical Reports preprocessing complete!")

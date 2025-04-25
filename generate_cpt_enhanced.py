import pandas as pd
import os

# Enhanced CPT code data
cpt_data = {
    "CPT Code": ["74176", "27447", "85027"],
    "Description": [
        "CT scan of the abdomen and pelvis without contrast",
        "Surgical knee replacement procedure to treat severe joint damage",
        "Blood test to measure red and white cells, hemoglobin, and hematocrit"
    ]
}

# Create DataFrame
df = pd.DataFrame(cpt_data)

# Define file path
file_path = r"C:\Users\AbiReddy\OneDrive\Desktop\Autocoding\medical_coding_ai\dataset\cpt_codes_enhanced.csv"

# Ensure directory exists
os.makedirs(os.path.dirname(file_path), exist_ok=True)

# Save to CSV
df.to_csv(file_path, index=False)

print("✅ cpt_codes_enhanced.csv created at:")
print(file_path)

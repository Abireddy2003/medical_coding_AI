import json
import pandas as pd

# Load the formatted ICD-10 JSON file
with open("scripts/formatted_icd10_mapping.json", "r") as file:
    icd_data = json.load(file)

# Convert JSON to DataFrame
icd_df = pd.DataFrame([
    {"ICD Code": code, "Description": desc}
    for code, desc in icd_data.items()
])

# Save to CSV
icd_df.to_csv("dataset/icd_codes.csv", index=False)
print("✅ ICD codes successfully extracted and saved to dataset/icd_codes.csv")

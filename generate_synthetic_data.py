import pandas as pd
import random
import csv
import os

# Load enhanced CPT descriptions
cpt_file = r"C:\Users\AbiReddy\OneDrive\Desktop\Autocoding\medical_coding_ai\dataset\cpt_codes_enhanced.csv"
cpt_df = pd.read_csv(cpt_file)

# Synthetic sentence templates
templates = [
    "Patient underwent a {}.",
    "Performed a {} to assess symptoms.",
    "Scheduled a {} for diagnostic evaluation.",
    "A {} was carried out due to chronic issues.",
    "Referred for a {} based on examination results.",
    "{} was recommended to investigate patient's condition."
]

# Generate synthetic examples
synthetic_rows = [("Report Description", "CPT Code")]
for _, row in cpt_df.iterrows():
    for _ in range(8):  # Generate ~8 variants per CPT (total ~80+)
        description = random.choice(templates).format(row["Description"])
        synthetic_rows.append((description, row["CPT Code"]))

# Save path
labeled_data_file = r"C:\Users\AbiReddy\OneDrive\Desktop\Autocoding\medical_coding_ai\dataset\labeled_data.csv"

# Ensure folder exists
os.makedirs(os.path.dirname(labeled_data_file), exist_ok=True)

# Append if exists, else write fresh
if os.path.exists(labeled_data_file):
    with open(labeled_data_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(synthetic_rows[1:])  # Skip header
else:
    with open(labeled_data_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(synthetic_rows)

print(f"✅ Generated {len(synthetic_rows) - 1} synthetic samples and saved to labeled_data.csv")

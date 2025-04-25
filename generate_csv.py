import pandas as pd

# Original CPT codes with vague descriptions
cpt_data = {
    "CPT Code": ["74176", "27447", "85027"],
    "Description": [
        "with either 76942 us 77012 ct",
        "total knee arthroplasty",
        "cbc w/o auto diff"
    ]
}

# Enhanced, medically descriptive versions
enhanced_descriptions = [
    "CT scan of the abdomen and pelvis without contrast",
    "Surgical knee replacement procedure to treat severe joint damage",
    "Blood test to measure red and white cells, hemoglobin, and hematocrit"
]

# Create enhanced DataFrame
enhanced_df = pd.DataFrame({
    "CPT Code": cpt_data["CPT Code"],
    "Description": enhanced_descriptions
})

# Save path
enhanced_file_path = "/mnt/data/cpt_codes_enhanced.csv"
enhanced_df.to_csv(enhanced_file_path, index=False)

enhanced_file_path

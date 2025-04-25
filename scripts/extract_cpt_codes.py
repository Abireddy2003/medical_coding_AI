import fitz  # PyMuPDF
import re
import json

def extract_cpt_codes(pdf_path):
    cpt_mapping = {}

    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text()

            # Regex to match CPT codes (Assuming format: Code Description)
            matches = re.findall(r"(\d{5})\s+(.*)", text)

            for code, description in matches:
                cpt_mapping[description.strip()] = code.strip()

    return cpt_mapping

# ✅ Update with the correct PDF path
pdf_path = "../dataset/2024_CPT_Code_Reference_Guide.pdf"  # Relative path
# OR use an absolute path:
# pdf_path = r"C:\Users\AbiReddy\OneDrive\Desktop\Autocoding\medical_coding_ai\dataset\2024_CPT_Code_Reference_Guide.pdf"

cpt_codes = extract_cpt_codes(pdf_path)

# Save extracted data to JSON file
with open("cpt_mapping.json", "w") as f:
    json.dump(cpt_codes, f)

print("✅ CPT codes extracted and saved to cpt_mapping.json!")


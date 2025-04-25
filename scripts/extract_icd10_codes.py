import os
import json
import re
from PyPDF2 import PdfReader

def fix_spacing(text):
    return re.sub(r'(?<=\b\w) (?=\w\b)', '', text)

def clean_description(text):
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def format_icd_code(code):
    if len(code) >= 4 and '.' not in code:
        formatted = f"{code[:3]}.{code[3:]}"
        return formatted
    return code

def extract_codes_from_text(text):
    patterns = [
        # Full ICD-10 codes with double letter suffix
        r"([A-Z][0-9]{2}\.?[0-9]{2,3}[A-Z][A-Z])\s+([^\n]+?)(?=\n|$)",
        # Codes with single letter suffix
        r"([A-Z][0-9]{2}\.?[0-9]{2,3}[A-Z])\s+([^\n]+?)(?=\n|$)",
        # Basic codes without suffix
        r"([A-Z][0-9]{2}\.?[0-9]{2,3})\s+([^\n]+?)(?=\n|$)",
        # Codes at line start
        r"^([A-Z][0-9]{2}\.?[0-9]{2,3}[A-Z]?)\s+([^\n]+)$",
        # Codes with multiple spaces
        r"([A-Z][0-9]{2}\.?[0-9]{2,3}[A-Z]?)\s{2,}([^\n]+)",
        # Codes with tabs
        r"([A-Z][0-9]{2}\.?[0-9]{2,3}[A-Z]?)\t+([^\n]+)"
    ]
    
    all_matches = set()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for i, line in enumerate(lines):
        next_line = lines[i + 1] if i + 1 < len(lines) else ""
        
        if not re.match(r"^[A-Z][0-9]{2}", next_line):
            line = line + " " + next_line
            
        for pattern in patterns:
            matches = re.findall(pattern, line, re.MULTILINE)
            for code, desc in matches:
                desc = desc.strip()
                if desc and code:
                    if '.' not in code and len(code) >= 4:
                        code = f"{code[:3]}.{code[3:]}"
                    all_matches.add((desc, code))
                    break
    
    return list(all_matches)

# Path to the PDF
pdf_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "icd-10-medical-diagnosis-codes.pdf")

# Check if file exists
if not os.path.exists(pdf_path):
    print(f"Error: PDF file not found at: {pdf_path}")
    print("\nChecking directory contents:")
    
    dataset_dir = os.path.join(os.path.dirname(__file__), "..", "dataset")
    if os.path.exists(dataset_dir):
        print(f"\nFiles in dataset directory:")
        for file in os.listdir(dataset_dir):
            print(f"- {file}")
    else:
        print("Dataset directory not found!")
    
    print("\nPlease ensure:")
    print("1. The 'dataset' folder exists in the project root")
    print("2. Your ICD-10/CPT PDF file is named correctly")
    print("3. The file is placed in the dataset folder")
    exit(1)

try:
    # Extract text from PDF
    reader = PdfReader(pdf_path)
    all_text = ""
    print(f"Processing {len(reader.pages)} pages...")
    
    for page_num, page in enumerate(reader.pages, 1):
        page_text = page.extract_text()
        if page_text:
            # Clean page text
            cleaned_text = re.sub(r'Page \d+ of \d+', '', page_text)
            cleaned_text = re.sub(r'^\s*\d+\s*$', '', cleaned_text, flags=re.MULTILINE)
            all_text += cleaned_text + "\n"

    # Extract codes using multiple patterns
    all_matches = extract_codes_from_text(all_text)
    print(f"\nTotal matches found: {len(all_matches)}")
    print(f"Average matches per page: {len(all_matches)/len(reader.pages):.2f}")

    # Convert matches to cleaned-up mapping
    icd_mapping = {}
    skipped_entries = []
    
    for desc, code in all_matches:
        cleaned_description = clean_description(fix_spacing(desc))
        if cleaned_description and len(code) >= 3:
            if cleaned_description not in icd_mapping:
                icd_mapping[cleaned_description] = code
        else:
            skipped_entries.append((desc, code))

    # Print processing statistics
    print(f"Valid entries processed: {len(icd_mapping)}")
    if skipped_entries:
        print(f"Skipped entries: {len(skipped_entries)}")
        print("\nFirst few skipped entries for verification:")
        for desc, code in skipped_entries[:3]:
            print(f"{desc}: {code}")

    # Save to JSON file
    output_path = os.path.join(os.path.dirname(__file__), "formatted_icd10_mapping.json")
    with open(output_path, "w", encoding='utf-8') as f:
        json.dump(icd_mapping, f, indent=4, ensure_ascii=False, sort_keys=True)

    print(f"\n✅ Cleaned and saved {len(icd_mapping)} ICD-10 mappings.")
    
    # Print first few entries for verification
    print("\nFirst few entries:")
    for i, (desc, code) in enumerate(sorted(icd_mapping.items())[:5]):
        print(f"{desc}: {code}")

    # Save debug information
    debug_path = os.path.join(os.path.dirname(__file__), "extraction_debug.txt")
    with open(debug_path, "w", encoding='utf-8') as f:
        f.write(f"Total pages: {len(reader.pages)}\n")
        f.write(f"Total matches: {len(all_matches)}\n")
        f.write(f"Valid entries: {len(icd_mapping)}\n")
        f.write(f"Skipped entries: {len(skipped_entries)}\n")
        f.write("\nSample of raw text:\n")
        f.write(all_text[:1000])

except Exception as e:
    print(f"Error processing PDF: {str(e)}")
    print(f"Full error details: {e.__class__.__name__}")
    exit(1)
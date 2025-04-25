import os
import re
import json
import string
import pytesseract
import textract
import cv2
import numpy as np

from PIL import Image
from fuzzywuzzy import fuzz
from difflib import SequenceMatcher
from pdf2image import convert_from_path
from django.conf import settings

MODALITY_PREFIXES = ("XR", "MRI", "NM", "US", "IVC", "CT", "PET", "MRA")

# ---------- IMAGE PREPROCESSING ----------
def preprocess_image(image_path):
    """Enhanced image preprocessing for better OCR results"""
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Could not read image file")
            
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(enhanced, 255, 
                                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                    cv2.THRESH_BINARY, 11, 2)
        
        # Apply slight dilation to connect broken characters
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.dilate(thresh, kernel, iterations=1)
        
        return processed
    except Exception as e:
        print(f"[ERROR] Image preprocessing failed: {e}")
        return gray if 'gray' in locals() else image

# ---------- TEXT CLEANING ----------
def clean_ocr_text(text):
    """Enhanced text cleaning with common OCR fixes"""
    if not text:
        return ""
        
    # Common OCR fixes for medical reports
    fixes = {
        r'PtType\s*[:=]': "PtType:",
        r'PtClass\s*[:=]': "PtClass:",
        r'RefPhy\s*[:=]': "RefPhy:",
        r'SignPhy\s*[:=]': "SignPhy:",
        r'OrdEx\s*[:=]': "OrdEx:",
        r'Accsn\s*[:=]': "Accsn:",
        r'OrdHx\s*[:=]': "OrdHx:",
        r'FinClass\s*[:=]': "FinClass:",
        r'Note File Name\s*[:=]': "Note File Name:",
        r'Last Coded On\s*[:=]': "Last Coded On:",
        r'Last Coded by\s*[:=]': "Last Coded by:",
        r'MRN\s*[:=]': "MRN:",
        r'DOB\s*[:=]': "DOB:",
        r'DOS\s*[:=]': "DOS:",
        "Or dEx": "OrdEx", "Ord Ex": "OrdEx", "Ordex": "OrdEx", "Ordx": "OrdEx",
        "ORD EX": "OrdEx", "ORDEx": "OrdEx", "ordex": "OrdEx",
        "ORD HX": "OrdHx", "ord hx": "OrdHx", "ORDHX": "OrdHx",
        "MR N": "MRN", "MRn": "MRN",
        "DOB :": "DOB:", "Sex :": "Sex:", "Age :": "Age:",
        "Clinical :": "Clinical:", "Findings :": "Findings:",
        "Impression :": "Impression:", "Procedure :": "Procedure:",
        "Date of Service :": "Date of Service:",
        "Accessio n": "Accession"
    }
    
    # Modality-specific fixes
    modality_fixes = {
        "x-r": "XR", "x r": "XR", "xray": "XR", "x ray": "XR",
        "m ri": "MRI", "mri": "MRI",
        "c t": "CT", "ct": "CT",
        "u s": "US", "us": "US",
        "n m": "NM", "nm": "NM"
    }
    
    # Apply all fixes
    for wrong, correct in fixes.items():
        if isinstance(wrong, str):
            text = text.replace(wrong, correct)
        else:  # regex pattern
            text = re.sub(wrong, correct, text, flags=re.IGNORECASE)
            
    for wrong, correct in modality_fixes.items():
        text = re.sub(rf'\b{wrong}\b', correct, text, flags=re.IGNORECASE)
    
    # Improved cleanup
    text = re.sub(r'\n{2,}', '\n', text)  # Reduce multiple newlines
    text = re.sub(r'[ \t]{2,}', ' ', text)  # Reduce multiple spaces
    text = re.sub(r'([A-Za-z])\s+([A-Za-z])', r'\1\2', text)  # Fix broken words
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
    
    return text.strip()

# ---------- TEXT EXTRACTION ----------
def extract_text_from_image(image_path):
    """Extract text from image with enhanced preprocessing"""
    try:
        processed_img = preprocess_image(image_path)
        custom_config = r'--oem 3 --psm 6'
        raw = pytesseract.image_to_string(processed_img, config=custom_config)
        return clean_ocr_text(raw)
    except Exception as e:
        print(f"[ERROR] Image text extraction failed: {e}")
        return ""

def extract_text(file_path):
    """Main text extraction function that handles multiple file types"""
    try:
        ext = os.path.splitext(file_path)[-1].lower()
        
        if ext in ['.png', '.jpg', '.jpeg']:
            # Try multiple OCR strategies
            text = extract_text_from_image(file_path)
            if len(text.strip().split()) < 10:  # If first attempt got too little text
                print("Trying alternative OCR approach")
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img, config='--psm 6')
                text = clean_ocr_text(text)
            return text
            
        elif ext == '.pdf':
            pages = convert_from_path(file_path, dpi=300)
            text = ""
            for i, page in enumerate(pages):
                temp_path = os.path.join(settings.MEDIA_ROOT, f'temp_page_{i}.png')
                page.save(temp_path, 'PNG')
                page_text = extract_text_from_image(temp_path)
                if len(page_text.strip().split()) < 5:  # If OCR got little text
                    page_text = pytesseract.image_to_string(temp_path, config='--psm 6')
                    page_text = clean_ocr_text(page_text)
                text += page_text + "\n"
                os.remove(temp_path)
            return clean_ocr_text(text)
            
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return clean_ocr_text(f.read())
                
        else:  # Try textract for other formats (doc, docx, etc.)
            try:
                return clean_ocr_text(textract.process(file_path).decode('utf-8'))
            except Exception as e:
                print(f"[ERROR] Textract failed on {file_path}: {e}")
                return ""
    except Exception as e:
        print(f"[ERROR] Text extraction failed: {e}")
        return ""

# ---------- FIELD EXTRACTION ----------
def clean_patient_name(raw_name):
    """Clean and normalize patient names"""
    if not raw_name:
        return "-"
        
    name = raw_name.split("Age")[0].strip()
    name = re.sub(r"\s{2,}", " ", name)
    name = re.sub(r"[^\w\s,]", "", name)
    name = re.sub(r"\bwan\b", "", name, flags=re.IGNORECASE)
    return name.strip()


def extract_fields(text):
    """Enhanced field extraction with proper ICD-10 diagnosis description capture and interpretation."""
    if not text:
        return {key: '-' for key in DEFAULT_KEYS}

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    data = {key: '-' for key in DEFAULT_KEYS}

    current_section = None
    section_content = []

    # Priority order for most reliable diagnosis sections
    diagnosis_priority = [
        ('impression', 'Impression:'),
        ('clinical_indication', 'Clinical Indication:'),
        ('findings', 'Findings:')
    ]

    for line in lines:
        # Normalize keys before sections
        for key, pattern in BASIC_PATTERNS.items():
            if re.match(pattern, line, re.I):
                if current_section and section_content:
                    data[current_section] = ' '.join(section_content).strip()
                    section_content = []
                data[key] = extract_value_from_line(line, key)
                break

        # Section-based extraction
        section_found = False
        for section, trigger in diagnosis_priority:
            if trigger.lower() in line.lower():
                if current_section and section_content:
                    data[current_section] = ' '.join(section_content).strip()
                current_section = section
                data['diagnosis_section'] = section
                section_content = [line.split(trigger, 1)[-1].strip()]
                section_found = True
                break

        if section_found:
            continue

        # Special cases: Exam, Procedure, Clinical inside Findings
        if 'Exam:' in line:
            store_section(data, current_section, section_content)
            current_section = 'exam'
            section_content = [line.split("Exam:", 1)[-1].strip()]

        elif 'Procedure:' in line:
            store_section(data, current_section, section_content)
            current_section = 'procedure'
            section_content = [line.split("Procedure:", 1)[-1].strip()]

        elif 'Clinical:' in line and current_section == 'findings':
            clinical_part = line.split("Clinical:", 1)[-1].strip()
            findings_part = line.split("Clinical:", 1)[0].strip()
            if clinical_part:
                data['clinical_indication'] = clinical_part
            if findings_part:
                section_content.append(findings_part)
        elif current_section:
            section_content.append(line)

    if current_section and section_content:
        data[current_section] = ' '.join(section_content).strip()

    # Step: ICD Diagnosis Description Inference
    icd_candidates = []
    for k in ['impression', 'clinical_indication', 'ordhx', 'findings']:
        if data[k] != '-':
            icd_candidates.append(data[k])

    data['icd_diagnosis_description'] = extract_relevant_diagnosis(icd_candidates) or '-'

    return data


def extract_value_from_line(line, key):
    """Extracts field value using key-specific patterns."""
    if key == 'name':
        return clean_patient_name(re.split(r'Name\s*[:=]', line, flags=re.I)[-1])
    elif key == 'age':
        age = re.findall(r"Age\s*[:=]?\s*(\d+)", line, re.I)
        return age[0] if age else '-'
    elif key == 'sex':
        sex = re.findall(r"Sex\s*[:=]?\s*([MF])", line, re.I)
        return sex[0].upper() if sex else '-'
    elif key == 'dob':
        dob = re.findall(r"DOB\s*[:=]?\s*([\d\-/]+)", line)
        return dob[0] if dob else '-'
    elif key == 'mrn':
        return re.split(r'MRN\s*[:=]', line, flags=re.I)[-1].strip()
    elif key == 'date_of_service':
        return re.split(r'(Date of Service|DOS)\s*[:=]', line, flags=re.I)[-1].strip(" :")
    elif key == 'ordex':
        return re.split(r'OrdEx\s*[:=]', line, flags=re.I)[-1].strip()
    elif key == 'ordhx':
        return re.split(r'OrdHx\s*[:=]', line, flags=re.I)[-1].strip()
    elif key == 'accession':
        accession = re.findall(r"\d{6,10}", line)
        return accession[0] if accession else '-'
    return '-'


def store_section(data, current_section, section_content):
    """Stores previous section before switching."""
    if current_section and section_content:
        data[current_section] = ' '.join(section_content).strip()
        section_content.clear()


def clean_patient_name(name):
    """Simple cleanup for patient name."""
    return re.sub(r"[^A-Z\s,]", "", name.upper()).strip()


def extract_relevant_diagnosis(text_list):
    """Extract final structured ICD-compatible diagnosis string."""
    side_keywords = {
        "right": "right",
        "left": "left",
        "bilateral": "bilateral"
    }

    for text in text_list:
        cleaned = clean_diagnosis_text(text)
        if not cleaned:
            continue

        terms = re.split(r"[.,;/]", cleaned)
        terms = [term.strip() for term in terms if term and not is_negation(term)]

        final_terms = []
        for term in terms:
            side = None
            for keyword in side_keywords:
                if keyword in term:
                    side = side_keywords[keyword]
                    break
            if side and "hand" in term:
                final_terms.append(f"{side} hand pain")
            else:
                final_terms.append(term)

        if final_terms:
            return ", ".join(final_terms)

    return "-"


def clean_diagnosis_text(text):
    """Cleans and simplifies diagnostic text."""
    if not text:
        return ""

    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # Remove non-ASCII
    text = re.sub(r"[^\w\s.,;/-]", "", text)  # Remove unwanted characters
    text = re.sub(r"\s+", " ", text).strip().lower()

    # Negation phrases to remove
    negation_patterns = [
        r"\b(no (evidence|fracture|lesion|abnormality|acute|mass|midline shift|hemorrhage)|without|unremarkable|negative for|rule out|r/o)\b[^.,;\n]*",
        r"there is no[^.,;\n]*"
    ]
    for pattern in negation_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Remove vague phrases
    text = re.sub(r"\b(bone alignment|joint spaces|soft tissues|clinical|see above|maintained|not associated with)\b", "", text, flags=re.IGNORECASE)

    # Remove severity adjectives
    text = re.sub(r"\b(mild|moderate|severe|acute|chronic)\b", "", text, flags=re.IGNORECASE)

    # Normalize punctuation
    text = re.sub(r"[;:]", ".", text)
    text = re.sub(r"[^\w\s.,]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def is_negation(term):
    """Detect phrases that indicate absence of disease."""
    negation_keywords = [
        "normal", "unremarkable", "no findings", "no acute findings",
        "without evidence of", "negative"
    ]
    return any(keyword in term.lower() for keyword in negation_keywords)


# Default dictionary keys
DEFAULT_KEYS = {
    'name', 'age', 'sex', 'dob', 'ordex', 'accession', 'ordhx', 'exam',
    'clinical_indication', 'findings', 'impression', 'procedure',
    'mrn', 'date_of_service', 'icd_diagnosis_description', 'diagnosis_section'
}

# Regex patterns for basic field lines
BASIC_PATTERNS = {
    'name': r'^(Name|Patient\s*Name)\s*[:=]',
    'age': r'^(Age|Patient\s*Age)\s*[:=]',
    'sex': r'^(Sex|Gender)\s*[:=]',
    'dob': r'^DOB\s*[:=]',
    'mrn': r'^MRN\s*[:=]',
    'date_of_service': r'^(Date of Service|DOS)\s*[:=]',
    'ordex': r'^OrdEx\s*[:=]',
    'ordhx': r'^OrdHx\s*[:=]',
    'accession': r'(Accsn|Accession)'
}

# ---------- TEXT NORMALIZATION ----------
def normalize(text):
    """Normalize text for CPT matching"""
    if not text:
        return ""
        
    text = text.lower()
    text = text.replace("-", " ")  # Treat dashes as spaces
    
    # Remove most punctuation except for parentheses
    text = text.translate(str.maketrans('', '', string.punctuation.replace("(", "").replace(")", "")))
    
    # Standardize common terms
    replacements = {
        "x-ray": "xr", "xray": "xr",
        "ultrasound": "us", "sonogram": "us",
        "ct scan": "ct", "mri scan": "mri",
        "pa and lateral": "2 views",
        "with contrast": "w contrast",
        "without contrast": "wo contrast",
        "right": "rt", "left": "lt", "bilateral": "bilat",
        "minimum": "min", "complete": "comp"
    }
    
    for term, replacement in replacements.items():
        text = text.replace(term, replacement)
    
    # Normalize number of views
    text = re.sub(r"\bmin\s+(\d+)\s*views?\b", r"\1 views", text)
    text = re.sub(r"\bcomp\s+(\d+)\s*views?\b", r"\1 views", text)
    text = re.sub(r"\b(\d+)\s*views?\b", r"\1 views", text)
    
    # Normalize contrast notations
    text = re.sub(r"w[/\\-]?wo", "with and without", text)
    text = re.sub(r"w[/\\-]?o", "without", text)
    text = re.sub(r"w[/\\-]?c", "with contrast", text)
    
    return re.sub(r"\s{2,}", " ", text).strip()

# ---------- EXAM DESCRIPTION DETECTION ----------
def normalize_exam_description(patient_data):
    """Extract and normalize exam description from patient data"""
    if not patient_data:
        return ""
    
    # Try multiple fields in priority order
    for field in ['ordex', 'exam', 'procedure', 'clinical_indication']:
        text = patient_data.get(field, '').strip()
        if text and any(prefix in text.upper() for prefix in MODALITY_PREFIXES):
            return text
    
    # Fallback: Search entire text for modality patterns
    full_text = " ".join(str(v) for v in patient_data.values() if v != '-')
    for prefix in MODALITY_PREFIXES:
        if prefix in full_text.upper():
            match = re.search(rf'({prefix}[^\n]+)', full_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
    
    # Final fallback - return procedure if exists
    if patient_data.get('procedure', '-') != '-':
        return patient_data['procedure']
    
    return ""

# ---------- CPT MATCHING ----------
def match_cpt_code(description, threshold=80, top_n=1):
    """Enhanced CPT code matching with better fallback logic"""
    if not description or not isinstance(description, str) or len(description.strip()) < 3:
        print(f"[WARN] Invalid description provided: {description}")
        return [{
            "code": "N/A", 
            "description": "Invalid or empty description", 
            "score": 0
        }]
    
    norm_description = normalize(description)
    print("[DEBUG] Normalized input description:", norm_description)

    mapping_path = os.path.join(settings.BASE_DIR, 'scripts', 'formatted_cpt_mapping.json')
    try:
        with open(mapping_path, 'r', encoding='utf-8') as file:
            raw_map = json.load(file)
    except Exception as e:
        print(f"[ERROR] Failed to load CPT mapping: {e}")
        return []

    # Normalize all mapping keys
    normalized_map = {
        normalize(k): (k, v.strip()) for k, v in raw_map.items()
    }

    # 1. Strong exact match on the entire normalized description
    if norm_description in normalized_map:
        original_key, code = normalized_map[norm_description]
        print("[DEBUG] Exact match found!")
        return [{"code": code, "description": original_key, "score": 100}]

    # Extract tokens from the normalized description
    tokens = norm_description.split()
    
    # Get modality (e.g., "xr", "ct", etc.)
    modality = next((m.lower() for m in MODALITY_PREFIXES if m.lower() in tokens), "")
    
    # Get side (if present)
    side = next((s for s in ["right", "left", "bilateral", "rt", "lt", "bilat"] if s in tokens), "")
    
    # Get the number of views (if any)
    views_match = re.search(r'(min\s*\d+\s*views|\d+\s*views)', norm_description)
    views = views_match.group(0) if views_match else ""
    
    # Collect body part tokens
    body_tokens = []
    if modality:
        try:
            mod_index = tokens.index(modality)
            for token in tokens[mod_index+1:]:
                if re.match(r'\d', token):
                    break
                body_tokens.append(token)
        except ValueError:
            pass
    body_part = " ".join(body_tokens).strip()

    # Build keyword combinations
    keyword_combo = f"{modality} {body_part} {side} {views}".strip()
    print("[DEBUG] Matching using keyword combo:", keyword_combo)

    # Build alternative candidates
    candidates = [keyword_combo]
    if side:
        alt_combo = re.sub(r'\b' + re.escape(side) + r'\b', "", keyword_combo).strip()
        alt_combo = re.sub(r'\s{2,}', ' ', alt_combo)
        candidates.append(alt_combo)
        print("[DEBUG] Alternative keyword combo without side:", alt_combo)

    # 2. Check for exact matches on candidates
    for candidate in candidates:
        if candidate in normalized_map:
            original_key, code = normalized_map[candidate]
            print("[DEBUG] Exact candidate match found for:", candidate)
            return [{"code": code, "description": original_key, "score": 100}]

    # 3. Prioritize semi-matching modality-based codes
    modality_matches = []
    for norm_key, (original_key, code) in normalized_map.items():
        # Skip if the desired modality is specified and not present in the key
        if modality and modality not in norm_key:
            continue
        # Also check body_part if available
        if body_part and body_part not in norm_key:
            continue

        score = fuzz.token_sort_ratio(keyword_combo, norm_key)
        if score >= 70:
            modality_matches.append({
                "code": code,
                "description": original_key,
                "score": score
            })

    if modality_matches:
        modality_matches.sort(key=lambda x: -x["score"])
        print("[DEBUG] Best modality partial match:", modality_matches[0])
        return [modality_matches[0]]

    # 4. Fallback fuzzy match on full description
    matches = []
    for norm_key, (original_key, code) in normalized_map.items():
        if modality and modality not in norm_key:
            continue
        score = fuzz.token_sort_ratio(norm_description, norm_key)
        if score >= threshold:
            matches.append({
                "code": code,
                "description": original_key,
                "score": score
            })

    if matches:
        matches.sort(key=lambda x: -x["score"])
        print("[DEBUG] Best fuzzy match fallback:", matches[0])
        return matches[:top_n]

    # 5. Additional fallback: Filter keys with modality and first body token
    if modality and body_tokens:
        primary_body = body_tokens[0]
        fallback_matches = []
        for norm_key, (original_key, code) in normalized_map.items():
            if modality in norm_key and primary_body in norm_key:
                score = fuzz.token_sort_ratio(norm_description, norm_key)
                fallback_matches.append((score, code, original_key))
        if fallback_matches:
            best_fallback = max(fallback_matches, key=lambda x: x[0])
            if best_fallback[0] >= 50:
                print("[DEBUG] Fallback filtered match:", best_fallback)
                return [{"code": best_fallback[1], "description": best_fallback[2], "score": best_fallback[0]}]

    # 6. Fallback to modality-only match
    if modality:
        print("[DEBUG] Falling back to modality only match.")
        return [{"code": "-", "description": modality.upper(), "score": 50}]

    print("[DEBUG] No strong match found. Returning fallback.")
    return [{"code": "N/A", "description": keyword_combo, "score": 0}]
    
def match_icd10_code(diagnosis_text, threshold=75, top_n=1):
    """Improved ICD-10 matcher with multi-term (headache, syncope) support."""
    if not diagnosis_text or not isinstance(diagnosis_text, str):
        return [{"code": "N/A", "description": "Invalid diagnosis", "score": 0}]

    # Load ICD-10 mapping
    mapping_path = os.path.join(settings.BASE_DIR, 'scripts', 'formatted_icd10_mapping.json')
    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            icd_map = json.load(f)
    except Exception as e:
        return [{"code": "N/A", "description": str(e), "score": 0}]

    # Clean input diagnosis
    cleaned = clean_diagnosis_text(diagnosis_text)
    print("[DEBUG] Cleaned diagnosis:", cleaned)

    # Split diagnosis by commas, semicolons, periods
    terms = re.split(r"[,;/\n.]", cleaned)
    terms = [t.strip().lower() for t in terms if len(t.strip()) >= 3]

    all_matches = []

    for term in terms:
        best_match = {"code": "N/A", "description": term, "score": 0}

        for key, code in icd_map.items():
            cleaned_key = clean_diagnosis_text(key).lower()
            key_words = set(cleaned_key.split())
            term_words = set(term.split())

            word_overlap = len(term_words & key_words)
            overlap_score = word_overlap / max(len(key_words), 1)
            fuzzy_score = fuzz.token_sort_ratio(term, cleaned_key) / 100
            final_score = round((0.6 * overlap_score + 0.4 * fuzzy_score) * 100)

            if final_score > best_match["score"]:
                best_match = {
                    "code": code,
                    "description": key,
                    "score": final_score
                }

        if best_match["score"] >= threshold:
            all_matches.append(best_match)
        else:
            all_matches.append({
                "code": "N/A",
                "description": term,
                "score": 0
            })

    if all_matches:
        return all_matches

    return [{
        "code": "N/A",
        "description": diagnosis_text,
        "score": 0
    }]

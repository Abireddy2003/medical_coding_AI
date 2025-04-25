from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.conf import settings
from django.shortcuts import render
from datetime import datetime
import traceback
import os
import logging

from .models import CPTCode, ICD10Code, MedicalReport
from .utils import (
    extract_text,
    extract_fields,
    match_cpt_code,
    match_icd10_code,
    normalize_exam_description,
    clean_diagnosis_text
)

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg', 'txt', 'doc', 'docx']

@api_view(['POST'])
def predict_cpt_from_image(request):
    """Handle image/pdf upload with integrated CPT and ICD-10 processing"""
    try:
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "No file provided"}, status=400)

        # Validate file extension
        file_ext = os.path.splitext(uploaded_file.name)[1].lower().lstrip('.')
        if file_ext not in ALLOWED_EXTENSIONS:
            return Response({"error": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}, status=400)

        # Save temporary file
        temp_file_path = default_storage.save(f"temp_reports/{uploaded_file.name}", uploaded_file)
        full_temp_path = os.path.join(settings.MEDIA_ROOT, temp_file_path)

        try:
            # Text extraction
            raw_text = extract_text(full_temp_path)
            if not raw_text.strip() or len(raw_text.strip()) < 30:
                logger.warning("Insufficient OCR content")
                return Response({"error": "Insufficient text extracted"}, status=400)

            # Data extraction
            patient_data = extract_fields(raw_text)
            patient_data['exam_description'] = normalize_exam_description(patient_data)

            # Code matching
            cpt_matches = match_cpt_code(
                patient_data['exam_description'], 
                top_n=3
            ) if patient_data.get('exam_description') else []
            
            icd_matches = match_icd10_code(
                patient_data.get('icd_diagnosis_description', ''),
                top_n=3
            )

            # Build response
            response_data = save_report_and_response(
                patient_data=patient_data,
                cpt_matches=cpt_matches,
                icd_matches=icd_matches,
                file_path=temp_file_path
            )

            return Response(response_data)

        except Exception as processing_error:
            logger.error(f"Processing error: {str(processing_error)}")
            traceback.print_exc()
            return Response({"error": "Document processing failed"}, status=500)
        finally:
            # Cleanup temporary file
            if os.path.exists(full_temp_path):
                os.remove(full_temp_path)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        traceback.print_exc()
        return Response({"error": "Server error"}, status=500)

@api_view(['POST'])
def predict_cpt_from_text(request):
    """Handle text input with integrated code matching"""
    try:
        raw_text = request.data.get("text", "")
        if not raw_text.strip():
            return Response({"error": "No text provided"}, status=400)

        # Clean and normalize text
        processed_text = raw_text.replace("`n", "\n").replace("\\n", "\n")
        
        try:
            # Data extraction
            patient_data = extract_fields(processed_text)
            patient_data['exam_description'] = normalize_exam_description(patient_data)

            # Code matching
            cpt_matches = match_cpt_code(
                patient_data.get('exam_description', ''),
                top_n=3
            )
            
            icd_matches = match_icd10_code(
                patient_data.get('icd_diagnosis_description', ''),
                top_n=3
            )

            # Build response
            response_data = save_report_and_response(
                patient_data=patient_data,
                cpt_matches=cpt_matches,
                icd_matches=icd_matches
            )

            return Response(response_data)

        except Exception as processing_error:
            logger.error(f"Processing error: {str(processing_error)}")
            traceback.print_exc()
            return Response({"error": "Text processing failed"}, status=500)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        traceback.print_exc()
        return Response({"error": "Server error"}, status=500)

def save_report_and_response(patient_data, cpt_matches, icd_matches, file_path=None):
    """Save results to database and format API response"""
    try:
        # Parse dates
        dos = parse_date(patient_data.get('date_of_service'))
        dob = parse_date(patient_data.get('dob'))

        # Get best matches
        best_cpt = cpt_matches[0] if cpt_matches else None
        best_icd = icd_matches[0] if icd_matches else None

        # Create database records
        report = MedicalReport.objects.create(
            patient_name=patient_data.get('name', '-'),
            age=patient_data.get('age', '-'),
            gender=patient_data.get('sex', '-'),
            dob=dob,
            mrn=patient_data.get('mrn', '-'),
            date_of_service=dos,
            exam=patient_data.get('exam', '-'),
            clinical_indication=patient_data.get('clinical_indication', '-'),
            findings=patient_data.get('findings', '-'),
            impression=patient_data.get('impression', '-'),
            cpt_code=get_or_create_cpt(best_cpt),  # Remove 'self' reference
            icd10_code=get_or_create_icd(best_icd),  # Remove 'self' reference
            uploaded_file=file_path or ''
        )

        return {
            "patient_data": patient_data,
            "cpt_prediction": best_cpt or {"code": "-", "description": "No match"},
            "icd_prediction": best_icd or {"code": "-", "description": "No match"},
            "top_cpt_matches": cpt_matches,
            "top_icd_matches": icd_matches,
            "report_id": report.id
        }

    except Exception as e:
        logger.error(f"Save error: {str(e)}")
        traceback.print_exc()
        raise


def parse_date(date_str):
    """Safe date parsing with multiple formats"""
    if not date_str or date_str == '-':
        return None
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d-%b-%y'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None
def get_or_create_cpt(match):
    if not match or match.get('code') in ('N/A', '-'):
        return None
    return CPTCode.objects.get_or_create(
        code=match['code'],
        defaults={'description': match['description']}
    )[0]

def get_or_create_icd(match):
    if not match or match.get('code') in ('N/A', '-'):
        return None
    return ICD10Code.objects.get_or_create(
        code=match['code'],
        defaults={'description': match['description']}
    )[0]
def index(request):
    return render(request, 'index.html')
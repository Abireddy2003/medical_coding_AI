from django.db import models
from django.utils import timezone

class CPTCode(models.Model):
    code = models.CharField(max_length=10, primary_key=True, verbose_name='CPT Code')
    description = models.TextField(verbose_name='Procedure Description')
    
    def __str__(self):
        return f"{self.code} - {self.description[:50]}..."

class ICD10Code(models.Model):
    code = models.CharField(max_length=10, primary_key=True, verbose_name='ICD-10 Code')
    description = models.TextField(verbose_name='Diagnosis Description')
    
    def __str__(self):
        return f"{self.code} - {self.description[:50]}..."

class MedicalReport(models.Model):
    # Patient Information
    created_at = models.DateTimeField(default=timezone.now)
    patient_name = models.CharField(max_length=255, default='-')
    age = models.CharField(max_length=20, default='-')
    gender = models.CharField(max_length=10, default='-')
    dob = models.DateField(null=True, blank=True)
    mrn = models.CharField(max_length=50, default='-')
    
    # Report Metadata
    date_of_service = models.DateField(null=True, blank=True)
    uploaded_file = models.FileField(upload_to='medical_reports/', blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    # Clinical Information
    exam = models.TextField(default='-')
    clinical_indication = models.TextField(default='-')
    findings = models.TextField(default='-')
    impression = models.TextField(default='-')
    
    # Coding Information
    cpt_code = models.ForeignKey(
        CPTCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Associated CPT Code'
    )
    
    icd10_code = models.ForeignKey(
        ICD10Code,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Associated ICD-10 Code'
    )

    # Audit Fields
    processing_log = models.TextField(blank=True, help_text='Any processing errors or notes')

    def __str__(self):
        return f"Report for {self.patient_name} - {self.date_of_service or 'No Date'}"

    class Meta:
        ordering = ['-date_of_service']
        verbose_name = 'Medical Report'
        verbose_name_plural = 'Medical Reports'
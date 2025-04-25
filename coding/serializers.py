from rest_framework import serializers
from .models import MedicalReport, CPTCode

class CPTCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPTCode
        fields = '__all__'

class MedicalReportSerializer(serializers.ModelSerializer):
    predicted_cpt = serializers.PrimaryKeyRelatedField(queryset=CPTCode.objects.all())

    class Meta:
        model = MedicalReport
        fields = '__all__'

from rest_framework import serializers
from .models import MedicationSchedule, Prescription, Patient, Doctor, Pharmacist

class MedicationScheduleSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    medication_name = serializers.SerializerMethodField()
    dosage = serializers.SerializerMethodField()
    frequency = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    instructions = serializers.SerializerMethodField()
    pharmacist_name = serializers.SerializerMethodField()

    class Meta:
        model = MedicationSchedule
        fields = [
            'id', 'prescription', 'time_slots', 'start_date', 'end_date',
            'created_at', 'patient_name', 'medication_name', 'dosage',
            'frequency', 'duration', 'instructions', 'pharmacist_name'
        ]

    def get_patient_name(self, obj):
        return obj.prescription.appointment.patient.user.get_full_name()

    def get_medication_name(self, obj):
        return obj.prescription.medication_name

    def get_dosage(self, obj):
        return obj.prescription.dosage

    def get_frequency(self, obj):
        return obj.prescription.frequency

    def get_duration(self, obj):
        return obj.prescription.duration

    def get_instructions(self, obj):
        return obj.prescription.instructions

    def get_pharmacist_name(self, obj):
        return obj.created_by.user.get_full_name() 
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('DOCTOR', 'Doctor'),
        ('RECEPTIONIST', 'Receptionist'),
        ('PHARMACIST', 'Pharmacist'),
        ('LAB_TECHNICIAN', 'Lab Technician'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.TextField()
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('MALE', 'Male'), ('FEMALE', 'Female')], null=True)
    emergency_contact = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=[
            ('WAITING', 'Waiting'),
            ('IN_LAB', 'In Lab'),
            ('IN_PHARMACY', 'In Pharmacy'),
            ('COMPLETED', 'Completed')
        ],
        default='WAITING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()}"

    @property
    def age(self):
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    class Meta:
        ordering = ['-created_at']

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Dr. {self.user.last_name} ({self.specialization})"

class Pharmacist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=50)
    shift_schedule = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Pharmacist {self.user.last_name}"

class Receptionist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    shift = models.CharField(max_length=50, blank=True)
    is_senior = models.BooleanField(default=False)

    def __str__(self):
        return f"Receptionist {self.user.get_full_name()}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    receptionist = models.ForeignKey(Receptionist, on_delete=models.SET_NULL, null=True, blank=True)
    date_time = models.DateTimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_time']

    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.doctor.user.get_full_name()} - {self.date_time}"

class Prescription(models.Model):
    STATUS_CHOICES = [
        ('SUGGESTED', 'Suggested by Doctor'),
        ('PRESCRIBED', 'Prescribed by Pharmacist'),
        ('SCHEDULED', 'Scheduled for Patient'),
    ]
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    medication_name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=50)
    frequency = models.CharField(max_length=50)
    duration = models.CharField(max_length=50)
    instructions = models.TextField(blank=True)
    prescribed_by = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUGGESTED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.medication_name} for {self.appointment.patient.user.get_full_name()}"

class MedicationSchedule(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='schedules')
    time_slots = models.JSONField()  # Stores list of times like ["08:00", "14:00", "20:00"]
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(Pharmacist, on_delete=models.CASCADE)

    def __str__(self):
        return f"Schedule for {self.prescription} from {self.start_date} to {self.end_date}"

    class Meta:
        ordering = ['-start_date']

class LabTechnician(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - Lab Technician"

class LabTest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    )
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(LabTechnician, on_delete=models.CASCADE, null=True, blank=True)
    test_name = models.CharField(max_length=100)
    instructions = models.TextField()
    required_measurements = models.TextField(blank=True)  # Store as comma-separated values
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    results = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.test_name} for {self.appointment.patient.user.get_full_name()}"

class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"

    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return '/static/images/default_profile.png'